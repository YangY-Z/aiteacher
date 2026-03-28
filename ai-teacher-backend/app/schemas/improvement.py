"""专项提升模块 API Schemas。"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ScoreUploadRequest(BaseModel):
    """成绩上传请求。"""

    exam_name: str = Field(..., description="试卷/作业名称")
    score: float = Field(..., ge=0, description="得分")
    total_score: float = Field(..., gt=0, description="满分")
    error_description: Optional[str] = Field(None, description="错题描述/老师评语")
    available_time: int = Field(30, ge=10, le=180, description="可投入时间（分钟）")
    difficulty: str = Field("normal", description="期望难度: basic/normal/challenge")
    foundation: str = Field("average", description="自评基础: weak/average/good")
    max_clarification_rounds: int = Field(5, ge=1, le=5, description="最大澄清轮次")


class StartImprovementRequest(BaseModel):
    """开始专项提升请求。"""

    course_id: str
    score_input: ScoreUploadRequest


class ClarificationAnswerRequest(BaseModel):
    """澄清回答请求。"""

    answer: str = Field(..., min_length=1, description="学生回答")


class GeneratePlanRequest(BaseModel):
    """生成学习方案请求。"""

    confirm_diagnosis: bool = True


class CompleteStepRequest(BaseModel):
    """完成步骤请求。"""

    notes: Optional[str] = None


class QuizSubmitRequest(BaseModel):
    """提交小测请求。"""

    answers: list[dict[str, Any]]


class ClarificationRoundResponse(BaseModel):
    """澄清轮次响应。"""

    round_number: int
    system_question: str
    student_answer: Optional[str] = None
    created_at: datetime
    answered_at: Optional[datetime] = None


class DiagnosisResponse(BaseModel):
    """诊断结果响应。"""

    target_knowledge_point_id: str
    target_kp_name: str
    confidence: float
    reason: str
    prerequisite_gaps: list[str] = Field(default_factory=list)


class PlanStepResponse(BaseModel):
    """方案步骤响应。"""

    step_order: int
    knowledge_point_id: str
    kp_name: str
    goal: str
    estimated_minutes: int
    is_completed: bool = False


class ImprovementPlanResponse(BaseModel):
    """学习方案响应。"""

    plan_id: str
    target_kp_id: str
    target_kp_name: str
    steps: list[PlanStepResponse]
    total_estimated_minutes: int


class ImprovementSessionResponse(BaseModel):
    """专项提升会话响应。"""

    session_id: str
    student_id: str
    course_id: str
    status: str
    max_clarification_rounds: int = 5
    score_input: Optional[dict[str, Any]] = None
    clarification_rounds: list[ClarificationRoundResponse] = Field(default_factory=list)
    diagnosis: Optional[DiagnosisResponse] = None
    plan: Optional[ImprovementPlanResponse] = None
    current_step_order: int = 0
    created_at: datetime
    updated_at: datetime


class QuizQuestionResponse(BaseModel):
    """小测题目响应。"""

    id: str
    type: str
    content: str
    options: Optional[list[str]] = None
    difficulty: str


class QuizResponse(BaseModel):
    """小测响应。"""

    quiz_id: str
    target_kp_id: str
    questions: list[QuizQuestionResponse]


class QuizResultResponse(BaseModel):
    """小测结果响应。"""

    quiz_id: str
    score: float
    passed: bool
    feedback: str
