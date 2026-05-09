from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AnalyzeRequest(BaseModel):
    resume_id: UUID | None = None
    jd_id: UUID | None = None
    resume_text: str | None = Field(default=None, min_length=50, max_length=50000)
    jd_text: str | None = Field(default=None, min_length=50, max_length=50000)

    @model_validator(mode="after")
    def validate_inputs(self) -> "AnalyzeRequest":
        has_resume_input = self.resume_id is not None or self.resume_text is not None
        has_jd_input = self.jd_id is not None or self.jd_text is not None

        if not has_resume_input:
            raise ValueError("Provide either resume_id or resume_text")
        if not has_jd_input:
            raise ValueError("Provide either jd_id or jd_text")

        return self


class ScoreWeightsResponse(BaseModel):
    keyword_score: Decimal
    cosine_similarity_score: Decimal


# the count of matched keywords, and the total number of keywords in the job description
class KeywordOverlapResponse(BaseModel):
    matched: list[str]
    missing: list[str]
    matched_count: int
    total_jd_keywords: int
    keyword_score: Decimal | None = None
    cosine_similarity_score: Decimal | None = None
    score_weights: ScoreWeightsResponse | None = None


class AnalysisResultResponse(BaseModel):
    id: UUID
    user_id: UUID
    resume_id: UUID | None
    jd_id: UUID | None
    match_score: Decimal
    missing_skills: list[str]
    suggestions: list[str]
    keyword_overlap: KeywordOverlapResponse
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)
