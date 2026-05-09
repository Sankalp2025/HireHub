import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.analysis import AnalysisResultResponse, AnalyzeRequest
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.analysis_service import (
    AnalysisInputError,
    AnalysisResourceNotFoundError,
    create_analysis,
    get_analysis_by_id,
    list_analyses,
)

router = APIRouter(prefix="/api/v1/analyses", tags=["analyses"])


@router.post(
    "",
    response_model=APIResponse[AnalysisResultResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_analysis_endpoint(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[AnalysisResultResponse]:
    try:
        analysis = await create_analysis(db, current_user.id, request)
    except AnalysisResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AnalysisInputError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return APIResponse(data=AnalysisResultResponse.model_validate(analysis), error=None)


@router.get("", response_model=APIResponse[PaginatedResponse[AnalysisResultResponse]])
async def list_analyses_endpoint(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[PaginatedResponse[AnalysisResultResponse]]:
    analyses, total = await list_analyses(db, current_user.id, page=page, per_page=per_page)
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return APIResponse(
        data=PaginatedResponse(
            items=[AnalysisResultResponse.model_validate(a) for a in analyses],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
        error=None,
    )


# or a 404 error if not found
@router.get("/{analysis_id}", response_model=APIResponse[AnalysisResultResponse])
async def get_analysis_endpoint(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[AnalysisResultResponse]:
    analysis = await get_analysis_by_id(db, current_user.id, analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    return APIResponse(data=AnalysisResultResponse.model_validate(analysis), error=None)
