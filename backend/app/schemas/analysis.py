from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Schemas for managing analysis requests and responses, including validation for input data and structured responses for analysis results

# The AnalyzeRequest schema defines the expected fields for requesting an analysis of a resume against a job description, allowing for either IDs 
# or raw text inputs for both the resume and job description, with validation to ensure that at least one form of input is provided for each
class AnalyzeRequest(BaseModel):
    resume_id: UUID | None = None
    jd_id: UUID | None = None
    resume_text: str | None = Field(default=None, min_length=50, max_length=50000)
    jd_text: str | None = Field(default=None, min_length=50, max_length=50000)

    # Validation to ensure that either resume_id or resume_text is provided, and either jd_id or jd_text is provided, to prevent invalid analysis requests
    @model_validator(mode="after")
    def validate_inputs(self) -> "AnalyzeRequest":
        has_resume_input = self.resume_id is not None or self.resume_text is not None
        has_jd_input = self.jd_id is not None or self.jd_text is not None

        if not has_resume_input:
            raise ValueError("Provide either resume_id or resume_text")
        if not has_jd_input:
            raise ValueError("Provide either jd_id or jd_text")

        return self

# The KeywordOverlapResponse schema defines the structure of the response for keyword overlap analysis, including lists of matched and missing keywords,
# the count of matched keywords, and the total number of keywords in the job description
class KeywordOverlapResponse(BaseModel):
    matched: list[str]
    missing: list[str]
    matched_count: int
    total_jd_keywords: int

# The AnalysisResultResponse schema defines the structure of the response for an analysis result, including the IDs of the analysis, user, resume, and job description,
# the match score, lists of missing skills and suggestions, the keyword overlap analysis, and the timestamp of when the analysis was performed
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
