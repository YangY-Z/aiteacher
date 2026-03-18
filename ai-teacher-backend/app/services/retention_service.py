"""
课后保持服务
包含：复习计划、微练习、错题管理
"""

from datetime import datetime, timedelta, date
from typing import Optional
import uuid

from app.models.retention import (
    RetentionSchedule,
    MicroPractice,
    WrongAnswerRecord,
    WrongAnswerBook,
    ReviewStatus,
    ErrorType,
    RETENTION_INTERVALS,
)


class RetentionService:
    """课后保持服务"""

    def __init__(self, repository):
        self.repository = repository

    # ============= 复习计划 =============
    
    def create_retention_schedule(
        self,
        student_id: int,
        kp_id: str,
        mastery_date: Optional[datetime] = None,
    ) -> RetentionSchedule:
        """
        创建复习计划（基于遗忘曲线）
        
        Args:
            student_id: 学生ID
            kp_id: 知识点ID
            mastery_date: 掌握日期
            
        Returns:
            复习计划
        """
        if mastery_date is None:
            mastery_date = datetime.now()
        
        # 基于艾宾浩斯遗忘曲线生成复习日期
        review_dates = [
            mastery_date + timedelta(days=d)
            for d in RETENTION_INTERVALS
        ]
        
        schedule = RetentionSchedule(
            id=0,  # 由repository分配
            student_id=student_id,
            kp_id=kp_id,
            mastery_date=mastery_date,
            review_dates=review_dates,
            status=ReviewStatus.PENDING,
        )
        
        return self.repository.save_retention_schedule(schedule)

    def get_retention_schedule(
        self,
        student_id: int,
        kp_id: str,
    ) -> Optional[RetentionSchedule]:
        """获取复习计划"""
        return self.repository.get_retention_schedule(student_id, kp_id)

    def get_today_schedules(self, student_id: int) -> list[RetentionSchedule]:
        """获取今日需要复习的计划"""
        all_schedules = self.repository.get_student_schedules(student_id)
        return [s for s in all_schedules if s.is_due_today()]

    def complete_review(
        self,
        student_id: int,
        kp_id: str,
    ) -> RetentionSchedule:
        """完成一次复习"""
        schedule = self.get_retention_schedule(student_id, kp_id)
        if not schedule:
            raise ValueError(f"未找到复习计划: student={student_id}, kp={kp_id}")
        
        now = datetime.now()
        # 找到当前应该完成的复习
        for review_date in schedule.review_dates:
            if review_date not in schedule.completed_reviews:
                if review_date.date() <= now.date():
                    schedule.completed_reviews.append(review_date)
                    break
        
        # 检查是否全部完成
        if len(schedule.completed_reviews) == len(schedule.review_dates):
            schedule.status = ReviewStatus.MASTERY_CONFIRMED
        
        return self.repository.save_retention_schedule(schedule)

    # ============= 微练习 =============
    
    def get_today_micro_practices(self, student_id: int) -> list[MicroPractice]:
        """获取今日微练习"""
        return self.repository.get_micro_practices_by_date(
            student_id, 
            date.today()
        )

    def generate_micro_practice(
        self,
        student_id: int,
        kp_id: str,
        kp_name: str,
    ) -> MicroPractice:
        """
        生成微练习（2分钟，2-3题）
        
        Args:
            student_id: 学生ID
            kp_id: 知识点ID
            kp_name: 知识点名称
            
        Returns:
            微练习
        """
        # 获取该知识点的简单题目
        questions = self._select_simple_questions(kp_id, count=3)
        
        practice = MicroPractice(
            id=f"MP_{uuid.uuid4().hex[:8]}",
            kp_id=kp_id,
            kp_name=kp_name,
            student_id=student_id,
            scheduled_date=date.today(),
            questions=questions,
            status=ReviewStatus.PENDING,
        )
        
        return self.repository.save_micro_practice(practice)

    def complete_micro_practice(
        self,
        practice_id: str,
        answers: list[dict],
    ) -> MicroPractice:
        """完成微练习"""
        practice = self.repository.get_micro_practice(practice_id)
        if not practice:
            raise ValueError(f"未找到微练习: {practice_id}")
        
        # 计算得分
        correct_count = 0
        for i, question in enumerate(practice.questions):
            if i < len(answers) and answers[i].get("answer") == question.get("correct_answer"):
                correct_count += 1
        
        practice.score = correct_count / len(practice.questions)
        practice.status = ReviewStatus.COMPLETED
        practice.completed_at = datetime.now()
        
        return self.repository.save_micro_practice(practice)

    def _select_simple_questions(self, kp_id: str, count: int = 3) -> list[dict]:
        """选择简单题目用于微练习"""
        # TODO: 从题库中选择题目
        # 这里使用模拟数据
        return [
            {
                "id": f"q_{i}",
                "content": f"练习题 {i+1}",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
            }
            for i in range(count)
        ]

    # ============= 错题管理 =============
    
    def record_wrong_answer(
        self,
        student_id: int,
        question_id: str,
        kp_id: str,
        kp_name: str,
        question_content: str,
        wrong_answer: str,
        correct_answer: str,
        error_type: ErrorType = ErrorType.CARELESS,
        error_analysis: str = "",
    ) -> WrongAnswerRecord:
        """记录错题"""
        # 检查是否已存在
        existing = self.repository.get_wrong_answer_record(student_id, question_id)
        
        if existing:
            existing.record_wrong()
            existing.error_type = error_type
            existing.error_analysis = error_analysis
            return self.repository.save_wrong_answer_record(existing)
        
        record = WrongAnswerRecord(
            id=0,
            student_id=student_id,
            question_id=question_id,
            kp_id=kp_id,
            kp_name=kp_name,
            question_content=question_content,
            wrong_answer=wrong_answer,
            correct_answer=correct_answer,
            error_type=error_type,
            error_analysis=error_analysis,
        )
        
        return self.repository.save_wrong_answer_record(record)

    def record_correct_answer(
        self,
        student_id: int,
        question_id: str,
    ) -> WrongAnswerRecord:
        """记录正确回答（用于错题重做）"""
        record = self.repository.get_wrong_answer_record(student_id, question_id)
        if not record:
            raise ValueError(f"未找到错题记录: student={student_id}, question={question_id}")
        
        record.record_correct()
        return self.repository.save_wrong_answer_record(record)

    def get_wrong_answer_book(self, student_id: int) -> WrongAnswerBook:
        """获取错题本"""
        records = self.repository.get_student_wrong_answers(student_id)
        return WrongAnswerBook(student_id=student_id, records=records)

    def get_pending_wrong_answers(
        self,
        student_id: int,
        limit: int = 10,
    ) -> list[WrongAnswerRecord]:
        """获取待复习的错题"""
        book = self.get_wrong_answer_book(student_id)
        pending = book.get_pending_reviews()
        return pending[:limit]

    def get_wrong_answers_by_kp(
        self,
        student_id: int,
        kp_id: str,
    ) -> list[WrongAnswerRecord]:
        """按知识点获取错题"""
        book = self.get_wrong_answer_book(student_id)
        return book.get_records_by_kp(kp_id)

    def generate_review_practice(
        self,
        student_id: int,
        kp_id: str,
    ) -> MicroPractice:
        """生成错题复习练习"""
        wrong_answers = self.get_wrong_answers_by_kp(student_id, kp_id)
        
        if not wrong_answers:
            raise ValueError(f"该知识点没有错题: kp={kp_id}")
        
        # 选择未掌握的错题
        pending = [r for r in wrong_answers if not r.is_mastered()][:3]
        
        questions = [
            {
                "id": r.question_id,
                "content": r.question_content,
                "options": ["A", "B", "C", "D"],  # TODO: 从原题目获取
                "correct_answer": r.correct_answer,
                "is_wrong_answer_review": True,
            }
            for r in pending
        ]
        
        practice = MicroPractice(
            id=f"RP_{uuid.uuid4().hex[:8]}",
            kp_id=kp_id,
            kp_name=pending[0].kp_name if pending else "",
            student_id=student_id,
            scheduled_date=date.today(),
            questions=questions,
            status=ReviewStatus.PENDING,
        )
        
        return self.repository.save_micro_practice(practice)
