import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.security import decode_access_token

# This module defines dependencies for the FastAPI application, including authentication and database session management. 
# It provides functions to get the current user based on the JWT token and to retrieve a database session for use in API endpoints.

# OAuth2 scheme for token-based authentication, specifying the token URL for obtaining access tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Dependency to get the current authenticated user based on the JWT token provided in the request. 
# It decodes the token, retrieves the user from the database, and checks if the user is active.
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Attempt to decode the JWT token and extract the user ID from the subject claim. If decoding fails or the subject is missing, raise an authentication error.
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        user_id = uuid.UUID(subject)
    except (jwt.InvalidTokenError, ValueError):
        raise credentials_exception

    # Query the database for the user with the extracted user ID. 
    # If the user does not exist or is not active, raise an authentication error. Otherwise, return the user object.
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return user
