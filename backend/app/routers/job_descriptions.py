import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.job_description import (
    JobDescriptionCreateRequest,
    JobDescriptionResponse,
    JobDescriptionUpdateRequest,
)
from app.services.job_description_service import (
    create_job_description,
    delete_job_description,
    get_job_description_by_id,
    list_job_descriptions,
    update_job_description,
)

# Router for managing job description-related API endpoints, including creating,
# listing, retrieving, updating, and deleting job descriptions for authenticated users
router = APIRouter(prefix="/api/v1/job-descriptions", tags=["job-descriptions"])


# the created job description in the response
@router.post(
    "",
    response_model=APIResponse[JobDescriptionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_job_description_endpoint(
    request: JobDescriptionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[JobDescriptionResponse]:
    job_description = await create_job_description(db, current_user.id, request)
    return APIResponse(
        data=JobDescriptionResponse.model_validate(job_description),
        error=None,
    )


@router.get("", response_model=APIResponse[PaginatedResponse[JobDescriptionResponse]])
async def list_job_descriptions_endpoint(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[PaginatedResponse[JobDescriptionResponse]]:
    job_descriptions, total = await list_job_descriptions(
        db, current_user.id, page=page, per_page=per_page
    )
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return APIResponse(
        data=PaginatedResponse(
            items=[JobDescriptionResponse.model_validate(jd) for jd in job_descriptions],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
        error=None,
    )


# Endpoint to retrieve a specific job description by its ID for the authenticated user, returning
# the job description in the response if found, or a 404 error if not found
@router.get(
    "/{job_description_id}",
    response_model=APIResponse[JobDescriptionResponse],
)
async def get_job_description_endpoint(
    job_description_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[JobDescriptionResponse]:
    job_description = await get_job_description_by_id(db, current_user.id, job_description_id)
    if job_description is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found",
        )

    return APIResponse(
        data=JobDescriptionResponse.model_validate(job_description),
        error=None,
    )


# Endpoint to update an existing job description by its ID for the authenticated user, accepting a
# JobDescriptionUpdateRequest body with the fields to update
@router.patch(
    "/{job_description_id}",
    response_model=APIResponse[JobDescriptionResponse],
)
async def update_job_description_endpoint(
    job_description_id: UUID,
    request: JobDescriptionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[JobDescriptionResponse]:
    job_description = await update_job_description(db, current_user.id, job_description_id, request)
    if job_description is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found",
        )

    return APIResponse(
        data=JobDescriptionResponse.model_validate(job_description),
        error=None,
    )


# or a 404 error if not found
@router.delete("/{job_description_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_description_endpoint(
    job_description_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    deleted = await delete_job_description(db, current_user.id, job_description_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
