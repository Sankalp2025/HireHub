from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Schemas for managing job description data, including requests for creating and updating job descriptions, 
# and responses for retrieving job description information
class JobDescriptionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    company: str | None = Field(default=None, min_length=1, max_length=200)
    role: str | None = Field(default=None, min_length=1, max_length=200)
    content: str = Field(min_length=50, max_length=50000)

# A schema for updating a job description, where all fields are optional and can be updated individually, with validation for minimum and maximum lengths
class JobDescriptionUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    company: str | None = Field(default=None, min_length=1, max_length=200)
    role: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=50, max_length=50000)

# A schema for the response when retrieving job description information, which includes the job description's ID, a
# ssociated user ID, title, company, role,
class JobDescriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    company: str | None
    role: str | None
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
