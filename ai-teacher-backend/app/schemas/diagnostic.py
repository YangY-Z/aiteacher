"""Diagnostic schemas for API request/response models."""

from typing import Any, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import APIResponse


class StartDiagnosticRequest(BaseModel):
    """Request model for starting a diagnostic session."""

    course_id: str = Field(..., description="课程ID")
    target_kp_id: str = Field(..., description="目标知识点ID")


class DiagnosticQuestionResponse(BaseModel):
    """Response model for a diagnostic question."""

    id: str = Field(..., description="题目ID")
    session_id: str = Field(..., description="诊断会话ID")
    kp_id: str = Field(..., description="关联知识点ID")
    category: str = Field(..., description="问题类别: prerequisite/target")
    question_type: str = Field(..., description="题型: point_click/input/choice")
    content: str = Field(..., description="题目内容")
    options: Optional[list[str]] = Field(None, description="选择题选项")
    image_url: Optional[str] = Field(None, description="题目配图URL")
    coordinate_range: Optional[dict[str, Any]] = Field(None, description="坐标范围设置")
    order: int = Field(0, description="题目顺序")


class DiagnosticSessionResponse(BaseModel):
    """Response model for diagnostic session."""

    session_id: str = Field(..., description="诊断会话ID")
    course_id: str = Field(..., description="课程ID")
    target_kp_id: str = Field(..., description="目标知识点ID")
    status: str = Field(..., description="会话状态: pending/in_progress/completed")
    progress: dict[str, int] = Field(..., description="进度信息")
    current_question: Optional[DiagnosticQuestionResponse] = Field(None, description="当前题目")


class DiagnosticAnswerRequest(BaseModel):
    """Request model for submitting an answer."""

    question_id: str = Field(..., description="题目ID")
    answer: Any = Field(..., description="学生答案（格式取决于题型）")
    response_time: Optional[int] = Field(None, description="答题耗时（秒）")


class DiagnosticAnswerResponse(BaseModel):
    """Response model after submitting an answer."""

    is_correct: bool = Field(..., description="是否正确")
    explanation: Optional[str] = Field(None, description="答案解析")
    progress: dict[str, int] = Field(..., description="当前进度")
    next_question: Optional[DiagnosticQuestionResponse] = Field(None, description="下一题")
    session_completed: bool = Field(False, description="诊断会话是否完成")


class PrerequisiteCheckResponse(BaseModel):
    """Response model for prerequisite check result."""

    kp_id: str = Field(..., description="知识点ID")
    kp_name: str = Field(..., description="知识点名称")
    is_mastered: bool = Field(..., description="是否掌握")
    questions_total: int = Field(0, description="总题数")
    questions_correct: int = Field(0, description="正确题数")
    confidence: float = Field(0.0, description="置信度")


class DiagnosticResultResponse(BaseModel):
    """Response model for diagnostic result."""

    session_id: str = Field(..., description="诊断会话ID")
    target_kp_id: str = Field(..., description="目标知识点ID")
    target_kp_name: str = Field(..., description="目标知识点名称")
    conclusion: str = Field(..., description="诊断结论: full_mastery/partial_mastery/need_review/full_learning")
    prerequisite_results: list[PrerequisiteCheckResponse] = Field(
        default_factory=list, description="前置知识检测结果"
    )
    target_questions_total: int = Field(0, description="目标知识检测总题数")
    target_questions_correct: int = Field(0, description="目标知识检测正确题数")
    total_questions: int = Field(0, description="总题数")
    total_correct: int = Field(0, description="总正确题数")
    correct_rate: float = Field(0.0, description="正确率")
    recommended_starting_point: Optional[str] = Field(None, description="推荐学习起点kp_id")
    recommended_teaching_mode: Optional[str] = Field(None, description="推荐教学模式")
    summary: Optional[str] = Field(None, description="诊断总结")
    created_at: Optional[datetime] = Field(None, description="创建时间")


class DiagnosticQuestionGenerateRequest(BaseModel):
    """Request model for generating diagnostic questions."""

    kp_id: str = Field(..., description="知识点ID")
    kp_name: str = Field(..., description="知识点名称")
    kp_type: str = Field(..., description="知识点类型")
    description: Optional[str] = Field(None, description="知识点描述")
    question_count: int = Field(1, description="生成题目数量", ge=1, le=3)
    category: str = Field("target", description="题目类别: prerequisite/target")


class CoordinateAnswer(BaseModel):
    """Model for coordinate click answer."""

    x: float = Field(..., description="X坐标")
    y: float = Field(..., description="Y坐标")


class ChoiceAnswer(BaseModel):
    """Model for choice answer."""

    selected: str = Field(..., description="选中的选项")


class InputAnswer(BaseModel):
    """Model for input answer."""

    value: str = Field(..., description="输入的值")
