"""Course API routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.security import get_current_student_id
from app.schemas.course import (
    CourseResponse,
    KnowledgePointResponse,
    KnowledgePointDetail,
)
from app.schemas.common import APIResponse
from app.services.course_service import course_service

router = APIRouter()


@router.get("", response_model=APIResponse[list[CourseResponse]])
async def get_courses(
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[list[CourseResponse]]:
    """Get all available courses.

    Args:
        student_id: Authenticated student ID.

    Returns:
        API response with list of courses.
    """
    courses = course_service.get_all_courses()
    course_responses = []
    for course in courses:
        kps = course_service.get_course_knowledge_points(course.id)
        deps_map = {}
        for kp in kps:
            deps_map[kp.id] = course_service.get_knowledge_point_dependencies(kp.id)
        course_responses.append(CourseResponse.from_domain(course, kps, deps_map))
    return APIResponse(
        success=True,
        data=course_responses,
    )


@router.get("/{course_id}", response_model=APIResponse[CourseResponse])
async def get_course(
    course_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[CourseResponse]:
    """Get a course by ID.

    Args:
        course_id: Course ID.
        student_id: Authenticated student ID.

    Returns:
        API response with course data.
    """
    course = course_service.get_course(course_id)
    kps = course_service.get_course_knowledge_points(course_id)
    deps_map = {}
    for kp in kps:
        deps_map[kp.id] = course_service.get_knowledge_point_dependencies(kp.id)
    return APIResponse(
        success=True,
        data=CourseResponse.from_domain(course, kps, deps_map),
    )


@router.get(
    "/{course_id}/knowledge-points",
    response_model=APIResponse[list[KnowledgePointResponse]]
)
async def get_course_knowledge_points(
    course_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[list[KnowledgePointResponse]]:
    """Get all knowledge points for a course.

    Args:
        course_id: Course ID.
        student_id: Authenticated student ID.

    Returns:
        API response with list of knowledge points.
    """
    kps = course_service.get_course_knowledge_points(course_id)
    kp_responses = []
    for kp in kps:
        deps = course_service.get_knowledge_point_dependencies(kp.id)
        kp_responses.append(KnowledgePointResponse.from_domain(kp, deps))
    return APIResponse(
        success=True,
        data=kp_responses,
    )


@router.get(
    "/{course_id}/knowledge-points/{kp_id}",
    response_model=APIResponse[KnowledgePointDetail]
)
async def get_knowledge_point(
    course_id: str,
    kp_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[KnowledgePointDetail]:
    """Get a specific knowledge point with details.

    Args:
        course_id: Course ID.
        kp_id: Knowledge point ID.
        student_id: Authenticated student ID.

    Returns:
        API response with knowledge point details.
    """
    info = course_service.get_knowledge_point_info(kp_id)
    return APIResponse(
        success=True,
        data=KnowledgePointDetail(**info),
    )
