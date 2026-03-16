"""Student API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_student_id
from app.schemas.student import StudentResponse
from app.schemas.common import APIResponse
from app.services.student_service import student_service

router = APIRouter()


@router.get("/me", response_model=APIResponse[StudentResponse])
async def get_current_student(
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[StudentResponse]:
    """Get the current authenticated student.

    Args:
        student_id: Authenticated student ID.

    Returns:
        API response with student data.
    """
    student = student_service.get_by_id(student_id)
    return APIResponse(
        success=True,
        data=StudentResponse.from_domain(student),
    )


@router.get("/{student_id}", response_model=APIResponse[StudentResponse])
async def get_student(
    student_id: int,
    current_student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[StudentResponse]:
    """Get a student by ID.

    Args:
        student_id: Student ID to retrieve.
        current_student_id: Authenticated student ID.

    Returns:
        API response with student data.
    """
    if student_id != current_student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问其他学生信息",
        )

    student = student_service.get_by_id(student_id)
    return APIResponse(
        success=True,
        data=StudentResponse.from_domain(student),
    )
