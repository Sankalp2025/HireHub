from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Schemas for user registration, login, and token responses in the authentication system

# The RegisterRequest schema defines the expected fields for user registration
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)

# The LoginRequest schema defines the expected fields for user login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

# The TokenResponse schema defines the structure of the response returned after successful authentication, including the access token and its type
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# The UserResponse schema defines the structure of the user information returned in API responses
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
