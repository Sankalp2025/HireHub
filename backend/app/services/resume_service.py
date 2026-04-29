from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.schemas.resume import ResumeCreateRequest, ResumeUpdateRequest

# Service functions for managing resumes, including creating, listing, retrieving, updating, and deleting resumes for users

# Function to create a new resume for a user, saving it to the database and returning the created resume object
async def create_resume(
    db: AsyncSession,
    user_id: UUID,
    request: ResumeCreateRequest,
) -> Resume:
    resume = Resume(
        user_id=user_id,
        title=request.title.strip(),
        content=request.content.strip(),
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume

# Function to list all resumes for a user, excluding those that have been marked as deleted, and returning them in descending order of last update time
async def list_resumes(
    db: AsyncSession,
    user_id: UUID,
) -> list[Resume]:
    stmt = (
        select(Resume)
        .where(Resume.user_id == user_id, Resume.deleted_at.is_(None))
        .order_by(Resume.updated_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

# Function to retrieve a specific resume by its ID for a user, ensuring it has not been marked as deleted, and returning the resume object if found
async def get_resume_by_id(
    db: AsyncSession,
    user_id: UUID,
    resume_id: UUID,
) -> Resume | None:
    stmt = select(Resume).where(
        Resume.id == resume_id,
        Resume.user_id == user_id,
        Resume.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# Function to update an existing resume for a user by its ID, applying any provided updates to the title and content, and returning the updated resume object if found
async def update_resume(
    db: AsyncSession,
    user_id: UUID,
    resume_id: UUID,
    request: ResumeUpdateRequest,
) -> Resume | None:
    resume = await get_resume_by_id(db, user_id, resume_id)
    if resume is None:
        return None

    updates = request.model_dump(exclude_unset=True, exclude_none=True)

    if "title" in updates:
        resume.title = updates["title"].strip()
    if "content" in updates:
        resume.content = updates["content"].strip()

    await db.commit()
    await db.refresh(resume)
    return resume

# Function to delete a resume for a user by its ID, marking it as deleted by setting the deleted_at timestamp, and returning True if 
# the resume was found and marked as deleted, or False if the resume was not found
async def delete_resume(
    db: AsyncSession,
    user_id: UUID,
    resume_id: UUID,
) -> bool:
    resume = await get_resume_by_id(db, user_id, resume_id)
    if resume is None:
        return False

    resume.deleted_at = datetime.now(UTC)
    await db.commit()
    return True
