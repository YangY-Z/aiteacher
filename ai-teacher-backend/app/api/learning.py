"""Learning API routes."""

import json
import logging
import uuid
from typing import Annotated, Any, Optional

from datetime import datetime
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
    SessionListItem,
    SessionHistoryResponse,
    SessionHistoryRound,
    RoundMessage,
)
from app.schemas.common import APIResponse
from app.services.learning_service import learning_service
from app.services.student_service import student_service
from app.services.backtrack_service import backtrack_service
from app.repositories.learning_repository import learning_session_repository
from app.repositories.memory_db import db

router = APIRouter()
logger = logging.getLogger(__name__)


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


@router.post("/session/{session_id}/stream")
async def unified_stream(
    session_id: str,
    request: Optional[ChatRequest] = None,
    start_new: bool = False,  # 是否开始新的学习轮次
    student_id: Annotated[int, Depends(get_current_student_id)] = None
) -> EventSourceResponse:
    """Unified streaming endpoint for teaching and chat.

    - If is_first_input=True: Teaching mode (start teaching)
    - If request has message and not first input: Chat mode (subsequent rounds)
    - If start_new=True: Start a new learning round (clear history, increment round)

    Args:
        session_id: Session ID.
        request: Optional chat request with message.
        start_new: Whether to start a new learning round.
        student_id: Authenticated student ID.

    Returns:
        SSE stream with teaching content or chat response.
    """
    trace_id = f"stream-{uuid.uuid4().hex[:12]}"
    message = request.message if request else ""
    is_first_input = request.is_first_input if request else False

    logger.info(f"[{trace_id}] ========== 流式请求开始 ==========")
    logger.info(f"[{trace_id}] session_id={session_id}, student_id={student_id}, has_message={bool(message)}, is_first_input={is_first_input}, start_new={start_new}")

    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        logger.warning(f"[{trace_id}] 权限校验失败")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    student = student_service.get_by_id(student_id)
    logger.info(f"[{trace_id}] 学生: {student.name}")

    # 如果请求开始新的学习轮次，重置会话状态
    if start_new:
        session.start_new_round()
        learning_session_repository.update(session)
        logger.info(f"[{trace_id}] 开始新的学习轮次: round={session.learning_round}")

    async def event_generator():
        event_count = 0
        try:
            async for event in learning_service.stream_unified_response(
                session=session,
                student_name=student.name,
                message=message,
                trace_id=trace_id,
                is_first_input=is_first_input,
            ):
                event_count += 1
                yield event
            logger.info(f"[{trace_id}] ========== 流式请求完成, 共{event_count}个事件 ==========")
        except Exception as e:
            logger.error(f"[{trace_id}] 流式生成失败: {e}", exc_info=True)
            yield {"event": "error", "data": json.dumps({"error": str(e)}, ensure_ascii=False)}

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
            question_results=result.get("question_results"),
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


@router.post("/session/{session_id}/phase/next")
async def advance_teaching_phase(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[dict[str, Any]]:
    """Advance to the next teaching phase.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with new phase info.
    """
    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    # Advance to next phase
    new_phase = session.advance_phase()
    learning_session_repository.update(session)

    # Get total phase count for this teaching mode
    from app.models.teaching_mode import TeachingModeType, TEACHING_MODE_CONFIGS
    total_phases = 4  # default
    if session.teaching_mode:
        try:
            mode_type = TeachingModeType(session.teaching_mode)
            mode_config = TEACHING_MODE_CONFIGS.get(mode_type)
            if mode_config:
                total_phases = len(mode_config.phases)
        except ValueError:
            pass

    return APIResponse(
        success=True,
        data={
            "current_phase": new_phase,
            "total_phases": total_phases,
            "is_last_phase": new_phase >= total_phases,
        },
        message=f"已进入第{new_phase}阶段",
    )


@router.get("/session/{session_id}/phase")
async def get_current_phase(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[dict[str, Any]]:
    """Get current teaching phase info.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with phase info.
    """
    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    # Get phase info
    from app.models.teaching_mode import TeachingModeType, TEACHING_MODE_CONFIGS
    
    current_phase = session.current_phase or 1
    phase_info = {}
    total_phases = 4

    if session.teaching_mode:
        try:
            mode_type = TeachingModeType(session.teaching_mode)
            mode_config = TEACHING_MODE_CONFIGS.get(mode_type)
            if mode_config:
                total_phases = len(mode_config.phases)
                for phase in mode_config.phases:
                    if phase.order == current_phase:
                        phase_info = {
                            "name": phase.name,
                            "description": phase.description,
                            "activities": phase.activities,
                        }
                        break
        except ValueError:
            pass

    return APIResponse(
        success=True,
        data={
            "teaching_mode": session.teaching_mode,
            "current_phase": current_phase,
            "total_phases": total_phases,
            "phase_status": session.phase_status,
            "phase_info": phase_info,
        },
    )


@router.get("/sessions", response_model=APIResponse[list[SessionListItem]])
async def list_sessions(
    course_id: Optional[str] = None,
    kp_id: Optional[str] = None,
    student_id: Annotated[int, Depends(get_current_student_id)] = None
) -> APIResponse[list[SessionListItem]]:
    """Get all learning sessions for the current student.

    Args:
        course_id: Optional course ID filter.
        kp_id: Optional knowledge point ID filter.
        student_id: Authenticated student ID.

    Returns:
        API response with list of sessions.
    """
    sessions = learning_session_repository.get_by_student(student_id)

    # Filter by course_id if provided
    if course_id:
        sessions = [s for s in sessions if s.course_id == course_id]

    # Filter by kp_id if provided
    if kp_id:
        sessions = [s for s in sessions if s.kp_id == kp_id]

    # Get KP name lookup
    kp_names: dict[str, str] = {}
    for kp in db._knowledge_points.values():
        kp_names[kp.id] = kp.name

    # Sort by created_at descending (most recent first)
    sessions.sort(key=lambda s: s.created_at or datetime.min, reverse=True)

    session_list = []
    for session in sessions:
        total_messages = sum(len(r.messages) for r in session.rounds)
        session_list.append(SessionListItem(
            session_id=session.id,
            course_id=session.course_id,
            kp_id=session.kp_id,
            kp_name=kp_names.get(session.kp_id) if session.kp_id else None,
            status=session.status.value,
            current_round=session.learning_round,
            rounds_count=len(session.rounds),
            total_messages=total_messages,
            created_at=session.created_at.isoformat() if session.created_at else None,
        ))

    return APIResponse(
        success=True,
        data=session_list,
    )


@router.get("/session/{session_id}/history", response_model=APIResponse[SessionHistoryResponse])
async def get_session_history(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[SessionHistoryResponse]:
    """Get full conversation history for a learning session.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with full session history including all rounds and messages.
    """
    session = learning_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    # Get KP name lookup
    kp_names: dict[str, str] = {}
    for kp in db._knowledge_points.values():
        kp_names[kp.id] = kp.name

    # Build rounds detail
    rounds_detail = []
    for round_data in session.rounds:
        messages = [
            RoundMessage(role=m.get("role", "assistant"), content=m.get("content", ""))
            for m in round_data.messages
        ]
        rounds_detail.append(SessionHistoryRound(
            round_number=round_data.round_number,
            status=round_data.status.value if isinstance(round_data.status, type(round_data.status)) else str(round_data.status),
            start_time=round_data.start_time.isoformat() if round_data.start_time else None,
            end_time=round_data.end_time.isoformat() if round_data.end_time else None,
            messages=messages,
            teaching_mode=round_data.teaching_mode,
            assessment_result=round_data.assessment_result.to_dict() if round_data.assessment_result else None,
            summary=round_data.summary.to_dict() if round_data.summary else None,
        ))

    return APIResponse(
        success=True,
        data=SessionHistoryResponse(
            session_id=session.id,
            course_id=session.course_id,
            kp_id=session.kp_id,
            kp_name=kp_names.get(session.kp_id) if session.kp_id else None,
            status=session.status.value,
            created_at=session.created_at.isoformat() if session.created_at else None,
            current_round_index=session.current_round_index,
            rounds=rounds_detail,
        ),
    )
