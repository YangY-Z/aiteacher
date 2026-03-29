"""专项提升 API 路由。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_student_id
from app.schemas.common import APIResponse
from app.schemas.improvement import (
    ClarificationAnswerRequest,
    CompleteStepRequest,
    GeneratePlanRequest,
    ImprovementPlanResponse,
    ImprovementSessionResponse,
    PlanStepResponse,
    QuizResponse,
    QuizResultResponse,
    QuizSubmitRequest,
    StartImprovementRequest,
)
from app.services.course_service import course_service
from app.services.improvement_service import ImprovementService, improvement_service
from app.models.improvement import DifficultyLevel, FoundationLevel, ScoreInput
from app.agents.improvement_agent import ImprovementAgent

router = APIRouter()

# 初始化 Agent
improvement_agent = ImprovementAgent(
    improvement_service=improvement_service,
    course_service=course_service,
    llm_service=improvement_service.llm_service,
)


def _build_session_response(service: ImprovementService, session) -> ImprovementSessionResponse:
    diagnosis = None
    if session.diagnosis:
        kp_info = service.course_service.get_knowledge_point_info(session.diagnosis.target_knowledge_point_id)
        diagnosis = {
            "target_knowledge_point_id": session.diagnosis.target_knowledge_point_id,
            "target_kp_name": kp_info["name"],
            "confidence": session.diagnosis.confidence,
            "reason": session.diagnosis.reason,
            "prerequisite_gaps": session.diagnosis.prerequisite_gaps,
        }

    plan = None
    if session.plan:
        target_info = service.course_service.get_knowledge_point_info(session.plan.target_kp_id)
        plan = ImprovementPlanResponse(
            plan_id=session.plan.plan_id,
            target_kp_id=session.plan.target_kp_id,
            target_kp_name=target_info["name"],
            steps=[
                PlanStepResponse(
                    step_order=step.step_order,
                    knowledge_point_id=step.knowledge_point_id,
                    kp_name=service.course_service.get_knowledge_point_info(step.knowledge_point_id)["name"],
                    goal=step.goal,
                    estimated_minutes=step.estimated_minutes,
                    is_completed=step.is_completed,
                )
                for step in session.plan.steps
            ],
            total_estimated_minutes=session.plan.total_estimated_minutes,
        )

    return ImprovementSessionResponse(
        session_id=session.session_id,
        student_id=session.student_id,
        course_id=session.course_id,
        status=session.status.value,
        max_clarification_rounds=session.max_clarification_rounds,
        score_input=session.score_input.to_dict() if session.score_input else None,
        clarification_rounds=[
            {
                "round_number": item.round_number,
                "system_question": item.system_question,
                "student_answer": item.student_answer,
                "created_at": item.created_at,
                "answered_at": item.answered_at,
            }
            for item in session.clarification_rounds
        ],
        diagnosis=diagnosis,
        plan=plan,
        current_step_order=session.current_step_order,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.post("/start", response_model=APIResponse[ImprovementSessionResponse])
async def start_improvement(
    request: StartImprovementRequest,
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[ImprovementSessionResponse]:
    score_input = ScoreInput(
        exam_name=request.score_input.exam_name,
        score=request.score_input.score,
        total_score=request.score_input.total_score,
        error_description=request.score_input.error_description,
        available_time=request.score_input.available_time,
        difficulty=DifficultyLevel(request.score_input.difficulty),
        foundation=FoundationLevel(request.score_input.foundation),
    )
    session = improvement_service.start_session(
        str(student_id),
        request.course_id,
        score_input,
        request.score_input.max_clarification_rounds,
    )
    return APIResponse(success=True, data=_build_session_response(improvement_service, session), message="专项提升会话已创建")


@router.get("/session/{session_id}", response_model=APIResponse[ImprovementSessionResponse])
async def get_improvement_session(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[ImprovementSessionResponse]:
    try:
        session = improvement_service.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if session.student_id != str(student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")

    return APIResponse(success=True, data=_build_session_response(improvement_service, session))


@router.post("/session/{session_id}/clarify", response_model=APIResponse[ImprovementSessionResponse])
async def submit_clarification_answer(
    session_id: str,
    request: ClarificationAnswerRequest,
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[ImprovementSessionResponse]:
    session = improvement_service.get_session(session_id)
    if session.student_id != str(student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")

    try:
        updated = improvement_service.submit_clarification_answer(session_id, request.answer)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return APIResponse(success=True, data=_build_session_response(improvement_service, updated))


@router.post("/session/{session_id}/plan", response_model=APIResponse[ImprovementSessionResponse])
async def generate_plan(
    session_id: str,
    request: GeneratePlanRequest,
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[ImprovementSessionResponse]:
    session = improvement_service.get_session(session_id)
    if session.student_id != str(student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")
    if not request.confirm_diagnosis:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先确认诊断结果")

    try:
        updated = improvement_service.generate_plan(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return APIResponse(success=True, data=_build_session_response(improvement_service, updated), message="学习方案已生成")


@router.post("/session/{session_id}/step/{step_order}/start", response_model=APIResponse[dict])
async def start_plan_step(
    session_id: str,
    step_order: int,
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[dict]:
    session = improvement_service.get_session(session_id)
    if session.student_id != str(student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")

    try:
        data = improvement_service.start_plan_step(session_id, step_order)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return APIResponse(success=True, data=data)


@router.post("/session/{session_id}/step/{step_order}/complete", response_model=APIResponse[ImprovementSessionResponse])
async def complete_plan_step(
    session_id: str,
    step_order: int,
    request: CompleteStepRequest,
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[ImprovementSessionResponse]:
    session = improvement_service.get_session(session_id)
    if session.student_id != str(student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")

    try:
        updated = improvement_service.complete_plan_step(session_id, step_order)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return APIResponse(success=True, data=_build_session_response(improvement_service, updated))


@router.get("/session/{session_id}/quiz", response_model=APIResponse[QuizResponse])
async def get_quiz(
    session_id: str,
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[QuizResponse]:
    session = improvement_service.get_session(session_id)
    if session.student_id != str(student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")

    try:
        quiz = improvement_service.get_quiz(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return APIResponse(success=True, data=QuizResponse(**quiz))


@router.post("/session/{session_id}/quiz", response_model=APIResponse[QuizResultResponse])
async def submit_quiz(
    session_id: str,
    request: QuizSubmitRequest,
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[QuizResultResponse]:
    session = improvement_service.get_session(session_id)
    if session.student_id != str(student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")

    try:
        result = improvement_service.submit_quiz(session_id, request.answers)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return APIResponse(
        success=True,
        data=QuizResultResponse(
            quiz_id=result.quiz_id,
            score=result.score,
            passed=result.passed,
            feedback=result.feedback,
        ),
        message="小测已提交",
    )


@router.post("/agent/run", response_model=APIResponse[ImprovementSessionResponse])
async def run_improvement_agent(
    request: StartImprovementRequest,
    student_id: Annotated[int, Depends(get_current_student_id)],
) -> APIResponse[ImprovementSessionResponse]:
    """运行专项提升 Agent 流程。

    Agent 自主决策诊断、方案生成、教学讲解、评估流程。
    """
    score_input = ScoreInput(
        exam_name=request.score_input.exam_name,
        score=request.score_input.score,
        total_score=request.score_input.total_score,
        error_description=request.score_input.error_description,
        available_time=request.score_input.available_time,
        difficulty=DifficultyLevel(request.score_input.difficulty),
        foundation=FoundationLevel(request.score_input.foundation),
    )

    # 创建初始会话
    session = improvement_service.start_session(
        str(student_id),
        request.course_id,
        score_input,
        request.score_input.max_clarification_rounds,
    )

    try:
        # 运行 Agent
        updated_session = improvement_agent.run(
            session_id=session.session_id,
            student_id=str(student_id),
            course_id=request.course_id,
            score=request.score_input.score,
            total_score=request.score_input.total_score,
            error_description=request.score_input.error_description,
            available_time=request.score_input.available_time,
            difficulty=request.score_input.difficulty,
            foundation=request.score_input.foundation,
        )
        return APIResponse(
            success=True,
            data=_build_session_response(improvement_service, updated_session),
            message="Agent 流程已执行",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent 流程失败：{str(e)}",
        ) from e

