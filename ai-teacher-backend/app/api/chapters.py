"""Chapter management API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import require_admin
from app.models.course import Edition, Subject, CourseStatus
from app.models.student import Student
from app.repositories.memory_db import db
from app.schemas.chapter import (
    ChapterCreate,
    ChapterUpdate,
    ChapterResponse,
    ChapterListResponse,
)
from app.schemas.common import APIResponse

router = APIRouter(prefix="/admin/chapters", tags=["章节管理"])


def _generate_chapter_id(grade: str, edition: Edition, subject: Subject, name: str) -> str:
    """Generate chapter ID.

    Format: CH_{SUBJECT}_{GRADE}_{EDITION}_{NUM}

    Args:
        grade: Grade string.
        edition: Edition enum.
        subject: Subject enum.
        name: Chapter name.

    Returns:
        Generated chapter ID.
    """
    # Map grade to number
    grade_map = {
        "初一": "7", "初二": "8", "初三": "9",
        "高一": "10", "高二": "11", "高三": "12"
    }
    
    # Count existing chapters with same grade/edition/subject
    count = sum(
        1 for ch in db._chapters.values()
        if ch.grade == grade and ch.edition == edition and ch.subject == subject
    )
    
    grade_num = grade_map.get(grade, "7")
    subject_name = subject.value
    edition_short = {
        Edition.RENJIAO: "REN",
        Edition.BEISHIDA: "BSD",
        Edition.SUJIAO: "SU",
        Edition.LUJIAO: "LU",
        Edition.HUASHIDA: "HSD",
        Edition.RENJIAO_NEW: "REN_NEW",
    }.get(edition, "REN")
    
    return f"CH_{subject_name}_{grade_num}_{edition_short}_{count + 1:02d}"


@router.get("", response_model=APIResponse[ChapterListResponse])
async def list_chapters(
    grade: Optional[str] = Query(None, description="年级筛选"),
    edition: Optional[Edition] = Query(None, description="版本筛选"),
    subject: Optional[Subject] = Query(None, description="科目筛选"),
    status: Optional[CourseStatus] = Query(None, description="状态筛选"),
    current_admin: Student = Depends(require_admin),
) -> APIResponse[ChapterListResponse]:
    """List chapters with optional filters.

    Args:
        grade: Filter by grade.
        edition: Filter by edition.
        subject: Filter by subject.
        status: Filter by status.
        current_admin: Current admin user.

    Returns:
        List of chapters.
    """
    chapters = list(db._chapters.values())
    
    # Apply filters
    if grade:
        chapters = [ch for ch in chapters if ch.grade == grade]
    if edition:
        chapters = [ch for ch in chapters if ch.edition == edition]
    if subject:
        chapters = [ch for ch in chapters if ch.subject == subject]
    if status:
        chapters = [ch for ch in chapters if ch.status == status]
    
    # Sort by sort_order, then by created_at
    chapters.sort(key=lambda ch: (ch.sort_order, ch.created_at))
    
    return APIResponse(
        success=True,
        data=ChapterListResponse(
            chapters=[ChapterResponse.from_domain(ch) for ch in chapters],
            total=len(chapters),
            grade=grade,
            edition=edition,
            subject=subject,
        ),
    )


@router.post("", response_model=APIResponse[ChapterResponse], status_code=status.HTTP_201_CREATED)
async def create_chapter(
    chapter_data: ChapterCreate,
    current_admin: Student = Depends(require_admin),
) -> APIResponse[ChapterResponse]:
    """Create a new chapter.

    Args:
        chapter_data: Chapter creation data.
        current_admin: Current admin user.

    Returns:
        Created chapter.

    Raises:
        HTTPException: If chapter already exists.
    """
    # Check for duplicate
    for existing_ch in db._chapters.values():
        if (existing_ch.grade == chapter_data.grade and
            existing_ch.edition == chapter_data.edition and
            existing_ch.subject == chapter_data.subject and
            existing_ch.name == chapter_data.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该章节已存在",
            )
    
    # Generate chapter ID
    from app.models.course import Chapter
    chapter_id = _generate_chapter_id(
        chapter_data.grade,
        chapter_data.edition,
        chapter_data.subject,
        chapter_data.name,
    )
    
    # Create chapter
    chapter = Chapter(
        id=chapter_id,
        name=chapter_data.name,
        grade=chapter_data.grade,
        edition=chapter_data.edition,
        subject=chapter_data.subject,
        description=chapter_data.description,
        sort_order=chapter_data.sort_order,
        estimated_hours=chapter_data.estimated_hours,
        level_descriptions=chapter_data.level_descriptions,
        status=CourseStatus.ACTIVE,
    )
    
    db._chapters[chapter.id] = chapter
    
    return APIResponse(
        success=True,
        data=ChapterResponse.from_domain(chapter),
        message="章节创建成功",
    )


@router.get("/{chapter_id}", response_model=APIResponse[ChapterResponse])
async def get_chapter(
    chapter_id: str,
    current_admin: Student = Depends(require_admin),
) -> APIResponse[ChapterResponse]:
    """Get chapter by ID.

    Args:
        chapter_id: Chapter ID.
        current_admin: Current admin user.

    Returns:
        Chapter details.

    Raises:
        HTTPException: If chapter not found.
    """
    chapter = db._chapters.get(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在",
        )
    
    return APIResponse(
        success=True,
        data=ChapterResponse.from_domain(chapter),
    )


@router.put("/{chapter_id}", response_model=APIResponse[ChapterResponse])
async def update_chapter(
    chapter_id: str,
    chapter_data: ChapterUpdate,
    current_admin: Student = Depends(require_admin),
) -> APIResponse[ChapterResponse]:
    """Update chapter.

    Args:
        chapter_id: Chapter ID.
        chapter_data: Chapter update data.
        current_admin: Current admin user.

    Returns:
        Updated chapter.

    Raises:
        HTTPException: If chapter not found.
    """
    chapter = db._chapters.get(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在",
        )
    
    # Update fields
    update_data = chapter_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chapter, field, value)
    
    # Update timestamp
    from datetime import datetime
    chapter.updated_at = datetime.now()
    
    return APIResponse(
        success=True,
        data=ChapterResponse.from_domain(chapter),
        message="章节更新成功",
    )


@router.delete("/{chapter_id}")
async def delete_chapter(
    chapter_id: str,
    current_admin: Student = Depends(require_admin),
) -> APIResponse[None]:
    """Delete chapter.

    Args:
        chapter_id: Chapter ID.
        current_admin: Current admin user.

    Returns:
        Success message.

    Raises:
        HTTPException: If chapter not found or has knowledge points.
    """
    chapter = db._chapters.get(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在",
        )
    
    # Check if chapter has knowledge points
    kp_count = sum(
        1 for kp in db._knowledge_points.values()
        if kp.chapter_id == chapter_id
    )
    
    if kp_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该章节下有 {kp_count} 个知识点，请先删除知识点",
        )
    
    # Delete chapter
    del db._chapters[chapter_id]
    
    return APIResponse(
        success=True,
        message="章节删除成功",
    )
