from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Schemas for managing resume data, including requests for creating and updating resumes, and responses for retrieving resume information

# A schema for creating a new resume, which requires a title and content with specified minimum and maximum lengths for validation
class ResumeCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=50, max_length=50000)

# A schema for updating a resume, where both title and content are optional fields that can be updated individually, with validation for minimum and maximum lengths
class ResumeUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=50, max_length=50000)

# A schema for the response when retrieving resume information, which includes the resume's ID, associated user ID, title, 
# content, and timestamps for creation and last update
class ResumeResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
