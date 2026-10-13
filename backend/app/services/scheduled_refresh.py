"""
CareerPilot AI — Scheduled Refresh Service (Phase 6.4)

Orchestrates periodic synchronization of authorized external opportunity sources
(JSearch RapidAPI and approved RSS/Atom feeds) alongside deadline-based auto-expiration.

Architectural Guarantees:
- Concurrency Lock: Prevents overlapping runs within the process runtime.
- Quota & Rate Limit Protection: Bounded pagination (max 1 page for JSearch).
- Status Invariant: All newly discovered opportunities are inserted with status='Draft'.
- Safe Updates: For existing opportunities, preserves admin-reviewed classifications,
  publication status, titles, and company names. Only safe fields (deadline, valid application URL,
  salary, and updated_at) are refreshed.
- Independent Failure Isolation: Failures in one RSS feed or JSearch API do not abort others.
- Auto-Expiration: Automatically triggers deadline expiration for published opportunities.
- Auditable Summary: Detailed summary of inserted, updated, duplicate, and expired counts.
"""

import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.opportunity import Opportunity, OpportunitySkill, utcnow
from app.models.profile import Skill
from app.schemas.ingestion import (
    RefreshSourceDetail,
    RefreshSummary,
)
from app.services.jsearch import (
    fetch_jsearch_jobs,
    normalize_job_record,
    parse_jsearch_payload,
    sanitize_external_id,
)
from app.services.opportunity import expire_overdue_opportunities
from app.services.rss import (
    fetch_feed_content,
    normalize_rss_item,
    parse_xml_feed,
    validate_feed_url,
)

logger = logging.getLogger("careerpilot.scheduled_refresh")

# Global in-process lock and execution state tracker
_refresh_lock = asyncio.Lock()
_is_refresh_running: bool = False
_last_refresh_summary: RefreshSummary = RefreshSummary()


def is_refresh_running() -> bool:
    """Return whether a scheduled refresh is currently executing."""
    return _is_refresh_running


def get_last_refresh_summary() -> RefreshSummary:
    """Return the most recent refresh execution summary."""
    return _last_refresh_summary


async def execute_scheduled_refresh(
    db: AsyncSession,
    admin_profile_id: UUID | None = None,
    force: bool = False,
) -> RefreshSummary:
    """
    Execute a full refresh cycle across authorized RSS feeds and JSearch.
    
    If force=False and scheduled_refresh_enabled=False, returns immediately with skipped status.
    Uses concurrency locking to reject overlapping calls.
    """
    global _is_refresh_running, _last_refresh_summary

    if not force and not settings.scheduled_refresh_enabled:
        return RefreshSummary(
            status="skipped",
            errors=["Scheduled refresh is disabled in configuration."],
        )

    if _refresh_lock.locked() or _is_refresh_running:
        logger.warning("Scheduled refresh requested while an existing run is in progress.")
        return RefreshSummary(
            status="already_running",
            is_running=True,
            errors=["A scheduled refresh is already in progress."],
        )

    async with _refresh_lock:
        _is_refresh_running = True
        start_time = datetime.now(timezone.utc)
        summary = RefreshSummary(
            last_run_at=start_time,
            status="running",
            is_running=True,
            sources=[],
            errors=[],
        )

        try:
            # 1. Fetch active canonical skills for mapping
            skills_stmt = select(Skill).where(Skill.is_active.is_(True))
            skills_res = await db.execute(skills_stmt)
            skills_objs = skills_res.scalars().all()
            skills_obj_map = {s.name.lower().strip(): s for s in skills_objs}
            skills_id_map = {name: s.id for name, s in skills_obj_map.items()}

            # -----------------------------------------------------------------
            # 2. Process RSS Feeds
            # -----------------------------------------------------------------
            if settings.scheduled_refresh_rss_enabled:
                feed_urls = settings.scheduled_refresh_rss_feed_list
                for feed_url in feed_urls:
                    source_detail = RefreshSourceDetail(
                        source="RSS",
                        target=feed_url,
                        status="success",
                    )
                    try:
                        valid_url = validate_feed_url(feed_url)
                        raw_xml = await fetch_feed_content(valid_url)
                        feed_meta, raw_items = parse_xml_feed(raw_xml)

                        # Bound items
                        max_items = settings.scheduled_refresh_rss_max_items
                        selected_items = raw_items[:max_items]
                        source_detail.items_found = len(selected_items)

                        for item in selected_items:
                            # Normalize item
                            preview_item = normalize_rss_item(
                                item,
                                existing_external_ids=set(),
                                existing_urls=set(),
                                existing_signatures=set(),
                                skills_map=skills_id_map,
                            )
                            if preview_item.errors:
                                continue

                            sanitized_ext_id = sanitize_external_id(preview_item.job_id)

                            # Check if opportunity already exists
                            stmt = select(Opportunity).where(
                                Opportunity.source_name == "RSS",
                                Opportunity.external_id == sanitized_ext_id,
                            )
                            res = await db.execute(stmt)
                            existing_opp = res.scalars().first()

                            if existing_opp:
                                # Safe update: only touch allowed source-controlled fields
                                updated = False
                                if preview_item.deadline and existing_opp.deadline != preview_item.deadline:
                                    existing_opp.deadline = preview_item.deadline
                                    updated = True
                                if preview_item.application_url and existing_opp.application_url != preview_item.application_url:
                                    existing_opp.application_url = preview_item.application_url
                                    updated = True

                                if updated:
                                    existing_opp.updated_at = utcnow()
                                    source_detail.items_updated += 1
                                    summary.total_updated += 1
                                else:
                                    source_detail.items_duplicate += 1
                                    summary.total_duplicates += 1
                            else:
                                # New item: Insert with status='Draft'
                                try:
                                    async with db.begin_nested():
                                        new_opp = Opportunity(
                                            title=preview_item.title[:255],
                                            company_name=preview_item.company_name[:255],
                                            company_website=preview_item.company_website[:500] if preview_item.company_website else None,
                                            company_logo_url=preview_item.company_logo_url[:500] if preview_item.company_logo_url else None,
                                            description=preview_item.description,
                                            opportunity_type=preview_item.opportunity_type,
                                            work_model=preview_item.work_model,
                                            locations=preview_item.locations,
                                            domain=getattr(preview_item, "domain", None),
                                            required_experience_min=preview_item.required_experience_min,
                                            required_experience_max=preview_item.required_experience_max,
                                            education_requirements=preview_item.education_requirements,
                                            eligibility=preview_item.eligibility,
                                            application_url=preview_item.application_url[:500] if preview_item.application_url else None,
                                            deadline=preview_item.deadline,
                                            stipend_min=preview_item.stipend_min,
                                            stipend_max=preview_item.stipend_max,
                                            salary_min=preview_item.salary_min,
                                            salary_max=preview_item.salary_max,
                                            currency=preview_item.currency[:10] if preview_item.currency else "USD",
                                            source_name="RSS",
                                            source_url=getattr(preview_item, "source_url", None),
                                            external_id=sanitized_ext_id,
                                            status="Draft",  # Strictly Draft
                                            created_by_profile_id=admin_profile_id,
                                            created_at=utcnow(),
                                            updated_at=utcnow(),
                                        )
                                        db.add(new_opp)
                                        await db.flush()

                                        for s in preview_item.matched_skills:
                                            db.add(
                                                OpportunitySkill(
                                                    opportunity_id=new_opp.id,
                                                    skill_id=s.id,
                                                )
                                            )
                                    source_detail.items_inserted += 1
                                    summary.total_inserted += 1
                                except IntegrityError:
                                    source_detail.items_duplicate += 1
                                    summary.total_duplicates += 1

                        await db.commit()
                    except Exception as e:
                        logger.error(f"Error refreshing RSS feed {feed_url}: {str(e)}")
                        source_detail.status = "error"
                        source_detail.error = str(e)
                        summary.errors.append(f"RSS ({feed_url}): {str(e)}")

                    summary.sources.append(source_detail)

            # -----------------------------------------------------------------
            # 3. Process JSearch (if enabled and configured)
            # -----------------------------------------------------------------
            if settings.scheduled_refresh_jsearch_enabled:
                if not settings.jsearch_api_key or not settings.jsearch_api_key.strip():
                    summary.sources.append(
                        RefreshSourceDetail(
                            source="JSearch",
                            target="RapidAPI",
                            status="skipped",
                            error="JSearch API key is not configured.",
                        )
                    )
                else:
                    jsearch_detail = RefreshSourceDetail(
                        source="JSearch",
                        target=f"Query: {settings.scheduled_refresh_jsearch_query}",
                        status="success",
                    )
                    try:
                        raw_payload = await fetch_jsearch_jobs(
                            query=settings.scheduled_refresh_jsearch_query,
                            page=1,
                            num_pages=settings.scheduled_refresh_jsearch_max_pages,
                        )
                        raw_jobs = parse_jsearch_payload(raw_payload)
                        jsearch_detail.items_found = len(raw_jobs)

                        for raw_job in raw_jobs:
                            preview_job = normalize_job_record(
                                raw_job,
                                existing_external_ids=set(),
                                skills_map=skills_obj_map,
                            )
                            if preview_job.errors:
                                continue

                            sanitized_ext_id = sanitize_external_id(preview_job.job_id)

                            stmt = select(Opportunity).where(
                                Opportunity.source_name == "JSearch",
                                Opportunity.external_id == sanitized_ext_id,
                            )
                            res = await db.execute(stmt)
                            existing_opp = res.scalars().first()

                            if existing_opp:
                                updated = False
                                if preview_job.deadline and existing_opp.deadline != preview_job.deadline:
                                    existing_opp.deadline = preview_job.deadline
                                    updated = True
                                if preview_job.application_url and existing_opp.application_url != preview_job.application_url:
                                    existing_opp.application_url = preview_job.application_url
                                    updated = True

                                if updated:
                                    existing_opp.updated_at = utcnow()
                                    jsearch_detail.items_updated += 1
                                    summary.total_updated += 1
                                else:
                                    jsearch_detail.items_duplicate += 1
                                    summary.total_duplicates += 1
                            else:
                                try:
                                    async with db.begin_nested():
                                        new_opp = Opportunity(
                                            title=preview_job.title[:255],
                                            company_name=preview_job.company_name[:255],
                                            company_website=preview_job.company_website[:500] if preview_job.company_website else None,
                                            company_logo_url=preview_job.company_logo_url[:500] if preview_job.company_logo_url else None,
                                            description=preview_job.description,
                                            opportunity_type=preview_job.opportunity_type,
                                            work_model=preview_job.work_model,
                                            locations=preview_job.locations,
                                            domain=getattr(preview_job, "domain", None),
                                            required_experience_min=preview_job.required_experience_min,
                                            required_experience_max=preview_job.required_experience_max,
                                            education_requirements=preview_job.education_requirements,
                                            eligibility=preview_job.eligibility,
                                            application_url=preview_job.application_url[:500] if preview_job.application_url else None,
                                            deadline=preview_job.deadline,
                                            stipend_min=preview_job.stipend_min,
                                            stipend_max=preview_job.stipend_max,
                                            salary_min=preview_job.salary_min,
                                            salary_max=preview_job.salary_max,
                                            currency=preview_job.currency[:10] if preview_job.currency else "USD",
                                            source_name="JSearch",
                                            source_url=getattr(preview_job, "source_url", None),
                                            external_id=sanitized_ext_id,
                                            status="Draft",  # Invariant: always Draft
                                            created_by_profile_id=admin_profile_id,
                                            created_at=utcnow(),
                                            updated_at=utcnow(),
                                        )
                                        db.add(new_opp)
                                        await db.flush()

                                        for s in preview_job.matched_skills:
                                            db.add(
                                                OpportunitySkill(
                                                    opportunity_id=new_opp.id,
                                                    skill_id=s.id,
                                                )
                                            )
                                    jsearch_detail.items_inserted += 1
                                    summary.total_inserted += 1
                                except IntegrityError:
                                    jsearch_detail.items_duplicate += 1
                                    summary.total_duplicates += 1

                        await db.commit()
                    except Exception as e:
                        logger.error(f"Error refreshing JSearch: {str(e)}")
                        jsearch_detail.status = "error"
                        jsearch_detail.error = str(e)
                        summary.errors.append(f"JSearch: {str(e)}")

                    summary.sources.append(jsearch_detail)

            # -----------------------------------------------------------------
            # 4. Auto-Expire Overdue Published Opportunities
            # -----------------------------------------------------------------
            if settings.scheduled_refresh_auto_expire:
                try:
                    expired_count = await expire_overdue_opportunities(db)
                    summary.total_expired = expired_count
                except Exception as e:
                    logger.error(f"Error during auto-expiration: {str(e)}")
                    summary.errors.append(f"Auto-expiration: {str(e)}")

            # Finalize status
            end_time = datetime.now(timezone.utc)
            summary.duration_seconds = round((end_time - start_time).total_seconds(), 2)
            summary.is_running = False

            if not summary.errors:
                summary.status = "success"
            elif summary.total_inserted > 0 or summary.total_updated > 0:
                summary.status = "partial_failure"
            else:
                summary.status = "failed"

            _last_refresh_summary = summary
            return summary

        except Exception as e:
            logger.error(f"Fatal unhandled error during scheduled refresh: {str(e)}")
            summary.status = "failed"
            summary.is_running = False
            summary.errors.append(f"Fatal error: {str(e)}")
            _last_refresh_summary = summary
            return summary
        finally:
            _is_refresh_running = False
