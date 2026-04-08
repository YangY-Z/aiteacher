"""Admin API endpoints for grade and subject management."""

from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.models import GradeLevel, Status, SubjectCategory
from app.schemas.grade import (
    GradeCreate,
    GradeUpdate,
    GradeResponse,
    GradeListResponse,
    GradeSubjectCreate,
    GradeSubjectResponse,
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    SubjectListResponse,
)
from app.services.grade_service import grade_service
from app.services.subject_service import subject_service
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError, ValidationError

router = APIRouter(prefix="/admin", tags=["admin"])


# ============ Grade Management ============


@router.get("/grades", response_model=GradeListResponse)
async def get_grades(
    level: Optional[GradeLevel] = None,
    active_only: bool = False,
) -> GradeListResponse:
    """Get all grades.

    Args:
        level: Filter by grade level (optional).
        active_only: Only return active grades.

    Returns:
        List of grades.
    """
    grades = grade_service.get_all_grades(level=level, active_only=active_only)
    grade_responses = [GradeResponse.from_domain(g) for g in grades]
    return GradeListResponse(grades=grade_responses, total=len(grade_responses))


@router.post(
    "/grades",
    response_model=GradeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_grade(request: GradeCreate) -> GradeResponse:
    """Create a new grade.

    Args:
        request: Grade creation request.

    Returns:
        The created grade.

    Raises:
        HTTPException: 409 if grade already exists.
    """
    try:
        grade = grade_service.create_grade(
            name=request.name,
            code=request.code,
            level=request.level,
            sort_order=request.sort_order,
            description=request.description,
        )
        return GradeResponse.from_domain(grade)
    except DuplicateEntityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.get("/grades/{grade_id}", response_model=GradeResponse)
async def get_grade(grade_id: str) -> GradeResponse:
    """Get a grade by ID.

    Args:
        grade_id: Grade ID.

    Returns:
        The grade.

    Raises:
        HTTPException: 404 if grade not found.
    """
    try:
        grade = grade_service.get_grade(grade_id)
        return GradeResponse.from_domain(grade)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.put("/grades/{grade_id}", response_model=GradeResponse)
async def update_grade(grade_id: str, request: GradeUpdate) -> GradeResponse:
    """Update a grade.

    Args:
        grade_id: Grade ID.
        request: Grade update request.

    Returns:
        The updated grade.

    Raises:
        HTTPException: 404 if grade not found, 409 if name conflict.
    """
    try:
        grade = grade_service.update_grade(
            grade_id=grade_id,
            name=request.name,
            level=request.level,
            sort_order=request.sort_order,
            description=request.description,
            status=request.status,
        )
        return GradeResponse.from_domain(grade)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except DuplicateEntityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.delete(
    "/grades/{grade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_grade(grade_id: str) -> None:
    """Delete a grade.

    Args:
        grade_id: Grade ID.

    Raises:
        HTTPException: 404 if grade not found, 400 if grade has chapters.
    """
    try:
        grade_service.delete_grade(grade_id)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get("/grades/{grade_id}/subjects", response_model=list[GradeSubjectResponse])
async def get_grade_subjects(grade_id: str) -> list[GradeSubjectResponse]:
    """Get all subjects in a grade.

    Args:
        grade_id: Grade ID.

    Returns:
        List of grade-subject associations.

    Raises:
        HTTPException: 404 if grade not found.
    """
    try:
        subjects = grade_service.get_grade_subjects(grade_id)
        return [
            GradeSubjectResponse(
                id=s.id,
                grade_id=s.grade_id,
                subject_id=s.subject_id,
                sort_order=s.sort_order,
                status=s.status,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in subjects
        ]
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.post(
    "/grades/{grade_id}/subjects",
    response_model=GradeSubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_subject_to_grade(grade_id: str, request: GradeSubjectCreate) -> GradeSubjectResponse:
    """Add a subject to a grade.

    Args:
        grade_id: Grade ID.
        request: Subject addition request.

    Returns:
        The created association.

    Raises:
        HTTPException: 404 if grade or subject not found, 400 if already added.
    """
    try:
        association = grade_service.add_subject_to_grade(
            grade_id=grade_id,
            subject_id=request.subject_id,
            sort_order=request.sort_order,
        )
        return GradeSubjectResponse(
            id=association.id,
            grade_id=association.grade_id,
            subject_id=association.subject_id,
            sort_order=association.sort_order,
            status=association.status,
            created_at=association.created_at,
            updated_at=association.updated_at,
        )
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.delete(
    "/grades/{grade_id}/subjects/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_subject_from_grade(grade_id: str, subject_id: str) -> None:
    """Remove a subject from a grade.

    Args:
        grade_id: Grade ID.
        subject_id: Subject ID.

    Raises:
        HTTPException: 404 if grade not found, 400 if subject has chapters.
    """
    try:
        grade_service.remove_subject_from_grade(grade_id, subject_id)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


# ============ Subject Management ============


@router.get("/subjects", response_model=SubjectListResponse)
async def get_subjects(
    category: Optional[SubjectCategory] = None,
    active_only: bool = False,
) -> SubjectListResponse:
    """Get all subjects.

    Args:
        category: Filter by subject category (optional).
        active_only: Only return active subjects.

    Returns:
        List of subjects.
    """
    subjects = subject_service.get_all_subjects(category=category, active_only=active_only)
    subject_responses = [SubjectResponse.from_domain(s) for s in subjects]
    return SubjectListResponse(subjects=subject_responses, total=len(subject_responses))


@router.post(
    "/subjects",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subject(request: SubjectCreate) -> SubjectResponse:
    """Create a new subject.

    Args:
        request: Subject creation request.

    Returns:
        The created subject.

    Raises:
        HTTPException: 409 if subject already exists.
    """
    try:
        subject = subject_service.create_subject(
            name=request.name,
            code=request.code,
            category=request.category,
            icon=request.icon,
            color=request.color,
            sort_order=request.sort_order,
            description=request.description,
        )
        return SubjectResponse.from_domain(subject)
    except DuplicateEntityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.get("/subjects/{subject_id}", response_model=SubjectResponse)
async def get_subject(subject_id: str) -> SubjectResponse:
    """Get a subject by ID.

    Args:
        subject_id: Subject ID.

    Returns:
        The subject.

    Raises:
        HTTPException: 404 if subject not found.
    """
    try:
        subject = subject_service.get_subject(subject_id)
        return SubjectResponse.from_domain(subject)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.put("/subjects/{subject_id}", response_model=SubjectResponse)
async def update_subject(subject_id: str, request: SubjectUpdate) -> SubjectResponse:
    """Update a subject.

    Args:
        subject_id: Subject ID.
        request: Subject update request.

    Returns:
        The updated subject.

    Raises:
        HTTPException: 404 if subject not found, 409 if name conflict.
    """
    try:
        subject = subject_service.update_subject(
            subject_id=subject_id,
            name=request.name,
            category=request.category,
            icon=request.icon,
            color=request.color,
            sort_order=request.sort_order,
            description=request.description,
            status=request.status,
        )
        return SubjectResponse.from_domain(subject)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except DuplicateEntityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.delete(
    "/subjects/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_subject(subject_id: str) -> None:
    """Delete a subject.

    Args:
        subject_id: Subject ID.

    Raises:
        HTTPException: 404 if subject not found, 400 if subject has chapters.
    """
    try:
        subject_service.delete_subject(subject_id)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
