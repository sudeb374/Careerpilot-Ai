import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import Skill
from app.schemas.ingestion import (
    ImportDetailItem,
    JobPreviewItem,
    JSearchImportResponse,
    JSearchPreviewResponse,
    MatchedSkillItem,
    PreviewSummary,
)

logger = logging.getLogger(__name__)

RAPIDAPI_JSEARCH_HOST = "jsearch.p.rapidapi.com"
RAPIDAPI_JSEARCH_ENDPOINT = "https://jsearch.p.rapidapi.com/search-v2"


def sanitize_external_id(raw_id: str | None) -> str:
    """
    Ensure external_id fits strictly within the PostgreSQL VARCHAR(255) column limit.
    For oversized provider IDs (>255 chars, common in JSearch base64 tokens),
    generates a deterministic, collision-free identifier (prefix + sha256 digest).
    """
    if not raw_id:
        return ""
    cleaned = str(raw_id).strip()
    if len(cleaned) <= 255:
        return cleaned
    digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
    return f"{cleaned[:200]}_{digest[:32]}"


def validate_url(url: str | None) -> str | None:
    """Validate that a URL has a valid http/https scheme and netloc."""
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    if not url:
        return None
    try:
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return url
    except (ValueError, AttributeError):
        pass
    return None


def parse_iso_or_timestamp(val: Any) -> datetime | None:
    """Parse ISO datetime string or Unix timestamp to timezone-aware UTC datetime."""
    if not val:
        return None
    if isinstance(val, (int, float)):
        try:
            return datetime.fromtimestamp(val, tz=timezone.utc)
        except (ValueError, TypeError, OSError):
            return None
    if isinstance(val, str):
        val = val.strip()
        try:
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            pass
    return None


async def fetch_jsearch_jobs(
    query: str,
    country: str = "in",
    date_posted: str = "all",
    employment_types: str | None = None,
    remote_jobs_only: bool = False,
    page: int = 1,
    num_pages: int = 1,
    cursor: str | None = None,
) -> dict[str, Any]:
    """
    Fetch job listings from the official RapidAPI JSearch search-v2 endpoint.
    Guarantees endpoint path strictly ends in /search-v2.
    Guarantees no automatic retries to protect free-tier credit consumption.
    """
    if not settings.jsearch_api_key or not settings.jsearch_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSearch API key is not configured. Please set JSEARCH_API_KEY in the backend environment.",
        )

    # Clean host and base URL
    clean_host = (settings.clean_jsearch_api_host or RAPIDAPI_JSEARCH_HOST).strip()
    clean_host = clean_host.replace("https://", "").replace("http://", "").strip("/")

    # Documented RapidAPI endpoint is strictly https://jsearch.p.rapidapi.com/search-v2
    raw_base = settings.clean_jsearch_base_url.rstrip("/")
    if not raw_base or "jsearch.p.rapidapi.com" in raw_base:
        url = RAPIDAPI_JSEARCH_ENDPOINT
    else:
        url = f"{raw_base}/search-v2"

    # Enforce strict outgoing URL invariants and catch any control characters, whitespace, or malformations
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme in JSearch request: {parsed_url.scheme!r}")
    if not parsed_url.netloc:
        raise ValueError(f"Missing host in JSearch request URL: {url!r}")
    if parsed_url.path != "/search-v2":
        raise ValueError(f"JSearch endpoint path must strictly be '/search-v2', got: {parsed_url.path!r}")
    if any(ord(c) < 32 or ord(c) == 127 for c in url):
        raise ValueError(f"Control characters detected in outgoing JSearch URL: {url!r}")

    # Safe diagnostic logging of URL components (strictly NEVER logging secrets, keys, or auth headers)
    logger.info(
        "JSearch outgoing request: scheme=%r host=%r path=%r repr(url)=%r has_control_chars=%s",
        parsed_url.scheme,
        clean_host,
        parsed_url.path,
        repr(url),
        any(ord(c) < 32 or ord(c) == 127 for c in url),
    )

    headers = {
        "X-RapidAPI-Key": settings.jsearch_api_key.strip(),
        "X-RapidAPI-Host": clean_host,
    }

    params: dict[str, Any] = {
        "query": query,
        "country": country,
        "page": str(page),
        "num_pages": str(num_pages),
    }

    if date_posted and date_posted != "all":
        params["date_posted"] = date_posted

    if employment_types:
        params["employment_types"] = employment_types

    if remote_jobs_only:
        params["remote_jobs_only"] = "true"

    if cursor:
        params["cursor"] = cursor

    timeout = httpx.Timeout(
        settings.jsearch_timeout_seconds,
        connect=settings.jsearch_connect_timeout_seconds,
        read=settings.jsearch_timeout_seconds,
        write=10.0,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers, params=params)

            if response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="JSearch API rate limit or monthly credit allowance exceeded. Please check your RapidAPI subscription.",
                )

            if response.status_code in (401, 403):
                error_body = response.text[:300]
                logger.error(
                    "JSearch provider authentication error %d: %s [url=%r host=%r]",
                    response.status_code,
                    error_body,
                    repr(url),
                    clean_host,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"JSearch provider authentication failed (status {response.status_code}): {error_body}",
                )

            if response.status_code == 404:
                error_body = response.text[:300]
                logger.error(
                    "JSearch provider returned 404 not found: %s [url=%r host=%r]",
                    error_body,
                    repr(url),
                    clean_host,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"JSearch provider endpoint not found (status 404): {error_body}",
                )

            if response.is_error:
                error_body = response.text[:300]
                logger.error(
                    "JSearch provider returned error status %d: %s [url=%r path=%r host=%r]",
                    response.status_code,
                    error_body,
                    repr(url),
                    parsed_url.path,
                    clean_host,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"JSearch API returned status {response.status_code}: {error_body}",
                )

            return response.json()

    except httpx.ConnectTimeout:
        logger.error(
            "JSearch provider connection timed out after %.1fs [host=%r]",
            settings.jsearch_connect_timeout_seconds,
            clean_host,
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"JSearch API connection timed out after {int(settings.jsearch_connect_timeout_seconds)} seconds. Provider gateway is unreachable.",
        )
    except httpx.ReadTimeout:
        logger.error(
            "JSearch provider read timed out after %.1fs [url=%r host=%r]",
            settings.jsearch_timeout_seconds,
            repr(url),
            clean_host,
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"JSearch API request timed out after {int(settings.jsearch_timeout_seconds)} seconds while waiting for response data. Provider may be experiencing slow response times.",
        )
    except httpx.TimeoutException as exc:
        logger.error(
            "JSearch provider request timed out (%s) [url=%r host=%r]",
            type(exc).__name__,
            repr(url),
            clean_host,
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"JSearch API request timed out after {int(settings.jsearch_timeout_seconds)} seconds. Provider may be experiencing slow response times.",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to communicate with JSearch API: {exc!s}",
        )


def parse_jsearch_payload(raw_response: Any) -> tuple[list[dict[str, Any]], str | None, dict[str, Any]]:
    """
    Safely extract jobs array, pagination cursor, and query parameters
    from observed JSearch response variations.
    """
    if not isinstance(raw_response, dict):
        if isinstance(raw_response, list):
            return raw_response, None, {}
        return [], None, {}

    # Check for error status in payload
    if raw_response.get("status") == "ERROR" or raw_response.get("error"):
        err_msg = raw_response.get("error") or raw_response.get("message") or "Provider returned an error status"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"JSearch returned error: {err_msg}",
        )

    parameters = raw_response.get("parameters", {})
    cursor = raw_response.get("cursor")
    data_field = raw_response.get("data")

    jobs_list: list[dict[str, Any]] = []

    if isinstance(data_field, dict):
        # Observed format: data.jobs array and data.cursor
        jobs_list = data_field.get("jobs", [])
        if not cursor:
            cursor = data_field.get("cursor")
    elif isinstance(data_field, list):
        # Alternative standard format: data array directly contains jobs
        jobs_list = data_field
    elif "jobs" in raw_response and isinstance(raw_response["jobs"], list):
        jobs_list = raw_response["jobs"]

    return jobs_list, cursor, parameters


async def get_canonical_skills_map(db: AsyncSession) -> dict[str, Skill]:
    """Build a mapping of normalized skill names and aliases to Skill models."""
    stmt = select(Skill).options(selectinload(Skill.aliases)).where(Skill.is_active.is_(True))
    result = await db.execute(stmt)
    skills = result.scalars().all()

    skills_map: dict[str, Skill] = {}
    for skill in skills:
        if skill.normalized_name:
            skills_map[skill.normalized_name.lower().strip()] = skill
        if skill.name:
            skills_map[skill.name.lower().strip()] = skill
        for alias in skill.aliases:
            if alias.normalized_alias:
                skills_map[alias.normalized_alias.lower().strip()] = skill
            if alias.alias:
                skills_map[alias.alias.lower().strip()] = skill

    return skills_map


def normalize_job_record(
    raw_job: dict[str, Any],
    existing_external_ids: set[str],
    skills_map: dict[str, Skill],
) -> JobPreviewItem:
    """
    Normalize raw JSearch job object to JobPreviewItem with thorough validation,
    conflict detection, and canonical skill matching.
    """
    warnings: list[str] = []
    errors: list[str] = []

    # 1. External ID
    job_id = str(raw_job.get("job_id") or "").strip()
    if not job_id:
        # Fallback to hashed title + company if job_id missing
        title_raw = str(raw_job.get("job_title") or "job")
        employer_raw = str(raw_job.get("employer_name") or "company")
        job_id = f"gen_{abs(hash(title_raw + employer_raw))}"
        warnings.append("Provider omitted stable job_id; generated internal identifier.")
    else:
        job_id = sanitize_external_id(job_id)

    # 2. Title & Company
    title = str(raw_job.get("job_title") or "").strip()
    if not title:
        errors.append("Job title is missing.")
        title = "Untitled Opportunity"

    company_name = str(raw_job.get("employer_name") or "").strip()
    if not company_name:
        errors.append("Employer name is missing.")
        company_name = "Unknown Employer"

    # 3. URLs
    company_website = validate_url(raw_job.get("employer_website"))
    company_logo_url = validate_url(raw_job.get("employer_logo"))
    
    apply_link = raw_job.get("job_apply_link") or raw_job.get("job_google_link")
    application_url = validate_url(apply_link)
    if not application_url:
        warnings.append("Missing or invalid application URL. Admin must provide URL before publishing.")

    # 4. Description
    description = raw_job.get("job_description") or ""
    if not description.strip():
        warnings.append("Job description is empty.")
        description = None

    # 5. Opportunity Type & Classification Conflict Detection
    # The observed response contains results where job_employment_types reports FULLTIME even when title includes 'Intern'.
    raw_emp_type = raw_job.get("job_employment_type")
    raw_emp_types_list = raw_job.get("job_employment_types") or []
    if isinstance(raw_emp_types_list, str):
        raw_emp_types_list = [raw_emp_types_list]
    if raw_emp_type and raw_emp_type not in raw_emp_types_list:
        raw_emp_types_list.append(raw_emp_type)

    normalized_types = [str(t).upper().strip() for t in raw_emp_types_list if t]

    title_lower = title.lower()
    has_intern_keyword = bool(re.search(r"\b(intern|internship|trainee|apprentice)\b", title_lower))

    classification_conflict = False
    opportunity_type = "Full-Time"

    if has_intern_keyword and any(t in ("FULLTIME", "FULL_TIME") for t in normalized_types) and not any(t in ("INTERN", "INTERNSHIP") for t in normalized_types):
        classification_conflict = True
        warnings.append(
            "Classification conflict: Job title includes 'Intern', but provider reports 'FULLTIME' employment type. Flagged for review."
        )
        opportunity_type = "Internship"
    elif has_intern_keyword or any(t in ("INTERN", "INTERNSHIP") for t in normalized_types):
        opportunity_type = "Internship"
    else:
        opportunity_type = "Full-Time"

    # 6. Work Model
    is_remote = bool(raw_job.get("job_is_remote"))
    full_text = f"{title} {description or ''} {raw_job.get('job_location', '')}".lower()
    if is_remote:
        work_model = "Remote"
    elif "hybrid" in full_text:
        work_model = "Hybrid"
    else:
        work_model = "On-site"

    # 7. Locations
    locations: list[str] | None = None
    city = raw_job.get("job_city")
    state = raw_job.get("job_state")
    country_val = raw_job.get("job_country")
    loc_parts = [p.strip() for p in (city, state, country_val) if p and isinstance(p, str) and p.strip()]

    if loc_parts:
        locations = [", ".join(loc_parts)]
    elif raw_job.get("job_location"):
        locations = [str(raw_job["job_location"]).strip()]
    elif work_model == "Remote":
        locations = ["Remote"]

    # 8. Salary / Stipend
    salary_min: int | None = None
    salary_max: int | None = None
    stipend_min: int | None = None
    stipend_max: int | None = None
    currency: str | None = None

    raw_min_sal = raw_job.get("job_min_salary")
    raw_max_sal = raw_job.get("job_max_salary")
    raw_curr = raw_job.get("job_salary_currency")
    raw_period = str(raw_job.get("job_salary_period") or "").upper().strip()

    if raw_curr and isinstance(raw_curr, str):
        currency = raw_curr.strip()[:10]

    try:
        val_min = round(float(raw_min_sal)) if raw_min_sal is not None else None
        val_max = round(float(raw_max_sal)) if raw_max_sal is not None else None

        if val_min is not None and val_min < 0:
            val_min = None
            warnings.append("Negative minimum salary value discarded.")
        if val_max is not None and val_max < 0:
            val_max = None
            warnings.append("Negative maximum salary value discarded.")

        if val_min is not None and val_max is not None and val_max < val_min:
            val_min, val_max = val_max, val_min
            warnings.append("Inverted salary range automatically corrected.")

        if val_min is not None or val_max is not None:
            if opportunity_type == "Internship" and raw_period == "MONTH":
                stipend_min = val_min
                stipend_max = val_max
            elif opportunity_type == "Internship" and raw_period in ("YEAR", ""):
                # If annual salary for internship, convert or store as salary
                salary_min = val_min
                salary_max = val_max
            else:
                salary_min = val_min
                salary_max = val_max
    except (ValueError, TypeError):
        warnings.append("Unparseable salary values omitted.")

    # 9. Dates
    posted_at = parse_iso_or_timestamp(
        raw_job.get("job_posted_at_datetime_utc") or raw_job.get("job_posted_at_timestamp")
    )
    if posted_at:
        now = datetime.now(timezone.utc)
        if posted_at < (now - timedelta(days=30)):
            warnings.append("Listing posted over 30 days ago and may be stale.")

    deadline = parse_iso_or_timestamp(
        raw_job.get("job_offer_expiration_datetime_utc") or raw_job.get("job_offer_expiration_timestamp")
    )
    if deadline:
        now = datetime.now(timezone.utc)
        if deadline < now:
            warnings.append("Listing expiration deadline has already elapsed.")
            deadline = None  # Do not set past deadline

    # 10. Canonical Skill Matching
    # Extract skills mentioned in JSearch job_required_skills
    raw_skills = raw_job.get("job_required_skills") or []
    if not isinstance(raw_skills, list):
        raw_skills = [str(raw_skills)]

    # Also check job_highlights -> Qualifications for mentions if skills array is empty
    highlights = raw_job.get("job_highlights", {})
    if isinstance(highlights, dict) and not raw_skills:
        qualifications = highlights.get("Qualifications", [])
        if isinstance(qualifications, list):
            # Scan for known skills in qualifications text
            qual_text = " ".join(str(q) for q in qualifications).lower()
            for key, sk in skills_map.items():
                if len(key) >= 3 and sk.name not in raw_skills and re.search(r"\b" + re.escape(key) + r"\b", qual_text):
                    raw_skills.append(sk.name)

    matched_skills: list[MatchedSkillItem] = []
    unmapped_skills: list[str] = []
    seen_matched_ids: set[UUID] = set()
    seen_unmapped: set[str] = set()

    for item in raw_skills:
        if not isinstance(item, str):
            continue
        cleaned = item.strip()
        if not cleaned:
            continue
        lookup_key = cleaned.lower()
        if lookup_key in skills_map:
            sk = skills_map[lookup_key]
            if sk.id not in seen_matched_ids:
                seen_matched_ids.add(sk.id)
                matched_skills.append(MatchedSkillItem(id=sk.id, name=sk.name))
        else:
            if lookup_key not in seen_unmapped:
                seen_unmapped.add(lookup_key)
                unmapped_skills.append(cleaned)

    # 11. Duplicate detection
    is_duplicate = job_id in existing_external_ids
    if is_duplicate:
        warnings.append("Listing has already been imported into CareerPilot.")

    # 12. Review required flag
    review_required = bool(classification_conflict or warnings or unmapped_skills or errors)

    return JobPreviewItem(
        job_id=job_id,
        title=title,
        company_name=company_name,
        company_website=company_website,
        company_logo_url=company_logo_url,
        description=description,
        opportunity_type=opportunity_type,
        work_model=work_model,
        locations=locations,
        application_url=application_url,
        publisher=raw_job.get("job_publisher"),
        posted_at=posted_at,
        deadline=deadline,
        salary_min=salary_min,
        salary_max=salary_max,
        stipend_min=stipend_min,
        stipend_max=stipend_max,
        currency=currency,
        matched_skills=matched_skills,
        unmapped_skills=unmapped_skills,
        is_duplicate=is_duplicate,
        review_required=review_required,
        warnings=warnings,
        errors=errors,
        classification_conflict=classification_conflict,
        raw_employment_types=normalized_types,
    )


async def preview_jsearch_ingestion(
    query: str,
    country: str = "in",
    date_posted: str = "all",
    employment_types: str | None = None,
    remote_jobs_only: bool = False,
    page: int = 1,
    num_pages: int = 1,
    db: AsyncSession | None = None,
) -> JSearchPreviewResponse:
    """
    Execute preview search against JSearch without writing to database.
    Normalizes response, checks duplicates against existing opportunities,
    and maps canonical skills.
    """
    raw_response = await fetch_jsearch_jobs(
        query=query,
        country=country,
        date_posted=date_posted,
        employment_types=employment_types,
        remote_jobs_only=remote_jobs_only,
        page=page,
        num_pages=num_pages,
    )

    jobs_raw, cursor, parameters = parse_jsearch_payload(raw_response)

    # Collect job IDs from response
    incoming_ids = [sanitize_external_id(str(j.get("job_id")).strip()) for j in jobs_raw if j.get("job_id")]

    # Check for existing records in DB
    existing_external_ids: set[str] = set()
    skills_map: dict[str, Skill] = {}

    if db is not None:
        if incoming_ids:
            dup_stmt = select(Opportunity.external_id).where(
                Opportunity.source_name == "JSearch",
                Opportunity.external_id.in_(incoming_ids),
            )
            dup_res = await db.execute(dup_stmt)
            existing_external_ids = set(dup_res.scalars().all())

        skills_map = await get_canonical_skills_map(db)

    # Normalize each job
    normalized_jobs: list[JobPreviewItem] = []
    seen_in_batch: set[str] = set()

    for r_job in jobs_raw:
        item = normalize_job_record(r_job, existing_external_ids, skills_map)
        if item.job_id in seen_in_batch:
            item.is_duplicate = True
            item.warnings.append("Duplicate listing within same provider result batch.")
            item.review_required = True
        else:
            seen_in_batch.add(item.job_id)
        normalized_jobs.append(item)

    valid_count = sum(1 for j in normalized_jobs if not j.errors and not j.is_duplicate)
    duplicate_count = sum(1 for j in normalized_jobs if j.is_duplicate)
    review_required_count = sum(1 for j in normalized_jobs if j.review_required)

    return JSearchPreviewResponse(
        jobs=normalized_jobs,
        total_found=len(normalized_jobs),
        cursor=cursor,
        parameters=parameters,
        summary=PreviewSummary(
            total_returned=len(normalized_jobs),
            valid_count=valid_count,
            duplicate_count=duplicate_count,
            review_required_count=review_required_count,
        ),
    )


async def import_jsearch_jobs(
    selected_job_ids: list[str],
    jobs: list[JobPreviewItem],
    admin_profile_id: UUID,
    db: AsyncSession,
) -> JSearchImportResponse:
    """
    Import explicitly selected jobs into the database as 'Draft'.
    Prevents duplicate imports, bypass of validation, and rogue skill creation.
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
        Opportunity.source_name == "JSearch",
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
        # Check errors
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

        # Check duplicate
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

        # Build Opportunity instance — always Draft, strictly respecting PostgreSQL column boundaries
        opportunity = Opportunity(
            title=item.title[:255] if item.title else "Untitled Opportunity",
            company_name=item.company_name[:255] if item.company_name else "Unknown Employer",
            company_website=item.company_website[:500] if item.company_website else None,
            company_logo_url=item.company_logo_url[:500] if item.company_logo_url else None,
            description=item.description,
            opportunity_type=item.opportunity_type if item.opportunity_type in ("Internship", "Full-Time") else "Internship",
            work_model=item.work_model if item.work_model in ("Remote", "Hybrid", "On-site") else "On-site",
            locations=item.locations,
            application_url=item.application_url[:500] if item.application_url else None,
            deadline=item.deadline,
            salary_min=item.salary_min,
            salary_max=item.salary_max,
            stipend_min=item.stipend_min,
            stipend_max=item.stipend_max,
            currency=item.currency[:10] if item.currency else None,
            source_name="JSearch",
            source_url=(item.application_url[:500] if item.application_url else None),
            external_id=sanitized_ext_id,
            status="Draft",  # Never silently published
            created_by_profile_id=admin_profile_id,
        )

        try:
            # Execute within a savepoint so a single record conflict doesn't abort the session transaction
            async with db.begin_nested():
                db.add(opportunity)
                await db.flush()  # Flush to get opportunity.id and verify uniqueness constraint

                # Add OpportunitySkills for valid canonical skills only
                for skill_item in item.matched_skills:
                    if skill_item.id in valid_skill_ids:
                        db.add(OpportunitySkill(opportunity_id=opportunity.id, skill_id=skill_item.id))

                await db.flush()
        except IntegrityError as exc:
            logger.warning("Duplicate import conflict for job %s: %s", item.job_id, exc)
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
            logger.exception("Failed to insert opportunity %s", item.job_id)
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
        already_imported_ids.add(item.job_id)
        already_imported_ids.add(sanitized_ext_id)
        details.append(
            ImportDetailItem(
                job_id=item.job_id,
                title=item.title,
                status="imported",
                opportunity_id=opportunity.id,
            )
        )

    try:
        await db.commit()
    except Exception as exc:
        logger.exception("Failed to commit imported opportunities")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database commit failed: {exc!s}",
        )

    return JSearchImportResponse(
        inserted_count=inserted_count,
        skipped_count=skipped_count,
        duplicate_count=duplicate_count,
        review_required_count=review_required_count,
        details=details,
    )
