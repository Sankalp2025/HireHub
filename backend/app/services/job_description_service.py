from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_description import JobDescription
from app.schemas.job_description import (
    JobDescriptionCreateRequest,
    JobDescriptionUpdateRequest,
)

# Service functions for managing job descriptions, including creating, listing, retrieving, updating, and deleting job descriptions for users
async def create_job_description(
    db: AsyncSession,
    user_id: UUID,
    request: JobDescriptionCreateRequest,
) -> JobDescription:
    job_description = JobDescription(
        user_id=user_id,
        title=request.title.strip(),
        company=request.company.strip() if request.company else None,
        role=request.role.strip() if request.role else None,
        content=request.content.strip(),
    )
    db.add(job_description)
    await db.commit()
    await db.refresh(job_description)
    return job_description

# Function to list all job descriptions for a user, excluding those that have been marked as deleted, 
# and returning them in descending order of last update time
async def list_job_descriptions(
    db: AsyncSession,
    user_id: UUID,
) -> list[JobDescription]:
    stmt = (
        select(JobDescription)
        .where(
            JobDescription.user_id == user_id,
            JobDescription.deleted_at.is_(None),
        )
        .order_by(JobDescription.updated_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

# Function to retrieve a specific job description by its ID for a user, ensuring it has not been marked as deleted, 
# and returning the job description object if found
async def get_job_description_by_id(
    db: AsyncSession,
    user_id: UUID,
    job_description_id: UUID,
) -> JobDescription | None:
    stmt = select(JobDescription).where(
        JobDescription.id == job_description_id,
        JobDescription.user_id == user_id,
        JobDescription.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# Function to update an existing job description for a user by its ID, applying any provided updates to the title, company, role, and content,
# and returning the updated job description object if found
async def update_job_description(
    db: AsyncSession,
    user_id: UUID,
    job_description_id: UUID,
    request: JobDescriptionUpdateRequest,
) -> JobDescription | None:
    job_description = await get_job_description_by_id(
        db, user_id, job_description_id
    )
    if job_description is None:
        return None

    updates = request.model_dump(exclude_unset=True, exclude_none=True)

    if "title" in updates:
        job_description.title = updates["title"].strip()
    if "company" in updates:
        job_description.company = updates["company"].strip()
    if "role" in updates:
        job_description.role = updates["role"].strip()
    if "content" in updates:
        job_description.content = updates["content"].strip()

    await db.commit()
    await db.refresh(job_description)
    return job_description

# Function to delete a job description for a user by its ID, marking it as deleted and returning True if successful, or False if not found  
async def delete_job_description(
    db: AsyncSession,
    user_id: UUID,
    job_description_id: UUID,
) -> bool:
    job_description = await get_job_description_by_id(
        db, user_id, job_description_id
    )
    if job_description is None:
        return False

    job_description.deleted_at = datetime.now(UTC)
    await db.commit()
    return True
