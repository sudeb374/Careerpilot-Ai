from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.models.profile import Profile
from app.schemas.ingestion import (
    JSearchImportRequest,
    JSearchImportResponse,
    JSearchPreviewRequest,
    JSearchPreviewResponse,
)
from app.services.jsearch import import_jsearch_jobs, preview_jsearch_ingestion

router = APIRouter(
    prefix="/api/v1/admin/ingestion/jsearch",
    tags=["Admin Job Ingestion"],
)


@router.post(
    "/preview",
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
    "/import",
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
