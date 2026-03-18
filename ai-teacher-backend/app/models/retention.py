"""
课后保持系统 - 模型定义
包含：复习计划、微练习、错题记录
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional


class ReviewStatus(str, Enum):
    """复习状态"""
    PENDING = "pending"           # 待复习
    COMPLETED = "completed"       # 已完成
    MASTERY_CONFIRMED = "mastery_confirmed"  # 已确认掌握


class ErrorType(str, Enum):
    """错误类型"""
    CALCULATION = "calculation"           # 计算错误
    CONCEPT_MISUNDERSTANDING = "concept"  # 概念误解
    KNOWLEDGE_GAP = "gap"                 # 知识断层
    CARELESS = "careless"                 # 粗心大意
    PROCEDURE_ERROR = "procedure"         # 程序错误


@dataclass
class RetentionSchedule:
    """复习计划（基于艾宾浩斯遗忘曲线）"""
    id: int
    student_id: int
    kp_id: str
    mastery_date: datetime
    review_dates: list[datetime] = field(default_factory=list)
    # 基于遗忘曲线：1天、3天、7天、30天
    completed_reviews: list[datetime] = field(default_factory=list)
    status: ReviewStatus = ReviewStatus.PENDING
    
    def get_next_review(self) -> Optional[datetime]:
        """获取下一次复习时间"""
        now = datetime.now()
        for review_date in self.review_dates:
            if review_date > now and review_date not in self.completed_reviews:
                return review_date
        return None
    
    def is_due_today(self) -> bool:
        """是否今天需要复习"""
        next_review = self.get_next_review()
        if not next_review:
            return False
        return next_review.date() == date.today()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "kp_id": self.kp_id,
            "mastery_date": self.mastery_date.isoformat() if self.mastery_date else None,
            "review_dates": [d.isoformat() for d in self.review_dates],
            "completed_reviews": [d.isoformat() for d in self.completed_reviews],
            "status": self.status.value,
        }


@dataclass
class MicroPractice:
    """微练习（2分钟，2-3题）"""
    id: str
    kp_id: str
    kp_name: str
    student_id: int
    scheduled_date: date
    questions: list[dict] = field(default_factory=list)
    estimated_time: int = 120  # 2分钟
    status: ReviewStatus = ReviewStatus.PENDING
    score: Optional[float] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kp_id": self.kp_id,
            "kp_name": self.kp_name,
            "student_id": self.student_id,
            "scheduled_date": self.scheduled_date.isoformat(),
            "questions": self.questions,
            "estimated_time": self.estimated_time,
            "status": self.status.value,
            "score": self.score,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class WrongAnswerRecord:
    """错题记录"""
    id: int
    student_id: int
    question_id: str
    kp_id: str
    kp_name: str
    question_content: str
    wrong_answer: str
    correct_answer: str
    error_type: ErrorType = ErrorType.CARELESS
    error_analysis: str = ""
    wrong_count: int = 1
    correct_count: int = 0
    first_wrong_at: datetime = field(default_factory=datetime.now)
    last_wrong_at: Optional[datetime] = None
    last_correct_at: Optional[datetime] = None
    
    def is_mastered(self) -> bool:
        """是否已掌握（连续3次正确）"""
        return self.correct_count >= 3
    
    def record_wrong(self) -> None:
        """记录再次错误"""
        self.wrong_count += 1
        self.last_wrong_at = datetime.now()
        self.correct_count = 0  # 重置正确计数
    
    def record_correct(self) -> None:
        """记录正确"""
        self.correct_count += 1
        self.last_correct_at = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "question_id": self.question_id,
            "kp_id": self.kp_id,
            "kp_name": self.kp_name,
            "question_content": self.question_content,
            "wrong_answer": self.wrong_answer,
            "correct_answer": self.correct_answer,
            "error_type": self.error_type.value,
            "error_analysis": self.error_analysis,
            "wrong_count": self.wrong_count,
            "correct_count": self.correct_count,
            "is_mastered": self.is_mastered(),
            "first_wrong_at": self.first_wrong_at.isoformat(),
            "last_wrong_at": self.last_wrong_at.isoformat() if self.last_wrong_at else None,
            "last_correct_at": self.last_correct_at.isoformat() if self.last_correct_at else None,
        }


@dataclass
class WrongAnswerBook:
    """错题本"""
    student_id: int
    records: list[WrongAnswerRecord] = field(default_factory=list)
    
    def get_pending_reviews(self) -> list[WrongAnswerRecord]:
        """获取待复习的错题"""
        return [r for r in self.records if not r.is_mastered()]
    
    def get_mastered_records(self) -> list[WrongAnswerRecord]:
        """获取已掌握的错题"""
        return [r for r in self.records if r.is_mastered()]
    
    def get_records_by_kp(self, kp_id: str) -> list[WrongAnswerRecord]:
        """按知识点获取错题"""
        return [r for r in self.records if r.kp_id == kp_id]
    
    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "records": [r.to_dict() for r in self.records],
            "pending_count": len(self.get_pending_reviews()),
            "mastered_count": len(self.get_mastered_records()),
        }


# 艾宾浩斯遗忘曲线复习间隔（天）
RETENTION_INTERVALS = [1, 3, 7, 30]
