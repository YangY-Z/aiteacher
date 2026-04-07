"""Learning schemas for API request/response models."""

from typing import Any, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import APIResponse


class StartSessionRequest(BaseModel):
    """Request model for starting a learning session."""

    course_id: str = Field(..., description="课程ID")
    kp_id: Optional[str] = Field(None, description="可选的知识点ID")


class SessionResponse(BaseModel):
    """Response model for learning session."""

    session_id: str = Field(..., description="会话ID")
    course_id: str = Field(..., description="课程ID")
    kp_id: Optional[str] = Field(None, description="当前知识点ID")
    status: str = Field(..., description="会话状态")


class ChatRequest(BaseModel):
    """Request model for sending a message."""

    message: str = Field(..., description="学生消息")
    input_type: str = Field("text", description="输入类型: text/voice")
    is_first_input: bool = Field(False, description="是否是首次输入（欢迎语后的确认）")


class ChatResponse(BaseModel):
    """Response model for AI chat response."""

    response_type: str = Field(..., description="响应类型: 讲解/提问/反馈/总结/引导")
    content: dict[str, Any] = Field(default_factory=dict, description="响应内容")
    whiteboard: dict[str, Any] = Field(default_factory=dict, description="白板内容")
    next_action: str = Field("wait_for_student", description="下一步动作")


class AssessmentRequest(BaseModel):
    """Request model for submitting assessment answers."""

    answers: list[dict[str, Any]] = Field(
        ...,
        description="答题列表，每项包含question_id和answer",
    )


class AssessmentResponse(BaseModel):
    """Response model for assessment result."""

    result: str = Field(..., description="结果: passed/failed")
    score: float = Field(..., description="得分比例")
    correct_count: int = Field(..., description="正确题数")
    total_questions: int = Field(..., description="总题数")
    passed: bool = Field(..., description="是否通过")
    next_kp_id: Optional[str] = Field(None, description="下一个知识点ID")
    next_kp_name: Optional[str] = Field(None, description="下一个知识点名称")
    backtrack_required: bool = Field(False, description="是否需要回溯")
    question_results: Optional[list[dict[str, Any]]] = Field(
        None, description="每道题的详细结果"
    )


class KnowledgePointProgress(BaseModel):
    """Response model for knowledge point progress."""

    id: str = Field(..., description="知识点ID")
    name: str = Field(..., description="知识点名称")
    type: str = Field(..., description="知识点类型")
    level: int = Field(..., description="知识点层级")
    status: str = Field(..., description="状态: locked/in_progress/current/completed/skipped")
    progress: float = Field(0, description="进度(0-100)")
    dependencies: list[str] = Field(default_factory=list, description="依赖的知识点ID列表")


class ProgressResponse(BaseModel):
    """Response model for learning progress."""

    student_id: int = Field(..., description="学生ID")
    course_id: str = Field(..., description="课程ID")
    current_kp_id: Optional[str] = Field(None, description="当前知识点ID")
    current_kp_name: Optional[str] = Field(None, description="当前知识点名称")
    completed_count: int = Field(0, description="已完成知识点数")
    mastered_count: int = Field(0, description="已掌握知识点数")
    skipped_count: int = Field(0, description="已跳过知识点数")
    total_count: int = Field(0, description="知识点总数")
    mastery_rate: float = Field(0, description="掌握率")
    total_time: int = Field(0, description="总学习时长(秒)")
    session_count: int = Field(0, description="会话次数")
    last_session_at: Optional[datetime] = Field(None, description="最后学习时间")
    knowledge_points: list[KnowledgePointProgress] = Field(
        default_factory=list, description="知识点进度详情列表"
    )


class SkipRequest(BaseModel):
    """Request model for skipping a knowledge point."""

    reason: Optional[str] = Field(None, description="跳过原因")