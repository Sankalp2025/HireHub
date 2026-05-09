import re
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_result import AnalysisResult
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.schemas.analysis import AnalyzeRequest
from app.services.skill_extractor import (
    COSINE_SCORE_WEIGHT,
    KEYWORD_SCORE_WEIGHT,
    compare_resume_to_jd,
)

# Service layer for handling analysis-related business logic, including creating analyses


class AnalysisInputError(ValueError):
    pass


class AnalysisResourceNotFoundError(LookupError):
    pass


def _generate_suggestions(resume_text: str, missing_skills: list[str]) -> list[str]:
    suggestions: list[str] = []

    if missing_skills:
        top_missing = ", ".join(missing_skills[:5])
        suggestions.append(f"Add evidence of these skills if you have them: {top_missing}.")

    if not re.search(r"\b\d+[%+]?\b", resume_text):
        suggestions.append("Use more quantified bullet points to show measurable impact.")

    suggestions.append("Tailor your summary and experience bullets to the target job description.")
    return suggestions


# with validation to ensure valid input
async def _get_resume_input(
    db: AsyncSession,
    user_id: UUID,
    request: AnalyzeRequest,
) -> tuple[UUID | None, str]:
    if request.resume_id is not None:
        stmt = select(Resume).where(
            Resume.id == request.resume_id,
            Resume.user_id == user_id,
            Resume.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        resume = result.scalar_one_or_none()
        if resume is None:
            raise AnalysisResourceNotFoundError("Resume not found")
        return resume.id, resume.content

    if request.resume_text is None:
        raise AnalysisInputError("Provide either resume_id or resume_text")

    return None, request.resume_text.strip()


# with validation to ensure valid input
async def _get_jd_input(
    db: AsyncSession,
    user_id: UUID,
    request: AnalyzeRequest,
) -> tuple[UUID | None, str]:
    if request.jd_id is not None:
        stmt = select(JobDescription).where(
            JobDescription.id == request.jd_id,
            JobDescription.user_id == user_id,
            JobDescription.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        job_description = result.scalar_one_or_none()
        if job_description is None:
            raise AnalysisResourceNotFoundError("Job description not found")
        return job_description.id, job_description.content

    if request.jd_text is None:
        raise AnalysisInputError("Provide either jd_id or jd_text")

    return None, request.jd_text.strip()


async def create_analysis(
    db: AsyncSession,
    user_id: UUID,
    request: AnalyzeRequest,
) -> AnalysisResult:
    resume_id, resume_text = await _get_resume_input(db, user_id, request)
    jd_id, jd_text = await _get_jd_input(db, user_id, request)

    match_result = compare_resume_to_jd(resume_text, jd_text)
    keyword_overlap = {
        "matched": match_result.matched,
        "missing": match_result.missing,
        "matched_count": match_result.matched_count,
        "total_jd_keywords": match_result.total_jd_keywords,
        "keyword_score": str(match_result.keyword_score),
        "cosine_similarity_score": str(match_result.cosine_similarity_score),
        "score_weights": {
            "keyword_score": str(KEYWORD_SCORE_WEIGHT),
            "cosine_similarity_score": str(COSINE_SCORE_WEIGHT),
        },
    }
    suggestions = _generate_suggestions(resume_text, match_result.missing)

    analysis = AnalysisResult(
        user_id=user_id,
        resume_id=resume_id,
        jd_id=jd_id,
        resume_snapshot=resume_text,
        jd_snapshot=jd_text,
        match_score=match_result.final_score,
        missing_skills=match_result.missing,
        suggestions=suggestions,
        keyword_overlap=keyword_overlap,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis


# Returns a page of analyses for a user plus the total unpaged count.
async def list_analyses(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[AnalysisResult], int]:
    base_filter = (AnalysisResult.user_id == user_id,)

    total: int = (
        await db.execute(select(func.count(AnalysisResult.id)).where(*base_filter))
    ).scalar_one()

    stmt = (
        select(AnalysisResult)
        .where(*base_filter)
        .order_by(AnalysisResult.analyzed_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def get_analysis_by_id(
    db: AsyncSession,
    user_id: UUID,
    analysis_id: UUID,
) -> AnalysisResult | None:
    stmt = select(AnalysisResult).where(
        AnalysisResult.id == analysis_id,
        AnalysisResult.user_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
