"""Student-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class StudentCreate(BaseModel):
    """Schema for student registration."""

    name: str = Field(..., min_length=2, max_length=50, description="学生姓名")
    grade: str = Field(..., description="年级")
    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
    password: str = Field(..., min_length=6, max_length=50, description="密码")

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: str) -> str:
        valid_grades = ["初一", "初二", "初三", "高一", "高二", "高三"]
        if v not in valid_grades:
            raise ValueError(f"年级必须是: {', '.join(valid_grades)}")
        return v


class StudentLogin(BaseModel):
    """Schema for student login."""

    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")


class StudentResponse(BaseModel):
    """Schema for student response."""

    id: int
    name: str
    grade: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_domain(cls, student: Any) -> "StudentResponse":
        """Create response from domain model."""
        return cls(
            id=student.id,
            name=student.name,
            grade=student.grade.value if hasattr(student.grade, 'value') else str(student.grade),
            phone=student.phone,
            avatar_url=student.avatar_url,
            status=student.status.value if hasattr(student.status, 'value') else str(student.status),
            created_at=student.created_at,
        )


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
    student_id: int
    student_name: str


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: int  # student_id
    exp: datetime
