"""Diagnostic API routes for pre-class assessment."""

from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_student_id
from app.schemas.diagnostic import (
    StartDiagnosticRequest,
    DiagnosticSessionResponse,
    DiagnosticQuestionResponse,
    DiagnosticAnswerRequest,
    DiagnosticAnswerResponse,
    DiagnosticResultResponse,
    PrerequisiteCheckResponse,
)
from app.schemas.common import APIResponse
from app.services.diagnostic_service import diagnostic_service
from app.models.diagnostic import DiagnosticStatus

router = APIRouter()


@router.post("/start", response_model=APIResponse[DiagnosticSessionResponse])
async def start_diagnostic(
    request: StartDiagnosticRequest,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[DiagnosticSessionResponse]:
    """Start a new diagnostic session.

    Creates a diagnostic session with questions to assess the student's
    prior knowledge before starting to learn a new knowledge point.

    Args:
        request: Diagnostic start request with course_id and target_kp_id.
        student_id: Authenticated student ID.

    Returns:
        API response with session data and first question.
    """
    session = diagnostic_service.create_diagnostic_session(
        student_id=student_id,
        course_id=request.course_id,
        target_kp_id=request.target_kp_id,
    )

    # Start the session
    current_question = session.get_current_question()

    return APIResponse(
        success=True,
        data=DiagnosticSessionResponse(
            session_id=session.id,
            course_id=session.course_id,
            target_kp_id=session.target_kp_id,
            status=session.status.value,
            progress=session.get_progress(),
            current_question=_format_question(current_question) if current_question else None,
        ),
        message="诊断会话已创建",
    )


@router.get(
    "/session/{session_id}",
    response_model=APIResponse[DiagnosticSessionResponse]
)
async def get_diagnostic_session(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[DiagnosticSessionResponse]:
    """Get a diagnostic session by ID.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with session data.
    """
    session = diagnostic_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此诊断会话",
        )

    current_question = session.get_current_question()

    return APIResponse(
        success=True,
        data=DiagnosticSessionResponse(
            session_id=session.id,
            course_id=session.course_id,
            target_kp_id=session.target_kp_id,
            status=session.status.value,
            progress=session.get_progress(),
            current_question=_format_question(current_question) if current_question else None,
        ),
    )


@router.get(
    "/session/{session_id}/question",
    response_model=APIResponse[DiagnosticQuestionResponse]
)
async def get_current_question(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[DiagnosticQuestionResponse]:
    """Get the current question for a diagnostic session.

    Returns the next unanswered question in the session.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with current question.
    """
    session = diagnostic_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此诊断会话",
        )

    question = session.get_current_question()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="所有题目已答完，请完成诊断",
        )

    return APIResponse(
        success=True,
        data=_format_question(question),
    )


@router.post(
    "/session/{session_id}/answer",
    response_model=APIResponse[DiagnosticAnswerResponse]
)
async def submit_answer(
    session_id: str,
    request: DiagnosticAnswerRequest,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[DiagnosticAnswerResponse]:
    """Submit an answer to a diagnostic question.

    Args:
        session_id: Session ID.
        request: Answer request with question_id and answer.
        student_id: Authenticated student ID.

    Returns:
        API response with answer result and next question.
    """
    session = diagnostic_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此诊断会话",
        )

    result = diagnostic_service.process_answer(
        session_id=session_id,
        question_id=request.question_id,
        student_answer=request.answer,
        response_time=request.response_time,
    )

    return APIResponse(
        success=True,
        data=DiagnosticAnswerResponse(
            is_correct=result["is_correct"],
            explanation=result["explanation"],
            progress=result["progress"],
            next_question=_format_question(result["next_question"]) if result["next_question"] else None,
            session_completed=result["session_completed"],
        ),
    )


@router.post(
    "/session/{session_id}/complete",
    response_model=APIResponse[DiagnosticResultResponse]
)
async def complete_diagnostic(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[DiagnosticResultResponse]:
    """Complete the diagnostic session and get results.

    Generates a comprehensive diagnostic result with conclusions
    and learning recommendations.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with diagnostic result.
    """
    session = diagnostic_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此诊断会话",
        )

    result = diagnostic_service.complete_diagnosis(session_id)

    return APIResponse(
        success=True,
        data=DiagnosticResultResponse(
            session_id=result.session_id,
            target_kp_id=result.target_kp_id,
            target_kp_name=result.target_kp_name,
            conclusion=result.conclusion.value,
            prerequisite_results=[
                PrerequisiteCheckResponse(**r.to_dict())
                for r in result.prerequisite_results
            ],
            target_questions_total=result.target_questions_total,
            target_questions_correct=result.target_questions_correct,
            total_questions=result.total_questions,
            total_correct=result.total_correct,
            correct_rate=result.correct_rate,
            recommended_starting_point=result.recommended_starting_point,
            recommended_teaching_mode=result.recommended_teaching_mode,
            summary=result.summary,
            created_at=result.created_at,
        ),
        message="诊断已完成",
    )


@router.get(
    "/session/{session_id}/result",
    response_model=APIResponse[DiagnosticResultResponse]
)
async def get_diagnostic_result(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[DiagnosticResultResponse]:
    """Get the result of a completed diagnostic session.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with diagnostic result.
    """
    session = diagnostic_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此诊断会话",
        )

    if session.status != DiagnosticStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="诊断会话尚未完成",
        )

    result = diagnostic_service.get_result(session_id)

    return APIResponse(
        success=True,
        data=DiagnosticResultResponse(
            session_id=result.session_id,
            target_kp_id=result.target_kp_id,
            target_kp_name=result.target_kp_name,
            conclusion=result.conclusion.value,
            prerequisite_results=[
                PrerequisiteCheckResponse(**r.to_dict())
                for r in result.prerequisite_results
            ],
            target_questions_total=result.target_questions_total,
            target_questions_correct=result.target_questions_correct,
            total_questions=result.total_questions,
            total_correct=result.total_correct,
            correct_rate=result.correct_rate,
            recommended_starting_point=result.recommended_starting_point,
            recommended_teaching_mode=result.recommended_teaching_mode,
            summary=result.summary,
            created_at=result.created_at,
        ),
    )


@router.get(
    "/session/{session_id}/progress",
    response_model=APIResponse[dict[str, Any]]
)
async def get_diagnostic_progress(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)]
) -> APIResponse[dict[str, Any]]:
    """Get the progress of a diagnostic session.

    Args:
        session_id: Session ID.
        student_id: Authenticated student ID.

    Returns:
        API response with progress info.
    """
    session = diagnostic_service.get_session(session_id)

    if session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此诊断会话",
        )

    return APIResponse(
        success=True,
        data={
            "session_id": session_id,
            "status": session.status.value,
            **session.get_progress(),
        },
    )


def _format_question(question: Any) -> DiagnosticQuestionResponse:
    """Format a diagnostic question for API response.

    Args:
        question: DiagnosticQuestion instance.

    Returns:
        DiagnosticQuestionResponse.
    """
    return DiagnosticQuestionResponse(
        id=question.id,
        session_id=question.session_id,
        kp_id=question.kp_id,
        category=question.category.value,
        question_type=question.question_type.value,
        content=question.content,
        options=question.options,
        image_url=question.image_url,
        coordinate_range=question.coordinate_range,
        order=question.order,
    )
