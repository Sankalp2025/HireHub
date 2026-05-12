from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.schemas.resume import ResumeCreateRequest, ResumeUpdateRequest
from app.utils.pdf import extract_text_from_pdf


async def create_resume_from_pdf(
    db: AsyncSession,
    user_id: UUID,
    title: str,
    pdf_bytes: bytes,
) -> Resume:
    text = extract_text_from_pdf(pdf_bytes)

    if len(text) < 50:
        raise ValueError(
            "Could not extract sufficient text from the PDF. "
            "The file may be a scanned image or contain no selectable text. "
            "Minimum 50 characters required."
        )
    if len(text) > 50000:
        raise ValueError("Extracted text exceeds the maximum length of 50,000 characters.")

    request = ResumeCreateRequest(title=title, content=text)
    return await create_resume(db, user_id, request)


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


# Returns a page of resumes for a user (excluding soft-deleted) plus the total unpaged count.
async def list_resumes(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Resume], int]:
    base_filter = (Resume.user_id == user_id, Resume.deleted_at.is_(None))

    total: int = (await db.execute(select(func.count(Resume.id)).where(*base_filter))).scalar_one()

    stmt = (
        select(Resume)
        .where(*base_filter)
        .order_by(Resume.updated_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


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


async def update_resume(
    db: AsyncSession,
    user_id: UUID,
    resume_id: UUID,
    request: ResumeUpdateRequest,
) -> Resume | None:
    resume = await get_resume_by_id(db, user_id, resume_id)
    if resume is None:
        return None

    # exclude_unset=True: fields the client didn't send are skipped entirely.
    # We do NOT also exclude_none so that nullable fields can be explicitly cleared.
    updates = request.model_dump(exclude_unset=True)

    # title and content are non-nullable — guard against an explicit null value.
    if "title" in updates and updates["title"] is not None:
        resume.title = updates["title"].strip()
    if "content" in updates and updates["content"] is not None:
        resume.content = updates["content"].strip()

    await db.commit()
    await db.refresh(resume)
    return resume


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
