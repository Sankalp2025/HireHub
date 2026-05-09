from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.security import hash_password, verify_password

# Service functions for user authentication and management


# Helper function to normalize email addresses by stripping whitespace and converting to lowercase
def _normalize_email(email: str) -> str:
    return email.strip().lower()


# Function to retrieve a user by their email address from the database
async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == _normalize_email(email))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, request: RegisterRequest) -> User:
    existing_user = await get_user_by_email(db, request.email)

    if existing_user is not None:
        raise ValueError("Email already registered")

    user = User(
        email=_normalize_email(request.email),
        full_name=request.full_name.strip(),
        hashed_password=hash_password(request.password),
        is_active=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
