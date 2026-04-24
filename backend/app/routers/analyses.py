from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.analysis import AnalysisResultResponse, AnalyzeRequest
from app.schemas.common import APIResponse
from app.services.analysis_service import (
    AnalysisInputError,
    AnalysisResourceNotFoundError,
    create_analysis,
    get_analysis_by_id,
    list_analyses,
)

# Router for managing analysis-related API endpoints, including creating new analyses, listing analyses for a user, and retrieving specific analysis results by ID
router = APIRouter(prefix="/api/v1/analyses", tags=["analyses"])

# Endpoint to create a new analysis for the authenticated user, accepting an AnalyzeRequest body and returning the created analysis result in the response
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

# Endpoint to list all analyses for the authenticated user, returning a list of AnalysisResultResponse objects in the response, 
# ordered by analysis time in descending order
@router.get("", response_model=APIResponse[list[AnalysisResultResponse]])
async def list_analyses_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[list[AnalysisResultResponse]]:
    analyses = await list_analyses(db, current_user.id)
    return APIResponse(
        data=[AnalysisResultResponse.model_validate(analysis) for analysis in analyses],
        error=None,
    )

# Endpoint to retrieve a specific analysis result by its ID for the authenticated user, returning the analysis result in the response if found, 
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
