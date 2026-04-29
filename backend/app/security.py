from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.config import settings

# This module provides utility functions for password hashing, token creation, and token decoding for user authentication and authorization.

password_hash = PasswordHash.recommended()

# Function to hash a plain text password 
def hash_password(password: str) -> str:
    return password_hash.hash(password)

# Function to verify a plain text password against a hashed password, returning True if they match and False otherwise
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False

# Function to create a JWT access token with a subject and an expiration time, using the secret key and algorithm defined in the settings
def create_access_token(subject: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": subject,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

# Function to decode a JWT access token and return the payload as a dictionary, using the secret key and algorithm defined in the settings
def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
