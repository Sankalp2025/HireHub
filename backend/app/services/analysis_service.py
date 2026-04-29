import re
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_result import AnalysisResult
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.schemas.analysis import AnalyzeRequest

# Service functions for performing analysis of resumes against job descriptions, including creating new analyses, listing analyses for a user, 
# and retrieving specific analysis results by ID

class AnalysisInputError(ValueError):
    pass


class AnalysisResourceNotFoundError(LookupError):
    pass

# Helper function to normalize text into a set of keywords by extracting words, converting to lowercase, and removing common stop words
def _normalize_keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]*", text.lower())
    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "have",
        "has",
        "in",
        "into",
        "is",
        "it",
        "of",
        "on",
        "or",
        "our",
        "that",
        "the",
        "their",
        "this",
        "to",
        "use",
        "using",
        "we",
        "will",
        "with",
        "you",
        "your",
    }
    return {word for word in words if len(word) > 1 and word not in stop_words}

# Helper function to build the keyword overlap analysis between a resume and a job description, returning the matched keywords, 
# missing keywords, and a summary of the overlap
def _build_keyword_overlap(
    resume_text: str,
    jd_text: str,
) -> tuple[list[str], list[str], dict[str, list[str] | int]]:
    resume_keywords = _normalize_keywords(resume_text)
    jd_keywords = _normalize_keywords(jd_text)

    matched = sorted(resume_keywords & jd_keywords)
    missing = sorted(jd_keywords - resume_keywords)

    keyword_overlap = {
        "matched": matched,
        "missing": missing,
        "matched_count": len(matched),
        "total_jd_keywords": len(jd_keywords),
    }
    return matched, missing, keyword_overlap

# Function to calculate the match score as a percentage of matched keywords out of total job description keywords, rounded to two decimal places
def _calculate_match_score(matched_count: int, total_jd_keywords: int) -> Decimal:
    if total_jd_keywords == 0:
        return Decimal("0.00")

    score = (Decimal(matched_count) / Decimal(total_jd_keywords)) * Decimal("100")
    return score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# Helper function to generate suggestions based on missing skills and the content of the resume, providing actionable advice to improve the match score
def _generate_suggestions(resume_text: str, missing_skills: list[str]) -> list[str]:
    suggestions: list[str] = []

    if missing_skills:
        top_missing = ", ".join(missing_skills[:5])
        suggestions.append(
            f"Add evidence of these skills if you have them: {top_missing}."
        )

    if not re.search(r"\b\d+[%+]?\b", resume_text):
        suggestions.append(
            "Use more quantified bullet points to show measurable impact."
        )

    suggestions.append(
        "Tailor your summary and experience bullets to the target job description."
    )
    return suggestions

# Function to get the resume input for analysis, either by retrieving the content of an existing resume by ID or using the provided raw text, 
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

# Function to get the job description input for analysis, either by retrieving the content of an existing job description by ID or using the provided raw text,
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

# Main function to create a new analysis by processing the resume and job description inputs, performing keyword overlap analysis, 
# calculating the match score, generating suggestions, and saving the analysis result to the database
async def create_analysis(
    db: AsyncSession,
    user_id: UUID,
    request: AnalyzeRequest,
) -> AnalysisResult:
    resume_id, resume_text = await _get_resume_input(db, user_id, request)
    jd_id, jd_text = await _get_jd_input(db, user_id, request)

    matched, missing, keyword_overlap = _build_keyword_overlap(resume_text, jd_text)
    match_score = _calculate_match_score(
        len(matched), int(keyword_overlap["total_jd_keywords"])
    )
    suggestions = _generate_suggestions(resume_text, missing)

    analysis = AnalysisResult(
        user_id=user_id,
        resume_id=resume_id,
        jd_id=jd_id,
        resume_snapshot=resume_text,
        jd_snapshot=jd_text,
        match_score=match_score,
        missing_skills=missing,
        suggestions=suggestions,
        keyword_overlap=keyword_overlap,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis

# Function to list all analyses for a user, returning them in descending order of analysis time, and allowing retrieval of specific analysis results by ID
async def list_analyses(
    db: AsyncSession,
    user_id: UUID,
) -> list[AnalysisResult]:
    stmt = (
        select(AnalysisResult)
        .where(AnalysisResult.user_id == user_id)
        .order_by(AnalysisResult.analyzed_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

# Function to retrieve a specific analysis result by its ID for a user, returning the analysis object if found, or None if not found
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
