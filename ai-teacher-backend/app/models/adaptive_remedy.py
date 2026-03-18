"""
自适应补救系统 - 模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.models.retention import ErrorType


class RemedyStatus(str, Enum):
    """补救状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RemedialStrategy(str, Enum):
    """补救策略"""
    CALCULATION_TIP = "calculation_tip"         # 计算提示
    CONCEPT_REVIEW = "concept_review"           # 概念复习
    PREREQUISITE_FILL = "prerequisite_fill"     # 前置知识补习
    PROCEDURE_PRACTICE = "procedure_practice"   # 程序强化练习
    ERROR_PREVENTION = "error_prevention"       # 错误预防


@dataclass
class ErrorAnalysis:
    """错误分析结果"""
    error_type: ErrorType
    error_description: str
    related_knowledge_gaps: list[str] = field(default_factory=list)
    severity: str = "moderate"  # minor/moderate/severe
    remedial_strategy: RemedialStrategy = RemedialStrategy.CONCEPT_REVIEW
    confidence: float = 0.8
    
    def to_dict(self) -> dict:
        return {
            "error_type": self.error_type.value,
            "error_description": self.error_description,
            "related_knowledge_gaps": self.related_knowledge_gaps,
            "severity": self.severity,
            "remedial_strategy": self.remedial_strategy.value,
            "confidence": self.confidence,
        }


@dataclass
class RemedialContent:
    """补救内容"""
    target_kp_id: str
    target_kp_name: str
    error_analysis: ErrorAnalysis
    review_content: str = ""
    examples: list[str] = field(default_factory=list)
    practice_questions: list[dict] = field(default_factory=list)
    estimated_time: int = 5  # 分钟
    
    def to_dict(self) -> dict:
        return {
            "target_kp_id": self.target_kp_id,
            "target_kp_name": self.target_kp_name,
            "error_analysis": self.error_analysis.to_dict(),
            "review_content": self.review_content,
            "examples": self.examples,
            "practice_questions": self.practice_questions,
            "estimated_time": self.estimated_time,
        }


@dataclass
class AdaptiveRemedyPlan:
    """自适应补救计划"""
    id: int
    student_id: int
    current_kp_id: str
    current_kp_name: str
    error_analysis: ErrorAnalysis
    remedy_path: list[RemedialContent] = field(default_factory=list)
    current_step: int = 0
    status: RemedyStatus = RemedyStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def get_current_content(self) -> Optional[RemedialContent]:
        """获取当前补救内容"""
        if self.current_step < len(self.remedy_path):
            return self.remedy_path[self.current_step]
        return None
    
    def advance_step(self) -> bool:
        """进入下一步"""
        if self.current_step < len(self.remedy_path) - 1:
            self.current_step += 1
            return True
        return False
    
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.current_step >= len(self.remedy_path) - 1
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "current_kp_id": self.current_kp_id,
            "current_kp_name": self.current_kp_name,
            "error_analysis": self.error_analysis.to_dict(),
            "remedy_path": [c.to_dict() for c in self.remedy_path],
            "current_step": self.current_step,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


# 错误类型与补救策略映射
ERROR_STRATEGY_MAPPING = {
    ErrorType.CALCULATION: RemedialStrategy.CALCULATION_TIP,
    ErrorType.CONCEPT_MISUNDERSTANDING: RemedialStrategy.CONCEPT_REVIEW,
    ErrorType.KNOWLEDGE_GAP: RemedialStrategy.PREREQUISITE_FILL,
    ErrorType.CARELESS: RemedialStrategy.ERROR_PREVENTION,
    ErrorType.PROCEDURE_ERROR: RemedialStrategy.PROCEDURE_PRACTICE,
}

# 错误严重程度判定阈值
SEVERITY_THRESHOLDS = {
    "minor": 1,      # 尝试1次
    "moderate": 3,   # 尝试2-3次
    "severe": 4,     # 尝试4次以上
}
