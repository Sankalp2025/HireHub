from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import APIResponse
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

# Router for managing resume-related API endpoints, including creating, listing, retrieving, updating, and deleting resumes for authenticated users
router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])

# Endpoint to create a new resume for the authenticated user, accepting a ResumeCreateRequest body and returning the created resume in the response
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

# Endpoint to list all resumes for the authenticated user, returning a list of ResumeResponse objects in the response
@router.get("", response_model=APIResponse[list[ResumeResponse]])
async def list_resumes_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[list[ResumeResponse]]:
    resumes = await list_resumes(db, current_user.id)
    return APIResponse(
        data=[ResumeResponse.model_validate(resume) for resume in resumes],
        error=None,
    )

# Endpoint to retrieve a specific resume by its ID for the authenticated user, returning the resume in the response if found, or a 404 error if not found
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

# Endpoint to update an existing resume by its ID for the authenticated user, accepting a ResumeUpdateRequest body with the fields to update, 
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

# Endpoint to delete a resume by its ID for the authenticated user, marking it as deleted and returning a 204 No Content response if successful, 
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
