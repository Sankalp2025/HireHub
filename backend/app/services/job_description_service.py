from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_description import JobDescription
from app.schemas.job_description import (
    JobDescriptionCreateRequest,
    JobDescriptionUpdateRequest,
)


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


async def list_job_descriptions(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[JobDescription], int]:
    base_filter = (
        JobDescription.user_id == user_id,
        JobDescription.deleted_at.is_(None),
    )

    total: int = (
        await db.execute(select(func.count(JobDescription.id)).where(*base_filter))
    ).scalar_one()

    stmt = (
        select(JobDescription)
        .where(*base_filter)
        .order_by(JobDescription.updated_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


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


# and returning the updated job description object if found
async def update_job_description(
    db: AsyncSession,
    user_id: UUID,
    job_description_id: UUID,
    request: JobDescriptionUpdateRequest,
) -> JobDescription | None:
    job_description = await get_job_description_by_id(db, user_id, job_description_id)
    if job_description is None:
        return None

    # exclude_unset=True: fields the client didn't send are skipped entirely.
    # We do NOT also exclude_none so that nullable fields (company, role) can be cleared.
    updates = request.model_dump(exclude_unset=True)

    # title and content are non-nullable — guard against an explicit null value.
    if "title" in updates and updates["title"] is not None:
        job_description.title = updates["title"].strip()
    if "content" in updates and updates["content"] is not None:
        job_description.content = updates["content"].strip()
    # company and role are nullable — None is a valid value that clears the field.
    if "company" in updates:
        val = updates["company"]
        job_description.company = val.strip() if val is not None else None
    if "role" in updates:
        val = updates["role"]
        job_description.role = val.strip() if val is not None else None

    await db.commit()
    await db.refresh(job_description)
    return job_description


async def delete_job_description(
    db: AsyncSession,
    user_id: UUID,
    job_description_id: UUID,
) -> bool:
    job_description = await get_job_description_by_id(db, user_id, job_description_id)
    if job_description is None:
        return False

    job_description.deleted_at = datetime.now(UTC)
    await db.commit()
    return True
