import html
import ipaddress
import logging
import re
import socket
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse
from uuid import UUID
import xml.etree.ElementTree as ET

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import Skill
from app.schemas.ingestion import (
    ImportDetailItem,
    JobPreviewItem,
    MatchedSkillItem,
    PreviewSummary,
    RssImportResponse,
    RssPresetFeed,
    RssPreviewResponse,
)
from app.services.jsearch import (
    get_canonical_skills_map,
    sanitize_external_id,
    validate_url,
)

logger = logging.getLogger(__name__)

APPROVED_RSS_PRESETS: list[RssPresetFeed] = [
    RssPresetFeed(
        id="weworkremotely-programming",
        name="We Work Remotely — Programming",
        url="https://weworkremotely.com/categories/remote-programming-jobs.rss",
        description="Curated remote developer, software engineering, and intern openings.",
    ),
    RssPresetFeed(
        id="weworkremotely-devops",
        name="We Work Remotely — DevOps & Sysadmin",
        url="https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
        description="Remote cloud, infrastructure, and systems administration listings.",
    ),
    RssPresetFeed(
        id="remoteok-dev",
        name="RemoteOK — Tech Openings",
        url="https://remoteok.com/remote-jobs.rss",
        description="Global remote technology and engineering positions.",
    ),
]


def clean_html_text(text: str | None) -> str:
    """
    Safely strip HTML tags and unescape entities using Python standard library.
    Avoids requiring BeautifulSoup or external scraping dependencies.
    """
    if not text or not isinstance(text, str):
        return ""
    # 1. Strip script and style blocks entirely (including contents)
    no_scripts = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.IGNORECASE | re.DOTALL)
    # 2. Strip remaining HTML tags
    stripped = re.sub(r"<[^>]+>", " ", no_scripts)
    # 3. Unescape HTML entities (&amp;, &lt;, &#39;, etc.)
    unescaped = html.unescape(stripped)
    # 4. Strip any newly uncovered HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", unescaped)
    # 5. Collapse whitespace
    collapsed = re.sub(r"[ \t]+", " ", cleaned)
    collapsed = re.sub(r"\s+([,.:;!?])", r"\1", collapsed)
    collapsed = re.sub(r"\n\s*\n+", "\n\n", collapsed)
    return collapsed.strip()


def validate_feed_url(url: str) -> str:
    """
    Enforce strict SSRF protection for outbound RSS feed requests:
    - Must be http or https
    - Hostname must resolve to public IP (rejects loopback, RFC 1918 private subnets, link-local, AWS metadata)
    """
    if not url or not isinstance(url, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feed URL must be a non-empty string.",
        )
    url = url.strip()
    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed Feed URL: {exc!s}",
        )

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prohibited URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted.",
        )

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing hostname in feed URL.",
        )

    # Check for direct localhost strings
    if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prohibited feed host: localhost and loopback destinations are forbidden.",
        )

    # Resolve IP and verify public addressing (SSRF prevention)
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        for _, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)
            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_multicast
                or ip_obj.is_reserved
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Prohibited feed host: address '{ip_str}' resolves to a private or restricted network.",
                )
    except socket.gaierror as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to resolve feed hostname '{hostname}': {exc!s}",
        )

    return url


def parse_rss_datetime(date_str: str | None) -> datetime | None:
    """Parse RFC 2822 (RSS) or ISO 8601 (Atom) date to timezone-aware UTC datetime."""
    if not date_str or not isinstance(date_str, str):
        return None
    cleaned = date_str.strip()
    # 1. Try RFC 2822 / 822 (standard in RSS)
    try:
        dt = parsedate_to_datetime(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # 2. Try ISO 8601 (Atom)
    try:
        dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    return None


def _find_child_elem(parent: ET.Element, candidate_tags: list[str]) -> ET.Element | None:
    """Safely find a child element among candidate tags without bool() coercion."""
    for tag in candidate_tags:
        elem = parent.find(tag)
        if elem is not None:
            return elem
    return None


def parse_xml_feed(xml_text: str) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """
    Parse RSS 2.0 or Atom 1.0 XML content into raw metadata and item records
    using standard library xml.etree.ElementTree without heavy scraping packages.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse XML feed content: {exc!s}",
        )

    feed_meta: dict[str, str] = {
        "title": "Untitled RSS Feed",
        "link": "",
        "description": "",
    }
    raw_items: list[dict[str, Any]] = []

    def local_name(tag: str) -> str:
        return tag.split("}", 1)[1] if "}" in tag else tag

    root_tag = local_name(root.tag).lower()

    if root_tag in ("rss", "rdf"):
        # RSS 2.0 or RDF channel
        channel = root.find("channel")
        if channel is None:
            channel = root

        t_elem = _find_child_elem(channel, ["title"])
        if t_elem is not None and t_elem.text:
            feed_meta["title"] = clean_html_text(t_elem.text)

        l_elem = _find_child_elem(channel, ["link"])
        if l_elem is not None and l_elem.text:
            feed_meta["link"] = l_elem.text.strip()

        d_elem = _find_child_elem(channel, ["description"])
        if d_elem is not None and d_elem.text:
            feed_meta["description"] = clean_html_text(d_elem.text)

        items = channel.findall("item")
        if not items:
            items = root.findall("item")

        for item in items:
            item_data: dict[str, Any] = {}
            categories: list[str] = []

            for child in item:
                tag = local_name(child.tag).lower()
                text = child.text.strip() if child.text else ""

                if tag == "title":
                    item_data["title"] = text
                elif tag == "link":
                    item_data["link"] = text
                elif tag in ("guid", "id"):
                    item_data["guid"] = text
                elif tag in ("description", "encoded", "summary"):
                    if len(text) > len(item_data.get("description", "")):
                        item_data["description"] = text
                elif tag in ("pubdate", "date"):
                    item_data["pub_date"] = text
                elif tag in ("creator", "author"):
                    item_data["author"] = text
                elif tag in ("company", "company_name"):
                    item_data["company"] = text
                elif tag == "category":
                    if text:
                        categories.append(text)
                elif tag == "location":
                    item_data["location"] = text

            item_data["categories"] = categories
            raw_items.append(item_data)

    elif root_tag == "feed":
        # Atom 1.0
        t_elem = _find_child_elem(root, ["{http://www.w3.org/2005/Atom}title", "title"])
        if t_elem is not None and t_elem.text:
            feed_meta["title"] = clean_html_text(t_elem.text)

        l_elem = _find_child_elem(root, ["{http://www.w3.org/2005/Atom}link", "link"])
        if l_elem is not None:
            feed_meta["link"] = l_elem.attrib.get("href", "")

        entries = root.findall("{http://www.w3.org/2005/Atom}entry")
        if not entries:
            entries = root.findall("entry")

        for entry in entries:
            item_data = {}
            categories = []
            for child in entry:
                tag = local_name(child.tag).lower()
                text = child.text.strip() if child.text else ""

                if tag == "title":
                    item_data["title"] = text
                elif tag == "link":
                    item_data["link"] = child.attrib.get("href") or text
                elif tag == "id":
                    item_data["guid"] = text
                elif tag in ("content", "summary"):
                    if len(text) > len(item_data.get("description", "")):
                        item_data["description"] = text
                elif tag in ("published", "updated"):
                    item_data["pub_date"] = text
                elif tag == "author":
                    name_elem = _find_child_elem(child, ["{http://www.w3.org/2005/Atom}name", "name"])
                    if name_elem is not None and name_elem.text:
                        item_data["author"] = name_elem.text.strip()
                elif tag == "category":
                    cat_term = child.attrib.get("term") or text
                    if cat_term:
                        categories.append(cat_term)

            item_data["categories"] = categories
            raw_items.append(item_data)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported XML root element '{root_tag}'. Expected RSS (<rss>) or Atom (<feed>).",
        )

    return feed_meta, raw_items


def normalize_rss_item(
    raw_item: dict[str, Any],
    existing_external_ids: set[str],
    existing_urls: set[str],
    existing_signatures: set[str],
    skills_map: dict[str, Skill],
) -> JobPreviewItem:
    """
    Normalize raw RSS item into JobPreviewItem with shared validation:
    - Cleans HTML markup from titles and descriptions
    - Extracts company and role from RSS title conventions (e.g. 'Company: Title' or 'Title at Company')
    - Detects classification conflict (Intern vs Full-Time)
    - Extracts canonical skills
    - Performs cross-source duplicate detection (external_id, application_url, and title+company signature)
    """
    warnings: list[str] = []
    errors: list[str] = []

    # 1. Clean Title and Extract Company
    raw_title = clean_html_text(raw_item.get("title"))
    if not raw_title:
        errors.append("Job title is missing.")
        raw_title = "Untitled Opportunity"

    extracted_company = raw_item.get("company") or raw_item.get("author") or ""
    title = raw_title

    # Common RSS job title patterns: "Company Name: Job Title" or "Job Title at Company Name"
    if not extracted_company:
        if ": " in raw_title:
            parts = raw_title.split(": ", 1)
            extracted_company = parts[0].strip()
            title = parts[1].strip()
        elif " at " in raw_title:
            parts = raw_title.split(" at ", 1)
            title = parts[0].strip()
            extracted_company = parts[1].strip()

    company_name = clean_html_text(extracted_company) or "Unknown Employer"

    # 2. URLs
    raw_link = raw_item.get("link")
    application_url = validate_url(raw_link)
    if not application_url:
        warnings.append("Missing or invalid application URL. Admin must provide URL before publishing.")

    # 3. External ID
    raw_guid = raw_item.get("guid") or application_url or f"{title}_{company_name}"
    job_id = sanitize_external_id(raw_guid)

    # 4. Description
    raw_desc = raw_item.get("description")
    description = clean_html_text(raw_desc)
    if not description:
        warnings.append("Job description is empty.")
        description = None

    # 5. Opportunity Type & Conflict Detection
    title_lower = title.lower()
    full_text = f"{title_lower} {str(description).lower()}"
    categories = [clean_html_text(c).lower() for c in raw_item.get("categories", [])]
    cat_text = " ".join(categories)

    has_intern_keyword = bool(re.search(r"\b(intern|internship|trainee|apprentice)\b", title_lower))
    has_fulltime_keyword = (
        "full-time" in cat_text
        or "fulltime" in cat_text
        or "full time" in cat_text
        or "full-time" in title_lower
    )

    classification_conflict = False
    opportunity_type = "Full-Time"

    if has_intern_keyword and has_fulltime_keyword:
        classification_conflict = True
        warnings.append(
            "Classification conflict: Job title includes 'Intern', but categories declare 'Full-Time'. Flagged for review."
        )
        opportunity_type = "Internship"
    elif has_intern_keyword or "intern" in cat_text or "internship" in cat_text:
        opportunity_type = "Internship"
    else:
        opportunity_type = "Full-Time"

    # 6. Work Model
    work_model = "On-site"
    if "remote" in title_lower or "remote" in cat_text or "remote" in full_text:
        work_model = "Remote"
    elif "hybrid" in full_text or "hybrid" in cat_text:
        work_model = "Hybrid"

    # 7. Locations
    locations: list[str] | None = None
    raw_loc = raw_item.get("location")
    if raw_loc:
        locations = [clean_html_text(raw_loc)]
    elif work_model == "Remote":
        locations = ["Remote"]

    # 8. Date & Staleness
    posted_at = parse_rss_datetime(raw_item.get("pub_date"))
    if posted_at:
        now = datetime.now(timezone.utc)
        if posted_at < (now - timedelta(days=30)):
            warnings.append("Listing posted over 30 days ago and may be stale.")

    # 9. Canonical Skill Matching
    # Scan categories and description against skills map
    search_text = f"{title} {cat_text} {description or ''}".lower()
    matched_skills: list[MatchedSkillItem] = []
    unmapped_skills: list[str] = []
    seen_matched_ids: set[UUID] = set()

    for key, sk in skills_map.items():
        if len(key) >= 3 and sk.id not in seen_matched_ids:
            if re.search(r"\b" + re.escape(key) + r"\b", search_text):
                seen_matched_ids.add(sk.id)
                matched_skills.append(MatchedSkillItem(id=sk.id, name=sk.name))

    for cat in categories:
        if cat and cat not in skills_map and len(cat) > 2 and cat not in ("remote", "full-time", "contract", "intern"):
            if cat not in unmapped_skills:
                unmapped_skills.append(cat)

    # 10. Cross-Source Duplicate Detection
    is_duplicate = False
    norm_sig = f"{title.lower()}::{company_name.lower()}"

    if job_id in existing_external_ids:
        is_duplicate = True
        warnings.append("Listing has already been imported into CareerPilot via RSS.")
    elif application_url and application_url.lower() in existing_urls:
        is_duplicate = True
        warnings.append("Listing already exists in CareerPilot (cross-source duplicate detected by URL).")
    elif norm_sig in existing_signatures:
        is_duplicate = True
        warnings.append("Listing already exists in CareerPilot (cross-source duplicate detected by title and company).")

    review_required = bool(classification_conflict or warnings or unmapped_skills or errors)

    return JobPreviewItem(
        job_id=job_id,
        title=title,
        company_name=company_name,
        company_website=None,
        company_logo_url=None,
        description=description,
        opportunity_type=opportunity_type,
        work_model=work_model,
        locations=locations,
        eligibility=None,
        application_url=application_url,
        publisher="RSS Feed",
        posted_at=posted_at,
        deadline=None,
        salary_min=None,
        salary_max=None,
        stipend_min=None,
        stipend_max=None,
        currency=None,
        matched_skills=matched_skills,
        unmapped_skills=unmapped_skills[:10],
        is_duplicate=is_duplicate,
        review_required=review_required,
        warnings=warnings,
        errors=errors,
        classification_conflict=classification_conflict,
        raw_employment_types=categories[:5],
    )


async def fetch_feed_content(url: str, timeout: float = 15.0) -> str:
    """Fetch raw XML content from a validated feed URL with timeout bounds."""
    headers = {
        "User-Agent": "CareerPilot-AI-FeedReader/1.0 (+https://careerpilot.ai)",
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, max_redirects=3) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code >= 400:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Feed provider responded with HTTP error {resp.status_code}.",
                )
            return resp.text
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Feed request timed out after 15 seconds. Provider may be unresponsive.",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Network error while connecting to feed provider: {exc!s}",
        )


async def preview_rss_feed(
    feed_url: str,
    max_items: int,
    filter_keywords: str | None,
    db: AsyncSession,
) -> RssPreviewResponse:
    """
    Fetch, validate, and preview job opportunities from an authorized RSS/Atom feed.
    Enforces SSRF prevention, cross-source deduplication, and canonical skill matching.
    """
    clean_url = validate_feed_url(feed_url)
    xml_text = await fetch_feed_content(clean_url)

    # 2. Parse XML
    feed_meta, raw_items = parse_xml_feed(xml_text)

    # 3. Apply optional keyword filter
    if filter_keywords and filter_keywords.strip():
        kw = filter_keywords.strip().lower()
        raw_items = [
            it for it in raw_items
            if kw in str(it.get("title", "")).lower() or kw in str(it.get("description", "")).lower()
        ]

    # Limit to max_items
    raw_items = raw_items[:max_items]

    # 4. Load canonical skills map
    skills_map = await get_canonical_skills_map(db)

    # 5. Load existing database listings for cross-source deduplication
    dup_stmt = select(Opportunity.external_id, Opportunity.application_url, Opportunity.title, Opportunity.company_name).where(
        Opportunity.status.in_(["Draft", "Published"])
    )
    dup_res = await db.execute(dup_stmt)
    rows = dup_res.all()

    existing_external_ids = {r[0] for r in rows if r[0]}
    existing_urls = {r[1].lower() for r in rows if r[1]}
    existing_signatures = {f"{r[2].lower()}::{r[3].lower()}" for r in rows if r[2] and r[3]}

    # 6. Normalize items
    jobs: list[JobPreviewItem] = []
    valid_count = 0
    duplicate_count = 0
    review_required_count = 0

    for it in raw_items:
        job_item = normalize_rss_item(
            it,
            existing_external_ids=existing_external_ids,
            existing_urls=existing_urls,
            existing_signatures=existing_signatures,
            skills_map=skills_map,
        )
        if job_item.is_duplicate:
            duplicate_count += 1
        elif not job_item.errors:
            valid_count += 1

        if job_item.review_required:
            review_required_count += 1

        jobs.append(job_item)

    return RssPreviewResponse(
        feed_title=feed_meta.get("title"),
        feed_link=feed_meta.get("link"),
        feed_description=feed_meta.get("description"),
        jobs=jobs,
        total_found=len(jobs),
        summary=PreviewSummary(
            total_returned=len(jobs),
            valid_count=valid_count,
            duplicate_count=duplicate_count,
            review_required_count=review_required_count,
        ),
    )


async def import_rss_jobs(
    db: AsyncSession,
    selected_job_ids: list[str],
    jobs: list[JobPreviewItem],
    admin_profile_id: UUID,
) -> RssImportResponse:
    """
    Import selected RSS jobs into CareerPilot database as Draft opportunities.
    Guarantees:
    - Always saved with status='Draft'
    - Nested savepoints (db.begin_nested()) per item to isolate failures
    - Cross-source duplicate checks
    - Associated canonical skills attached
    """
    selected_set = set(selected_job_ids)
    candidate_jobs = [j for j in jobs if j.job_id in selected_set]

    if not candidate_jobs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid preview jobs matched the selected job IDs.",
        )

    # 1. Query existing records to prevent race-condition duplicates
    incoming_ids = [sanitize_external_id(j.job_id) for j in candidate_jobs]
    dup_stmt = select(Opportunity.external_id).where(
        Opportunity.source_name == "RSS",
        Opportunity.external_id.in_(incoming_ids),
    )
    dup_res = await db.execute(dup_stmt)
    already_imported_ids = set(dup_res.scalars().all())

    # 2. Query valid canonical skill IDs
    all_skill_ids = {s.id for j in candidate_jobs for s in j.matched_skills}
    valid_skill_ids: set[UUID] = set()
    if all_skill_ids:
        skill_stmt = select(Skill.id).where(Skill.id.in_(all_skill_ids), Skill.is_active.is_(True))
        skill_res = await db.execute(skill_stmt)
        valid_skill_ids = set(skill_res.scalars().all())

    inserted_count = 0
    skipped_count = 0
    duplicate_count = 0
    review_required_count = 0
    details: list[ImportDetailItem] = []

    for item in candidate_jobs:
        if item.errors:
            skipped_count += 1
            details.append(
                ImportDetailItem(
                    job_id=item.job_id,
                    title=item.title,
                    status="skipped",
                    reason=f"Validation errors: {', '.join(item.errors)}",
                )
            )
            continue

        sanitized_ext_id = sanitize_external_id(item.job_id)

        if sanitized_ext_id in already_imported_ids or item.job_id in already_imported_ids:
            duplicate_count += 1
            details.append(
                ImportDetailItem(
                    job_id=item.job_id,
                    title=item.title,
                    status="duplicate",
                    reason="Already exists in database.",
                )
            )
            continue

        eligibility_val = getattr(item, "eligibility", None)
        if item.classification_conflict or any("classification conflict" in str(w).lower() for w in item.warnings):
            conflict_tag = "[Classification Conflict: Job title includes 'Intern', but categories declare 'Full-Time'. Flagged for review.]"
            eligibility_val = f"{conflict_tag} {eligibility_val}".strip() if eligibility_val else conflict_tag

        opportunity = Opportunity(
            title=item.title[:255] if item.title else "Untitled Opportunity",
            company_name=item.company_name[:255] if item.company_name else "Unknown Employer",
            company_website=item.company_website[:500] if item.company_website else None,
            company_logo_url=item.company_logo_url[:500] if item.company_logo_url else None,
            description=item.description,
            opportunity_type=item.opportunity_type if item.opportunity_type in ("Internship", "Full-Time") else "Internship",
            work_model=item.work_model if item.work_model in ("Remote", "Hybrid", "On-site") else "On-site",
            locations=item.locations,
            eligibility=eligibility_val,
            application_url=item.application_url[:500] if item.application_url else None,
            deadline=item.deadline,
            salary_min=item.salary_min,
            salary_max=item.salary_max,
            stipend_min=item.stipend_min,
            stipend_max=item.stipend_max,
            currency=item.currency[:10] if item.currency else None,
            source_name="RSS",
            source_url=(item.application_url[:500] if item.application_url else None),
            external_id=sanitized_ext_id,
            status="Draft",  # Never silently published
            created_by_profile_id=admin_profile_id,
        )

        try:
            async with db.begin_nested():
                db.add(opportunity)
                await db.flush()

                for skill_item in item.matched_skills:
                    if skill_item.id in valid_skill_ids:
                        db.add(OpportunitySkill(opportunity_id=opportunity.id, skill_id=skill_item.id))

                await db.flush()
        except IntegrityError as exc:
            logger.warning("Duplicate import conflict for RSS job %s: %s", item.job_id, exc)
            duplicate_count += 1
            already_imported_ids.add(item.job_id)
            already_imported_ids.add(sanitized_ext_id)
            details.append(
                ImportDetailItem(
                    job_id=item.job_id,
                    title=item.title,
                    status="duplicate",
                    reason="Concurrent import conflict; record already exists.",
                )
            )
            continue
        except Exception as exc:
            logger.exception("Failed to insert RSS opportunity %s", item.job_id)
            skipped_count += 1
            details.append(
                ImportDetailItem(
                    job_id=item.job_id,
                    title=item.title,
                    status="skipped",
                    reason=f"Database insertion failed: {exc!s}",
                )
            )
            continue

        if item.review_required:
            review_required_count += 1

        inserted_count += 1
        already_imported_ids.add(sanitized_ext_id)
        details.append(
            ImportDetailItem(
                job_id=item.job_id,
                title=item.title,
                status="imported",
                opportunity_id=opportunity.id,
            )
        )

    await db.commit()

    return RssImportResponse(
        inserted_count=inserted_count,
        skipped_count=skipped_count,
        duplicate_count=duplicate_count,
        review_required_count=review_required_count,
        details=details,
    )
