"""Chapter API schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.course import Edition, Subject, CourseStatus


class ChapterCreate(BaseModel):
    """Chapter creation request."""

    name: str = Field(..., min_length=1, max_length=100, description="章节名称")
    grade: str = Field(..., description="年级")
    edition: Edition = Field(..., description="教材版本")
    subject: Subject = Field(..., description="科目")
    description: Optional[str] = Field(None, description="章节描述")
    estimated_hours: Optional[float] = Field(None, ge=0, description="预估学习时长")
    level_descriptions: dict[int, str] = Field(default_factory=dict, description="层级描述")
    sort_order: int = Field(default=0, description="排序权重")

    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v: str) -> str:
        valid_grades = ['初一', '初二', '初三', '高一', '高二', '高三']
        if v not in valid_grades:
            raise ValueError(f'年级必须是: {", ".join(valid_grades)}')
        return v

    @field_validator('level_descriptions')
    @classmethod
    def validate_level_descriptions(cls, v: dict[int, str]) -> dict[int, str]:
        for level in v.keys():
            if not 0 <= level <= 6:
                raise ValueError('层级必须在 0-6 之间')
        return v


class ChapterUpdate(BaseModel):
    """Chapter update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    level_descriptions: Optional[dict[int, str]] = None
    sort_order: Optional[int] = None
    status: Optional[CourseStatus] = None

    @field_validator('level_descriptions')
    @classmethod
    def validate_level_descriptions(cls, v: Optional[dict[int, str]]) -> Optional[dict[int, str]]:
        if v is not None:
            for level in v.keys():
                if not 0 <= level <= 6:
                    raise ValueError('层级必须在 0-6 之间')
        return v


class ChapterResponse(BaseModel):
    """Chapter response."""

    id: str
    name: str
    grade: str
    edition: Edition
    subject: Subject
    description: Optional[str] = None
    sort_order: int = 0
    total_knowledge_points: int = 0
    estimated_hours: Optional[float] = None
    level_descriptions: dict[int, str] = Field(default_factory=dict)
    status: CourseStatus = CourseStatus.ACTIVE
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_domain(cls, chapter) -> "ChapterResponse":
        """Create from domain model."""
        return cls(
            id=chapter.id,
            name=chapter.name,
            grade=chapter.grade,
            edition=chapter.edition,
            subject=chapter.subject,
            description=chapter.description,
            sort_order=chapter.sort_order,
            total_knowledge_points=chapter.total_knowledge_points,
            estimated_hours=chapter.estimated_hours,
            level_descriptions=chapter.level_descriptions,
            status=chapter.status,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
        )


class ChapterListResponse(BaseModel):
    """Chapter list response with filters."""

    chapters: list[ChapterResponse]
    total: int
    grade: Optional[str] = None
    edition: Optional[Edition] = None
    subject: Optional[Subject] = None
