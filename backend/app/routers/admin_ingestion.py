from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db, require_admin
from app.models.profile import Profile
from app.schemas.ingestion import (
    BulkUploadImportRequest,
    BulkUploadImportResponse,
    BulkUploadPreviewResponse,
    JSearchImportRequest,
    JSearchImportResponse,
    JSearchPreviewRequest,
    JSearchPreviewResponse,
    RefreshStatusResponse,
    RefreshTriggerResponse,
    RssImportRequest,
    RssImportResponse,
    RssPresetFeed,
    RssPreviewRequest,
    RssPreviewResponse,
)
from app.services.bulk_upload import import_bulk_upload_jobs, preview_bulk_upload
from app.services.jsearch import import_jsearch_jobs, preview_jsearch_ingestion
from app.services.rss import (
    APPROVED_RSS_PRESETS,
    import_rss_jobs,
    preview_rss_feed,
)
from app.services.scheduled_refresh import (
    execute_scheduled_refresh,
    get_last_refresh_summary,
    is_refresh_running,
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


# -----------------------------------------------------------------------------
# Fallback Bulk Upload Endpoints (Phase 6.4)
# -----------------------------------------------------------------------------

@router.post(
    "/bulk-upload/preview",
    response_model=BulkUploadPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview and validate CSV or JSON opportunity bulk upload",
)
async def preview_bulk_upload_endpoint(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),  # noqa: B008
    admin_user: Profile = Depends(require_admin),  # noqa: B008
):
    """
    Upload a CSV or JSON file containing job listings for validation and preview.
    Validates format, boundaries (<=5MB, <=500 rows), URL safety, cross-source
    duplicates, and canonical skills before committing.
    Admin authorization required.
    """
    file_bytes = await file.read()
    return await preview_bulk_upload(
        filename=file.filename or "upload.csv",
        file_bytes=file_bytes,
        db=db,
    )


@router.post(
    "/bulk-upload/import",
    response_model=BulkUploadImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Import selected bulk upload opportunities as Draft",
)
async def import_bulk_upload_endpoint(
    body: BulkUploadImportRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    admin_user: Profile = Depends(require_admin),  # noqa: B008
):
    """
    Import validated preview rows into opportunities database with status='Draft'.
    Uses transactional savepoints for robust isolated item handling.
    Admin authorization required.
    """
    return await import_bulk_upload_jobs(
        db=db,
        selected_job_ids=body.selected_job_ids,
        jobs=body.jobs,
        admin_profile_id=admin_user.id,
    )


# -----------------------------------------------------------------------------
# Scheduled Refresh & Expiration Endpoints (Phase 6.4)
# -----------------------------------------------------------------------------

@router.get(
    "/refresh/status",
    response_model=RefreshStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get scheduled refresh configuration and latest execution summary",
)
async def get_refresh_status(
    admin_user: Profile = Depends(require_admin),  # noqa: B008
):
    """
    Return current scheduled refresh settings and status of the latest refresh run.
    Admin authorization required.
    """
    summary = get_last_refresh_summary()
    return RefreshStatusResponse(
        enabled=settings.scheduled_refresh_enabled,
        interval_minutes=settings.scheduled_refresh_interval_minutes,
        jsearch_enabled=settings.scheduled_refresh_jsearch_enabled,
        jsearch_query=settings.scheduled_refresh_jsearch_query,
        jsearch_max_pages=settings.scheduled_refresh_jsearch_max_pages,
        rss_enabled=settings.scheduled_refresh_rss_enabled,
        rss_feed_urls=settings.scheduled_refresh_rss_feed_list,
        rss_max_items=settings.scheduled_refresh_rss_max_items,
        auto_expire=settings.scheduled_refresh_auto_expire,
        last_summary=summary,
    )


@router.post(
    "/refresh/trigger",
    response_model=RefreshTriggerResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger an immediate refresh cycle across authorized sources and auto-expire",
)
async def trigger_refresh(
    force: bool = Query(True, description="Force run even if scheduled refresh is disabled in settings"),
    db: AsyncSession = Depends(get_db),  # noqa: B008
    admin_user: Profile = Depends(require_admin),  # noqa: B008
):
    """
    Trigger immediate execution of opportunity refresh from RSS and JSearch,
    followed by deadline expiration of published opportunities.
    Admin authorization required.
    """
    if is_refresh_running():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A scheduled refresh is already in progress.",
        )

    summary = await execute_scheduled_refresh(
        db=db,
        admin_profile_id=admin_user.id,
        force=force,
    )

    return RefreshTriggerResponse(
        message="Refresh execution completed.",
        status=summary.status,
        summary=summary,
    )

