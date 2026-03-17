"""Learning API routes."""

import json
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.core.security import get_current_student_id
from app.schemas.learning import (
    StartSessionRequest,
    SessionResponse,
    ChatRequest,
    ChatResponse,
    AssessmentRequest,
    AssessmentResponse,
    ProgressResponse,
    SkipRequest,
)
from app.schemas.common import APIResponse
from app.services.learning_service import learning_service
from app.services.student_service import student_service
from app.services.backtrack_service import backtrack_service

router = APIRouter()


@router.post("/start", response_model=APIResponse[SessionResponse])
async def start_session(
    request: StartSessionRequest,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[SessionResponse]:
    """Start a new learning session.

    Args:
        request: Session start request.
        student_id: Authenticated student ID.

    Returns:
        API response with session data.
    """
    session = learning_service.start_session(
        student_id=student_id,
        course_id=request.course_id,
        kp_id=request.kp_id,
    )

    return APIResponse(
        success=True,
        data=SessionResponse(
            session_id=session.id,
            course_id=session.course_id,
            kp_id=session.kp_id,
            status=session.status.value,
        ),
        message="学习会话已创建",
    )


@router.get("/session/{session_id}", response_model=APIResponse[SessionResponse])
async def get_session(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[SessionResponse]:
    """Get a learning session by ID.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with session data.
    """
    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    return APIResponse(
        success=True,
        data=SessionResponse(
            session_id=session.id,
            course_id=session.course_id,
            kp_id=session.kp_id,
            status=session.status.value,
        ),
    )


@router.post("/session/{session_id}/teach", response_model=APIResponse[ChatResponse])
async def get_teaching_content(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[ChatResponse]:
    """Get teaching content for current knowledge point.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with teaching content.
    """
    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    student = student_service.get_by_id(student_id)
    content = learning_service.generate_teaching_content(session, student.name)

    return APIResponse(
        success=True,
        data=ChatResponse(
            response_type=content.get("response_type", "讲解"),
            content=content.get("content", {}),
            whiteboard=content.get("whiteboard", {}),
            next_action=content.get("next_action", "wait_for_student"),
        ),
    )


@router.post("/session/{session_id}/teach/stream")
async def get_teaching_content_stream(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> EventSourceResponse:
    """Get teaching content for current knowledge point as a stream.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        SSE stream with teaching content.
    """
    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    student = student_service.get_by_id(student_id)

    async def event_generator():
        async for event in learning_service.stream_teaching_content(session, student.name):
            yield event

    return EventSourceResponse(event_generator())


@router.post("/session/{session_id}/chat", response_model=APIResponse[ChatResponse])
async def send_message(
    session_id: str,
    request: ChatRequest,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[ChatResponse]:
    """Send a message in the learning session.

    Args:
        session_id: Session ID.
        request: Chat request.
        student_id: Authenticated student ID.

    Returns:
        API response with AI response.
    """
    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    response = learning_service.process_student_message(session, request.message)

    return APIResponse(
        success=True,
        data=ChatResponse(
            response_type=response.get("response_type", "反馈"),
            content=response.get("content", {}),
            whiteboard=response.get("whiteboard", {}),
            next_action=response.get("next_action", "wait_for_student"),
        ),
    )


@router.post("/session/{session_id}/chat/stream")
async def send_message_stream(
    session_id: str,
    request: ChatRequest,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> EventSourceResponse:
    """Send a message in the learning session and get streaming response.

    Args:
        session_id: Session ID.
        request: Chat request.
        student_id: Authenticated student ID.

    Returns:
        SSE stream with AI response.
    """
    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    async def event_generator():
        async for event in learning_service.stream_chat_response(session, request.message):
            yield event

    return EventSourceResponse(event_generator())


@router.get(
    "/session/{session_id}/assessment",
    response_model=APIResponse[dict[str, Any]]
)
async def get_assessment_questions(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[dict[str, Any]]:
    """Get assessment questions for current knowledge point.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with assessment questions.
    """
    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    if not session.kp_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="会话没有当前知识点",
        )

    questions = learning_service.get_assessment_questions(session.kp_id)

    return APIResponse(
        success=True,
        data={
            "kp_id": session.kp_id,
            "questions": [
                {
                    "id": q.id,
                    "type": q.type.value,
                    "content": q.content,
                    "options": q.options,
                    "difficulty": q.difficulty.value if q.difficulty else "基础",
                }
                for q in questions
            ],
        },
    )


@router.post(
    "/session/{session_id}/assessment",
    response_model=APIResponse[AssessmentResponse]
)
async def submit_assessment(
    session_id: str,
    request: AssessmentRequest,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[AssessmentResponse]:
    """Submit assessment answers.

    Args:
        session_id: Session ID.
        request: Assessment request with answers.
        student_id: Authenticated student ID.

    Returns:
        API response with assessment result.
    """
    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    result = learning_service.submit_assessment(session, request.answers)

    return APIResponse(
        success=True,
        data=AssessmentResponse(
            result=result["result"],
            score=result["score"],
            correct_count=result["correct_count"],
            total_questions=result["total_questions"],
            passed=result["passed"],
            next_kp_id=result.get("next_kp_id"),
            next_kp_name=result.get("next_kp_name"),
            backtrack_required=result.get("backtrack_required", False),
        ),
    )


@router.post(
    "/session/{session_id}/skip",
    response_model=APIResponse[dict[str, Any]]
)
async def skip_knowledge_point(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)],
    request: Optional[SkipRequest] = None,
) -> APIResponse[dict[str, Any]]:
    """Skip the current knowledge point.

    Args:
        session_id: Session ID.
        request: Optional skip request with reason.
        student_id: Authenticated student ID.

    Returns:
        API response with next knowledge point info.
    """
    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    reason = request.reason if request else None
    result = learning_service.skip_knowledge_point(session, reason)

    return APIResponse(
        success=True,
        data=result,
        message="知识点已跳过",
    )


@router.post(
    "/session/{session_id}/complete",
    response_model=APIResponse[dict[str, Any]]
)
async def complete_knowledge_point(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[dict[str, Any]]:
    """Mark current knowledge point as mastered (for concept-type KPs without assessment).

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with next knowledge point info.
    """
    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    result = learning_service.complete_knowledge_point(session)

    return APIResponse(
        success=True,
        data=result,
        message="知识点已完成",
    )


@router.post(
    "/session/{session_id}/backtrack",
    response_model=APIResponse[dict[str, Any]]
)
async def backtrack(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[dict[str, Any]]:
    """Trigger backtrack decision for current knowledge point.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with backtrack decision and content.
    """
    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    if not session.kp_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="会话没有当前知识点",
        )

    # Get the last failed attempt
    record = learning_service.get_or_create_record(student_id, session.kp_id)

    if not record.attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有失败记录，无法回溯",
        )

    last_attempt = record.attempts[-1]
    if last_attempt.result == "passed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="最近一次已通过，无需回溯",
        )

    # Analyze and decide
    decision = backtrack_service.analyze_and_decide(
        student_id=student_id,
        current_kp_id=session.kp_id,
        error_type=last_attempt.error_type or "概念混淆",
        student_response="",
        error_count=record.attempt_count,
    )

    # Generate remedial content if backtrack
    if decision["decision"] == "backtrack" and "backtrack_target" in decision:
        student = student_service.get_by_id(student_id)
        content = backtrack_service.generate_remedial_content(
            backtrack_kp_id=decision["backtrack_target"]["knowledge_point_id"],
            current_kp_name=decision["backtrack_target"]["knowledge_point_name"],
            error_analysis=decision.get("error_root_cause", ""),
            student_name=student.name,
        )
        decision["remedial_content"] = content

    return APIResponse(
        success=True,
        data=decision,
    )


@router.get("/progress/{course_id}", response_model=APIResponse[ProgressResponse])
async def get_progress(
    course_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[ProgressResponse]:
    """Get learning progress for a course.

    Args:
        course_id: Course ID.
        student_id: Authenticated student ID.

    Returns:
        API response with progress data.
    """
    progress = learning_service.get_progress(student_id, course_id)

    return APIResponse(
        success=True,
        data=ProgressResponse(**progress),
    )
