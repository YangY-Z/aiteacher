"""DTO schemas for Grade and Subject APIs."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import GradeLevel, Status, SubjectCategory


# ============ GradeSubject Schemas ============


class GradeSubjectCreate(BaseModel):
    """Request schema for adding a subject to a grade."""

    subject_id: str = Field(..., description="科目ID")
    sort_order: int = Field(default=0, description="排序序号")


class GradeSubjectResponse(BaseModel):
    """Response schema for grade-subject association."""

    id: str
    grade_id: str
    subject_id: str
    sort_order: int
    status: Status
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Grade Schemas ============


class GradeCreate(BaseModel):
    """Request schema for creating a grade."""

    name: str = Field(..., min_length=1, max_length=50, description="年级名称")
    code: str = Field(..., min_length=1, max_length=10, description="年级代码")
    level: GradeLevel = Field(..., description="学段")
    sort_order: int = Field(default=0, description="排序序号")
    description: Optional[str] = Field(None, description="描述")


class GradeUpdate(BaseModel):
    """Request schema for updating a grade."""

    name: Optional[str] = Field(None, min_length=1, max_length=50, description="年级名称")
    level: Optional[GradeLevel] = Field(None, description="学段")
    sort_order: Optional[int] = Field(None, description="排序序号")
    description: Optional[str] = Field(None, description="描述")
    status: Optional[Status] = Field(None, description="状态")


class GradeResponse(BaseModel):
    """Response schema for a grade."""

    id: str
    name: str
    code: str
    level: GradeLevel
    subjects: list[GradeSubjectResponse] = Field(default_factory=list)
    sort_order: int
    description: Optional[str]
    status: Status
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_domain(cls, grade) -> "GradeResponse":
        """Create from domain model.

        Args:
            grade: Grade domain model instance.

        Returns:
            GradeResponse instance.
        """
        subjects = [
            GradeSubjectResponse(
                id=s.id,
                grade_id=s.grade_id,
                subject_id=s.subject_id,
                sort_order=s.sort_order,
                status=s.status,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in grade.subjects
        ]

        return cls(
            id=grade.id,
            name=grade.name,
            code=grade.code,
            level=grade.level,
            subjects=subjects,
            sort_order=grade.sort_order,
            description=grade.description,
            status=grade.status,
            created_at=grade.created_at,
            updated_at=grade.updated_at,
        )


class GradeListResponse(BaseModel):
    """Response schema for a list of grades."""

    grades: list[GradeResponse]
    total: int


# ============ Subject Schemas ============


class SubjectCreate(BaseModel):
    """Request schema for creating a subject."""

    name: str = Field(..., min_length=1, max_length=50, description="科目名称")
    code: str = Field(..., min_length=1, max_length=20, description="科目代码")
    category: SubjectCategory = Field(..., description="科目类别")
    icon: Optional[str] = Field(None, description="图标")
    color: Optional[str] = Field(None, description="主题色")
    sort_order: int = Field(default=0, description="排序序号")
    description: Optional[str] = Field(None, description="描述")


class SubjectUpdate(BaseModel):
    """Request schema for updating a subject."""

    name: Optional[str] = Field(None, min_length=1, max_length=50, description="科目名称")
    category: Optional[SubjectCategory] = Field(None, description="科目类别")
    icon: Optional[str] = Field(None, description="图标")
    color: Optional[str] = Field(None, description="主题色")
    sort_order: Optional[int] = Field(None, description="排序序号")
    description: Optional[str] = Field(None, description="描述")
    status: Optional[Status] = Field(None, description="状态")


class SubjectResponse(BaseModel):
    """Response schema for a subject."""

    id: str
    name: str
    code: str
    category: SubjectCategory
    icon: Optional[str]
    color: Optional[str]
    sort_order: int
    description: Optional[str]
    status: Status
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_domain(cls, subject) -> "SubjectResponse":
        """Create from domain model.

        Args:
            subject: Subject domain model instance.

        Returns:
            SubjectResponse instance.
        """
        return cls(
            id=subject.id,
            name=subject.name,
            code=subject.code,
            category=subject.category,
            icon=subject.icon,
            color=subject.color,
            sort_order=subject.sort_order,
            description=subject.description,
            status=subject.status,
            created_at=subject.created_at,
            updated_at=subject.updated_at,
        )


class SubjectListResponse(BaseModel):
    """Response schema for a list of subjects."""

    subjects: list[SubjectResponse]
    total: int
