import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.resume import (
    ResumeCreateRequest,
    ResumeResponse,
    ResumeUpdateRequest,
)
from app.services.resume_service import (
    create_resume,
    delete_resume,
    get_resume_by_id,
    list_resumes,
    update_resume,
)

router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])


@router.post(
    "",
    response_model=APIResponse[ResumeResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_resume_endpoint(
    request: ResumeCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ResumeResponse]:
    resume = await create_resume(db, current_user.id, request)
    return APIResponse(data=ResumeResponse.model_validate(resume), error=None)


@router.get("", response_model=APIResponse[PaginatedResponse[ResumeResponse]])
async def list_resumes_endpoint(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[PaginatedResponse[ResumeResponse]]:
    resumes, total = await list_resumes(db, current_user.id, page=page, per_page=per_page)
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return APIResponse(
        data=PaginatedResponse(
            items=[ResumeResponse.model_validate(r) for r in resumes],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
        error=None,
    )


@router.get("/{resume_id}", response_model=APIResponse[ResumeResponse])
async def get_resume_endpoint(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ResumeResponse]:
    resume = await get_resume_by_id(db, current_user.id, resume_id)
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    return APIResponse(data=ResumeResponse.model_validate(resume), error=None)


# and returning the updated resume in the response if found, or a 404 error if not found
@router.patch("/{resume_id}", response_model=APIResponse[ResumeResponse])
async def update_resume_endpoint(
    resume_id: UUID,
    request: ResumeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ResumeResponse]:
    resume = await update_resume(db, current_user.id, resume_id, request)
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    return APIResponse(data=ResumeResponse.model_validate(resume), error=None)


# or a 404 error if not found
@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume_endpoint(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    deleted = await delete_resume(db, current_user.id, resume_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
