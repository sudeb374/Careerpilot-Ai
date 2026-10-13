from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.models.profile import Profile
from app.schemas.ingestion import (
    JSearchImportRequest,
    JSearchImportResponse,
    JSearchPreviewRequest,
    JSearchPreviewResponse,
    RssImportRequest,
    RssImportResponse,
    RssPresetFeed,
    RssPreviewRequest,
    RssPreviewResponse,
)
from app.services.jsearch import import_jsearch_jobs, preview_jsearch_ingestion
from app.services.rss import (
    APPROVED_RSS_PRESETS,
    import_rss_jobs,
    preview_rss_feed,
)

router = APIRouter(
    prefix="/api/v1/admin/ingestion",
    tags=["Admin Job Ingestion"],
)


# -----------------------------------------------------------------------------
# JSearch Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/jsearch/preview",
    response_model=JSearchPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview job discovery from JSearch API",
)
async def preview_jsearch(
    body: JSearchPreviewRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    admin_user: Profile = Depends(require_admin),  # noqa: B008
):
    """
    Fetch job listings from JSearch, normalize fields, detect duplicates and classification conflicts,
    and return an actionable preview. Does not write to the database.
    Admin authorization required.
    """
    return await preview_jsearch_ingestion(
        query=body.query,
        country=body.country,
        date_posted=body.date_posted,
        employment_types=body.employment_types,
        remote_jobs_only=body.remote_jobs_only,
        page=body.page,
        num_pages=body.num_pages,
        db=db,
    )


@router.post(
    "/jsearch/import",
    response_model=JSearchImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Import selected jobs into opportunities catalog as Draft",
)
async def import_jsearch(
    body: JSearchImportRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    admin_user: Profile = Depends(require_admin),  # noqa: B008
):
    """
    Persistently import explicitly selected preview jobs into the database.
    Jobs are strictly imported as 'Draft' status for administrator verification.
    Prevents duplicates and rogue skill creation.
    Admin authorization required.
    """
    return await import_jsearch_jobs(
        selected_job_ids=body.selected_job_ids,
        jobs=body.jobs,
        admin_profile_id=admin_user.id,
        db=db,
    )


# -----------------------------------------------------------------------------
# RSS Ingestion Endpoints (Phase 6.3)
# -----------------------------------------------------------------------------

@router.get(
    "/rss/presets",
    response_model=list[RssPresetFeed],
    status_code=status.HTTP_200_OK,
    summary="Get approved RSS job feeds presets",
)
async def get_rss_presets(
    admin_user: Profile = Depends(require_admin),  # noqa: B008
):
    """Return curated list of verified RSS job feeds."""
    return APPROVED_RSS_PRESETS


@router.post(
    "/rss/preview",
    response_model=RssPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview job discovery from authorized RSS/Atom feed",
)
async def preview_rss(
    body: RssPreviewRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    admin_user: Profile = Depends(require_admin),  # noqa: B008
):
    """
    Fetch and parse job listings from an authorized RSS/Atom feed with SSRF protection,
    cross-source deduplication, and canonical skill matching.
    Admin authorization required.
    """
    return await preview_rss_feed(
        feed_url=body.feed_url,
        max_items=body.max_items,
        filter_keywords=body.filter_keywords,
        db=db,
    )


@router.post(
    "/rss/import",
    response_model=RssImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Import selected RSS jobs into opportunities catalog as Draft",
)
async def import_rss(
    body: RssImportRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    admin_user: Profile = Depends(require_admin),  # noqa: B008
):
    """
    Persistently import selected RSS preview jobs into the opportunities database.
    Always saved with 'Draft' status with isolated transaction savepoints.
    Admin authorization required.
    """
    return await import_rss_jobs(
        db=db,
        selected_job_ids=body.selected_job_ids,
        jobs=body.jobs,
        admin_profile_id=admin_user.id,
    )

