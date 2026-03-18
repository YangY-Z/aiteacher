"""
课后保持API接口
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_student_id
from app.models.retention import ErrorType
from app.services.retention_service import RetentionService
from app.services.adaptive_remedy_service import AdaptiveRemedyService
from app.repositories.retention_repository import RetentionRepository, AdaptiveRemedyRepository
from app.repositories.memory_db import db

router = APIRouter(prefix="/api/v1/retention", tags=["retention"])

# 初始化服务
retention_repo = RetentionRepository(db)
remedy_repo = AdaptiveRemedyRepository(db)
retention_service = RetentionService(retention_repo)
remedy_service = AdaptiveRemedyService(remedy_repo)


# ============= 请求/响应模型 =============

class CreateRetentionScheduleRequest(BaseModel):
    kp_id: str
    mastery_date: Optional[datetime] = None


class CompleteReviewRequest(BaseModel):
    kp_id: str


class GenerateMicroPracticeRequest(BaseModel):
    kp_id: str
    kp_name: str


class CompleteMicroPracticeRequest(BaseModel):
    answers: list[dict]


class RecordWrongAnswerRequest(BaseModel):
    question_id: str
    kp_id: str
    kp_name: str
    question_content: str
    wrong_answer: str
    correct_answer: str
    error_type: str = "careless"
    error_analysis: str = ""


class RecordCorrectAnswerRequest(BaseModel):
    question_id: str


class AnalyzeErrorRequest(BaseModel):
    kp_id: str
    wrong_answers: list[dict]
    attempt_count: int


class CreateRemedyPlanRequest(BaseModel):
    kp_id: str
    kp_name: str
    error_analysis: dict


# ============= API路由 =============

@router.get("/schedules")
async def get_retention_schedules(student_id: int = Depends(get_current_student_id)):
    """获取学生的复习计划列表"""
    schedules = retention_service.get_today_schedules(student_id)
    return {
        "success": True,
        "data": [s.to_dict() for s in schedules]
    }


@router.post("/schedules")
async def create_retention_schedule(
    request: CreateRetentionScheduleRequest,
    student_id: int = Depends(get_current_student_id)
):
    """创建复习计划"""
    schedule = retention_service.create_retention_schedule(
        student_id=student_id,
        kp_id=request.kp_id,
        mastery_date=request.mastery_date
    )
    return {
        "success": True,
        "data": schedule.to_dict()
    }


@router.post("/schedules/complete")
async def complete_review(
    request: CompleteReviewRequest,
    student_id: int = Depends(get_current_student_id)
):
    """完成一次复习"""
    try:
        schedule = retention_service.complete_review(
            student_id=student_id,
            kp_id=request.kp_id
        )
        return {
            "success": True,
            "data": schedule.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/micro-practices/today")
async def get_today_micro_practices(student_id: int = Depends(get_current_student_id)):
    """获取今日微练习"""
    practices = retention_service.get_today_micro_practices(student_id)
    return {
        "success": True,
        "data": [p.to_dict() for p in practices]
    }


@router.post("/micro-practices")
async def generate_micro_practice(
    request: GenerateMicroPracticeRequest,
    student_id: int = Depends(get_current_student_id)
):
    """生成微练习"""
    practice = retention_service.generate_micro_practice(
        student_id=student_id,
        kp_id=request.kp_id,
        kp_name=request.kp_name
    )
    return {
        "success": True,
        "data": practice.to_dict()
    }


@router.post("/micro-practices/{practice_id}/complete")
async def complete_micro_practice(
    practice_id: str,
    request: CompleteMicroPracticeRequest,
    student_id: int = Depends(get_current_student_id)
):
    """完成微练习"""
    try:
        practice = retention_service.complete_micro_practice(
            practice_id=practice_id,
            answers=request.answers
        )
        return {
            "success": True,
            "data": practice.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/wrong-answers")
async def get_wrong_answer_book(student_id: int = Depends(get_current_student_id)):
    """获取错题本"""
    book = retention_service.get_wrong_answer_book(student_id)
    return {
        "success": True,
        "data": book.to_dict()
    }


@router.post("/wrong-answers")
async def record_wrong_answer(
    request: RecordWrongAnswerRequest,
    student_id: int = Depends(get_current_student_id)
):
    """记录错题"""
    record = retention_service.record_wrong_answer(
        student_id=student_id,
        question_id=request.question_id,
        kp_id=request.kp_id,
        kp_name=request.kp_name,
        question_content=request.question_content,
        wrong_answer=request.wrong_answer,
        correct_answer=request.correct_answer,
        error_type=ErrorType(request.error_type),
        error_analysis=request.error_analysis
    )
    return {
        "success": True,
        "data": record.to_dict()
    }


@router.post("/wrong-answers/correct")
async def record_correct_answer(
    request: RecordCorrectAnswerRequest,
    student_id: int = Depends(get_current_student_id)
):
    """记录正确回答（错题重做）"""
    try:
        record = retention_service.record_correct_answer(
            student_id=student_id,
            question_id=request.question_id
        )
        return {
            "success": True,
            "data": record.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/wrong-answers/pending")
async def get_pending_wrong_answers(
    limit: int = 10,
    student_id: int = Depends(get_current_student_id)
):
    """获取待复习的错题"""
    records = retention_service.get_pending_wrong_answers(
        student_id=student_id,
        limit=limit
    )
    return {
        "success": True,
        "data": [r.to_dict() for r in records]
    }


@router.post("/analyze-error")
async def analyze_error(
    request: AnalyzeErrorRequest,
    student_id: int = Depends(get_current_student_id)
):
    """分析错误类型"""
    analysis = remedy_service.analyze_error(
        student_id=student_id,
        kp_id=request.kp_id,
        wrong_answers=request.wrong_answers,
        attempt_count=request.attempt_count
    )
    return {
        "success": True,
        "data": analysis.to_dict()
    }


@router.post("/remedy-plans")
async def create_remedy_plan(
    request: CreateRemedyPlanRequest,
    student_id: int = Depends(get_current_student_id)
):
    """创建补救计划"""
    from app.models.adaptive_remedy import ErrorAnalysis
    
    # 构建错误分析对象
    error_analysis = ErrorAnalysis(
        error_type=ErrorType(request.error_analysis.get("error_type", "careless")),
        error_description=request.error_analysis.get("error_description", ""),
        related_knowledge_gaps=request.error_analysis.get("related_knowledge_gaps", []),
        severity=request.error_analysis.get("severity", "moderate"),
    )
    
    plan = remedy_service.create_remedy_plan(
        student_id=student_id,
        current_kp_id=request.kp_id,
        current_kp_name=request.kp_name,
        error_analysis=error_analysis
    )
    return {
        "success": True,
        "data": plan.to_dict()
    }


@router.get("/remedy-plans/{plan_id}")
async def get_remedy_plan(
    plan_id: int,
    student_id: int = Depends(get_current_student_id)
):
    """获取补救计划"""
    plan = remedy_service.get_remedy_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="补救计划不存在")
    return {
        "success": True,
        "data": plan.to_dict()
    }


@router.post("/remedy-plans/{plan_id}/advance")
async def advance_remedy_step(
    plan_id: int,
    student_id: int = Depends(get_current_student_id)
):
    """进入补救计划的下一步"""
    try:
        plan = remedy_service.advance_remedy_step(plan_id)
        return {
            "success": True,
            "data": plan.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/remedy-plans/{plan_id}/complete")
async def complete_remedy(
    plan_id: int,
    success: bool = True,
    student_id: int = Depends(get_current_student_id)
):
    """完成补救"""
    try:
        plan = remedy_service.complete_remedy(plan_id, success)
        return {
            "success": True,
            "data": plan.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))