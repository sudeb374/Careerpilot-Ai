"""
CareerPilot AI — Admin Bulk Upload Service (Phase 6.4)

Provides safe, validated CSV and JSON bulk opportunity ingestion for partner
organizations, campus drives, and fallback sources that lack direct APIs or RSS feeds.

Guarantees & Safeguards:
- Strict file bounds: <= 5MB file size, <= 500 rows/items max.
- UTF-8 validation (with utf-8-sig BOM support).
- HTML sanitization using stdlib regex (no HTML tags or executable markup).
- URL scheme validation (only http/https allowed, no javascript:, file:, data:).
- NEVER fetches or executes network calls to uploaded URLs.
- Cross-source duplicate detection against external IDs, URLs, and title::company signatures.
- Always saves new opportunities with status='Draft'.
- Transactional savepoints (db.begin_nested()) per row for isolated failure handling.
- Canonical skill mapping against active database skills catalog.
"""

import csv
import io
import json
import re
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import Opportunity, OpportunitySkill, utcnow
from app.models.profile import Skill
from app.schemas.ingestion import (
    BulkUploadImportResponse,
    BulkUploadPreviewResponse,
    ImportDetailItem,
    JobPreviewItem,
    MatchedSkillItem,
    PreviewSummary,
)
from app.services.jsearch import sanitize_external_id
from app.services.rss import clean_html_text, parse_rss_datetime

# Maximum file bounds
MAX_BULK_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_BULK_UPLOAD_ROWS = 500

# Supported content types and extensions
ALLOWED_EXTENSIONS = {".csv", ".json"}

# URL validation regex (only http and https schemes)
URL_REGEX = re.compile(
    r"^https?://[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"
    r"(:\d{1,5})?(/.*)?$",
    re.IGNORECASE,
)


def validate_upload_file_metadata(filename: str, file_bytes: bytes) -> str:
    """
    Validate file extension, file size, and clean filename.
    Returns cleaned file extension ('.csv' or '.json').
    """
    if len(file_bytes) > MAX_BULK_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {MAX_BULK_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    if not filename or "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a valid extension (.csv or .json).",
        )

    ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only .csv and .json files are supported.",
        )

    return ext


def parse_csv_rows(content: str) -> list[dict]:
    """Parse CSV text into list of sanitized dictionaries."""
    try:
        reader = csv.DictReader(io.StringIO(content))
        rows: list[dict] = []
        for r in reader:
            cleaned_row = {
                (k.strip().lower() if k else ""): (v.strip() if isinstance(v, str) else v)
                for k, v in r.items()
                if k is not None
            }
            # Skip empty rows
            if any(cleaned_row.values()):
                rows.append(cleaned_row)
        return rows
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV file: {str(e)}",
        )


def parse_json_rows(content: str) -> list[dict]:
    """Parse JSON text into list of dictionaries."""
    try:
        data = json.loads(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse JSON file: {str(e)}",
        )

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if "jobs" in data and isinstance(data["jobs"], list):
            items = data["jobs"]
        elif "opportunities" in data and isinstance(data["opportunities"], list):
            items = data["opportunities"]
        else:
            items = [data]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON root must be an array of objects or an object containing a 'jobs' array.",
        )

    # Clean keys to lowercase
    cleaned_rows: list[dict] = []
    for item in items:
        if isinstance(item, dict):
            cleaned = {
                (k.strip().lower() if isinstance(k, str) else str(k)): v
                for k, v in item.items()
            }
            cleaned_rows.append(cleaned)
    return cleaned_rows


def normalize_bulk_row(
    row: dict,
    row_index: int,
    existing_external_ids: set[str],
    existing_urls: set[str],
    existing_signatures: set[str],
    skills_map: dict[str, UUID],
) -> JobPreviewItem:
    """
    Validate, sanitize, and normalize a single bulk upload row.
    Never fetches remote URLs. Never trusts uploaded markup.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Title (required, varchar 255)
    raw_title = str(row.get("title") or "").strip()
    title = clean_html_text(raw_title)
    if not title:
        errors.append("Title is required.")
    elif len(title) > 255:
        title = title[:255]
        warnings.append("Title was truncated to 255 characters.")

    # 2. Company Name (required, varchar 255)
    raw_company = str(row.get("company_name") or row.get("company") or "").strip()
    company_name = clean_html_text(raw_company)
    if not company_name:
        errors.append("Company name is required.")
    elif len(company_name) > 255:
        company_name = company_name[:255]
        warnings.append("Company name was truncated to 255 characters.")

    # 3. External ID (varchar 255)
    raw_ext_id = str(row.get("external_id") or row.get("id") or "").strip()
    if raw_ext_id:
        external_id = sanitize_external_id(raw_ext_id)
    else:
        # Generate stable fallback ID based on index
        external_id = f"bulk-{row_index}-{uuid4().hex[:8]}"

    job_id = external_id

    # 4. Description (clean text)
    raw_desc = str(row.get("description") or "").strip()
    description = clean_html_text(raw_desc) if raw_desc else None

    # 5. Opportunity Type & Classification Conflict
    raw_type = str(row.get("opportunity_type") or row.get("type") or "").strip().lower()
    if "intern" in raw_type:
        opportunity_type = "Internship"
    elif "full" in raw_type:
        opportunity_type = "Full-Time"
    else:
        opportunity_type = "Internship"  # Default for student platform

    title_lower = title.lower()
    if "intern" in title_lower and opportunity_type == "Full-Time":
        warnings.append("Classification conflict: Title mentions 'intern' but type is Full-Time.")
    elif ("full-time" in title_lower or "full time" in title_lower) and opportunity_type == "Internship":
        warnings.append("Classification conflict: Title mentions 'full-time' but type is Internship.")

    # 6. Work Model
    raw_wm = str(row.get("work_model") or row.get("workplace") or "").strip().lower()
    if "hybrid" in raw_wm:
        work_model = "Hybrid"
    elif "on-site" in raw_wm or "onsite" in raw_wm or "office" in raw_wm:
        work_model = "On-site"
    else:
        work_model = "Remote"

    # 7. Locations (array of varchar)
    raw_loc = row.get("locations") or row.get("location")
    locations: list[str] = []
    if isinstance(raw_loc, list):
        for loc in raw_loc:
            cleaned_loc = clean_html_text(str(loc)).strip()
            if cleaned_loc:
                locations.append(cleaned_loc[:100])
    elif isinstance(raw_loc, str) and raw_loc.strip():
        for loc in raw_loc.split(","):
            cleaned_loc = clean_html_text(loc).strip()
            if cleaned_loc:
                locations.append(cleaned_loc[:100])

    # 8. Application URL & Company Website
    raw_app_url = str(row.get("application_url") or row.get("url") or row.get("link") or "").strip()
    application_url: str | None = None
    if raw_app_url:
        if raw_app_url.lower().startswith(("javascript:", "data:", "file:", "vbscript:")):
            errors.append("Invalid application URL scheme.")
        elif URL_REGEX.match(raw_app_url) and len(raw_app_url) <= 500:
            application_url = raw_app_url
        else:
            errors.append("Application URL must be a valid http:// or https:// link (max 500 chars).")

    raw_web_url = str(row.get("company_website") or row.get("website") or "").strip()
    company_website: str | None = None
    if raw_web_url:
        if URL_REGEX.match(raw_web_url) and len(raw_web_url) <= 500:
            company_website = raw_web_url
        else:
            warnings.append("Company website is not a valid URL (ignored).")

    # 9. Deadline
    raw_deadline = row.get("deadline") or row.get("expires_at") or row.get("application_deadline")
    deadline: datetime | None = None
    if raw_deadline:
        if isinstance(raw_deadline, datetime):
            deadline = raw_deadline
        elif isinstance(raw_deadline, str) and raw_deadline.strip():
            parsed_dl = parse_rss_datetime(raw_deadline.strip())
            if parsed_dl:
                deadline = parsed_dl
            else:
                try:
                    # ISO 8601 fallback
                    deadline = datetime.fromisoformat(raw_deadline.strip().replace("Z", "+00:00"))
                except Exception:
                    warnings.append(f"Unrecognized deadline format '{raw_deadline}' (ignored).")

    # 10. Salaries & Stipends
    def parse_int_field(val: any, field_name: str) -> int | None:
        if val is None or val == "":
            return None
        try:
            parsed = int(float(str(val).replace("$", "").replace(",", "").strip()))
            if parsed < 0:
                errors.append(f"{field_name} must be non-negative.")
                return None
            return parsed
        except ValueError:
            warnings.append(f"Could not parse numeric value for {field_name}.")
            return None

    stipend_min = parse_int_field(row.get("stipend_min"), "stipend_min")
    stipend_max = parse_int_field(row.get("stipend_max"), "stipend_max")
    salary_min = parse_int_field(row.get("salary_min"), "salary_min")
    salary_max = parse_int_field(row.get("salary_max"), "salary_max")

    if stipend_min is not None and stipend_max is not None and stipend_max < stipend_min:
        errors.append("stipend_max cannot be less than stipend_min.")
    if salary_min is not None and salary_max is not None and salary_max < salary_min:
        errors.append("salary_max cannot be less than salary_min.")

    currency = str(row.get("currency") or "USD").strip()[:10]

    # 11. Experience & Education
    req_exp_min = parse_int_field(row.get("required_experience_min") or 0, "required_experience_min") or 0
    req_exp_max = parse_int_field(row.get("required_experience_max"), "required_experience_max")
    if req_exp_max is not None and req_exp_max < req_exp_min:
        errors.append("required_experience_max cannot be less than required_experience_min.")

    domain = str(row.get("domain") or "").strip()[:255] or None
    education_requirements = clean_html_text(str(row.get("education_requirements") or "")) or None
    eligibility = clean_html_text(str(row.get("eligibility") or "")) or None

    # 12. Canonical Skill Mapping
    raw_skills = row.get("skills") or row.get("required_skills") or []
    candidate_skill_names: list[str] = []
    if isinstance(raw_skills, list):
        candidate_skill_names = [str(s).strip() for s in raw_skills if str(s).strip()]
    elif isinstance(raw_skills, str) and raw_skills.strip():
        candidate_skill_names = [s.strip() for s in raw_skills.split(",") if s.strip()]

    # Also scan title & description text for canonical skills if none explicitly provided
    if not candidate_skill_names and (title or description):
        text_corpus = f"{title} {description or ''}".lower()
        candidate_skill_names = [
            skill_name for skill_name in skills_map.keys()
            if re.search(r"\b" + re.escape(skill_name) + r"\b", text_corpus)
        ]

    matched_skills: list[MatchedSkillItem] = []
    unmatched_skills: list[str] = []
    seen_matched_ids: set[UUID] = set()

    for s_name in candidate_skill_names:
        norm_key = s_name.lower().strip()
        if norm_key in skills_map:
            s_id = skills_map[norm_key]
            if s_id not in seen_matched_ids:
                matched_skills.append(MatchedSkillItem(id=s_id, name=s_name))
                seen_matched_ids.add(s_id)
        else:
            if s_name not in unmatched_skills:
                unmatched_skills.append(s_name)

    # 13. Deduplication Checks
    is_duplicate = False
    if external_id in existing_external_ids:
        is_duplicate = True
        warnings.append("Duplicate: Matches an existing opportunity external ID.")

    if application_url and application_url.lower() in existing_urls:
        is_duplicate = True
        warnings.append("Duplicate: Matches an existing opportunity application URL.")

    signature = f"{title.lower()}::{company_name.lower()}"
    if signature in existing_signatures:
        is_duplicate = True
        warnings.append("Duplicate: Matches an existing title and company in the database.")

    review_required = bool(warnings) or (not bool(matched_skills)) or bool(unmatched_skills)

    return JobPreviewItem(
        job_id=job_id,
        title=title,
        company_name=company_name,
        company_website=company_website,
        company_logo_url=None,
        description=description,
        opportunity_type=opportunity_type,
        work_model=work_model,
        locations=locations,
        domain=domain,
        required_experience_min=req_exp_min,
        required_experience_max=req_exp_max,
        education_requirements=education_requirements,
        eligibility=eligibility,
        application_url=application_url,
        deadline=deadline,
        stipend_min=stipend_min,
        stipend_max=stipend_max,
        salary_min=salary_min,
        salary_max=salary_max,
        currency=currency,
        matched_skills=matched_skills,
        unmapped_skills=unmatched_skills,
        warnings=warnings,
        errors=errors,
        is_duplicate=is_duplicate,
        review_required=review_required,
    )


async def preview_bulk_upload(
    filename: str,
    file_bytes: bytes,
    db: AsyncSession,
) -> BulkUploadPreviewResponse:
    """
    Validate, parse, normalize, and preview uploaded CSV or JSON file.
    Performs cross-source deduplication and canonical skill matching.
    """
    ext = validate_upload_file_metadata(filename, file_bytes)

    # Decode UTF-8 (handling BOM)
    try:
        content = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not valid UTF-8 text. Please check encoding and re-upload.",
        )

    # Parse rows
    if ext == ".csv":
        raw_rows = parse_csv_rows(content)
    else:
        raw_rows = parse_json_rows(content)

    if not raw_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file contains no rows or valid opportunity items.",
        )

    if len(raw_rows) > MAX_BULK_UPLOAD_ROWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file contains {len(raw_rows)} rows, exceeding the limit of {MAX_BULK_UPLOAD_ROWS}.",
        )

    # Query existing database state for deduplication
    existing_ext_stmt = select(Opportunity.external_id).where(Opportunity.external_id.isnot(None))
    existing_ext_res = await db.execute(existing_ext_stmt)
    existing_external_ids = {ext_id for ext_id in existing_ext_res.scalars().all() if ext_id}

    existing_url_stmt = select(Opportunity.application_url).where(Opportunity.application_url.isnot(None))
    existing_url_res = await db.execute(existing_url_stmt)
    existing_urls = {u.lower() for u in existing_url_res.scalars().all() if u}

    existing_sig_stmt = select(
        func.lower(Opportunity.title),
        func.lower(Opportunity.company_name),
    )
    existing_sig_res = await db.execute(existing_sig_stmt)
    existing_signatures = {f"{t}::{c}" for t, c in existing_sig_res.all()}

    # Query active skills catalog
    skills_stmt = select(Skill.id, Skill.name).where(Skill.is_active.is_(True))
    skills_res = await db.execute(skills_stmt)
    skills_map = {name.lower().strip(): s_id for s_id, name in skills_res.all()}

    jobs: list[JobPreviewItem] = []
    valid_count = 0
    invalid_count = 0
    duplicate_count = 0
    review_required_count = 0

    for idx, row in enumerate(raw_rows, start=1):
        item = normalize_bulk_row(
            row=row,
            row_index=idx,
            existing_external_ids=existing_external_ids,
            existing_urls=existing_urls,
            existing_signatures=existing_signatures,
            skills_map=skills_map,
        )

        if item.errors:
            invalid_count += 1
        else:
            valid_count += 1

        if item.is_duplicate:
            duplicate_count += 1

        if item.review_required:
            review_required_count += 1

        jobs.append(item)

    clean_filename = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]

    return BulkUploadPreviewResponse(
        filename=clean_filename,
        total_rows=len(jobs),
        valid_count=valid_count,
        invalid_count=invalid_count,
        duplicate_count=duplicate_count,
        review_required_count=review_required_count,
        jobs=jobs,
        summary=PreviewSummary(
            total_returned=len(jobs),
            valid_count=valid_count,
            duplicate_count=duplicate_count,
            review_required_count=review_required_count,
        ),
    )


async def import_bulk_upload_jobs(
    db: AsyncSession,
    selected_job_ids: list[str],
    jobs: list[JobPreviewItem],
    admin_profile_id: UUID,
) -> BulkUploadImportResponse:
    """
    Import selected bulk upload items into CareerPilot database as Draft opportunities.
    Guarantees:
    - Status is always 'Draft'
    - Nested savepoints per row (db.begin_nested())
    - Canonical skill linking
    - Safe error isolation
    """
    selected_set = set(selected_job_ids)
    candidate_jobs = [j for j in jobs if j.job_id in selected_set]

    if not candidate_jobs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid preview jobs matched the selected job IDs.",
        )

    # 1. Existing external IDs query
    incoming_ids = [sanitize_external_id(j.job_id) for j in candidate_jobs]
    dup_stmt = select(Opportunity.external_id).where(
        Opportunity.source_name == "BulkUpload",
        Opportunity.external_id.in_(incoming_ids),
    )
    dup_res = await db.execute(dup_stmt)
    already_imported_ids = set(dup_res.scalars().all())

    # 2. Existing active skills
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
                    reason="Opportunity already exists in database.",
                )
            )
            continue

        # Transaction savepoint per row
        try:
            async with db.begin_nested():
                opportunity = Opportunity(
                    title=item.title[:255],
                    company_name=item.company_name[:255],
                    company_website=item.company_website[:500] if item.company_website else None,
                    company_logo_url=None,
                    description=item.description,
                    opportunity_type=item.opportunity_type,
                    work_model=item.work_model,
                    locations=item.locations,
                    domain=item.domain[:255] if item.domain else None,
                    required_experience_min=item.required_experience_min,
                    required_experience_max=item.required_experience_max,
                    education_requirements=item.education_requirements,
                    eligibility=item.eligibility,
                    application_url=item.application_url[:500] if item.application_url else None,
                    deadline=item.deadline,
                    stipend_min=item.stipend_min,
                    stipend_max=item.stipend_max,
                    salary_min=item.salary_min,
                    salary_max=item.salary_max,
                    currency=item.currency[:10] if item.currency else "USD",
                    source_name="BulkUpload",
                    source_url=None,
                    external_id=sanitized_ext_id,
                    status="Draft",  # Invariant: always Draft
                    created_by_profile_id=admin_profile_id,
                    created_at=utcnow(),
                    updated_at=utcnow(),
                )
                db.add(opportunity)
                await db.flush()

                # Attach canonical skills
                for skill_item in item.matched_skills:
                    if skill_item.id in valid_skill_ids:
                        db.add(
                            OpportunitySkill(
                                opportunity_id=opportunity.id,
                                skill_id=skill_item.id,
                            )
                        )

            inserted_count += 1
            if item.review_required:
                review_required_count += 1

            already_imported_ids.add(sanitized_ext_id)
            details.append(
                ImportDetailItem(
                    job_id=item.job_id,
                    opportunity_id=opportunity.id,
                    title=opportunity.title,
                    status="imported",
                    reason=None,
                )
            )
        except IntegrityError:
            duplicate_count += 1
            details.append(
                ImportDetailItem(
                    job_id=item.job_id,
                    title=item.title,
                    status="duplicate",
                    reason="Integrity violation (likely duplicate external ID or application URL).",
                )
            )
        except Exception as e:
            skipped_count += 1
            details.append(
                ImportDetailItem(
                    job_id=item.job_id,
                    title=item.title,
                    status="skipped",
                    reason=f"Database error: {str(e)}",
                )
            )

    await db.commit()

    return BulkUploadImportResponse(
        inserted_count=inserted_count,
        skipped_count=skipped_count,
        duplicate_count=duplicate_count,
        review_required_count=review_required_count,
        details=details,
    )
