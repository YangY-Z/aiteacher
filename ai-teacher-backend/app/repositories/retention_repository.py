"""
课后保持和自适应补救 - Repository
"""

from datetime import date, datetime
from typing import Optional

from app.repositories.base import BaseRepository
from app.models.retention import (
    RetentionSchedule,
    MicroPractice,
    WrongAnswerRecord,
    ReviewStatus,
)
from app.models.adaptive_remedy import AdaptiveRemedyPlan, RemedyStatus


class RetentionRepository(BaseRepository):
    """课后保持Repository"""

    def __init__(self, db):
        self._db = db
        self._retention_schedules: dict[int, RetentionSchedule] = {}
        self._micro_practices: dict[str, MicroPractice] = {}
        self._wrong_answers: dict[int, WrongAnswerRecord] = {}
        self._schedule_id_counter = 0
        self._wrong_answer_id_counter = 0

    # ============= BaseRepository 抽象方法实现 =============
    
    def get_by_id(self, id: int) -> Optional[RetentionSchedule]:
        """获取实体"""
        return self._retention_schedules.get(id)
    
    def get_all(self) -> list[RetentionSchedule]:
        """获取所有实体"""
        return list(self._retention_schedules.values())
    
    def create(self, entity: RetentionSchedule) -> RetentionSchedule:
        """创建实体"""
        return self.save_retention_schedule(entity)
    
    def update(self, entity: RetentionSchedule) -> RetentionSchedule:
        """更新实体"""
        self._retention_schedules[entity.id] = entity
        return entity
    
    def delete(self, id: int) -> bool:
        """删除实体"""
        if id in self._retention_schedules:
            del self._retention_schedules[id]
            return True
        return False

    # ============= 复习计划 =============
    
    def save_retention_schedule(self, schedule: RetentionSchedule) -> RetentionSchedule:
        """保存复习计划"""
        if schedule.id == 0:
            self._schedule_id_counter += 1
            schedule.id = self._schedule_id_counter
        
        key = schedule.id
        self._retention_schedules[key] = schedule
        return schedule

    def get_retention_schedule(self, student_id: int, kp_id: str) -> Optional[RetentionSchedule]:
        """获取复习计划"""
        for schedule in self._retention_schedules.values():
            if schedule.student_id == student_id and schedule.kp_id == kp_id:
                return schedule
        return None

    def get_student_schedules(self, student_id: int) -> list[RetentionSchedule]:
        """获取学生的所有复习计划"""
        return [
            s for s in self._retention_schedules.values()
            if s.student_id == student_id
        ]

    # ============= 微练习 =============
    
    def save_micro_practice(self, practice: MicroPractice) -> MicroPractice:
        """保存微练习"""
        self._micro_practices[practice.id] = practice
        return practice

    def get_micro_practice(self, practice_id: str) -> Optional[MicroPractice]:
        """获取微练习"""
        return self._micro_practices.get(practice_id)

    def get_micro_practices_by_date(self, student_id: int, target_date: date) -> list[MicroPractice]:
        """获取指定日期的微练习"""
        return [
            p for p in self._micro_practices.values()
            if p.student_id == student_id and p.scheduled_date == target_date
        ]

    # ============= 错题 =============
    
    def save_wrong_answer_record(self, record: WrongAnswerRecord) -> WrongAnswerRecord:
        """保存错题记录"""
        if record.id == 0:
            self._wrong_answer_id_counter += 1
            record.id = self._wrong_answer_id_counter
        
        self._wrong_answers[record.id] = record
        return record

    def get_wrong_answer_record(self, student_id: int, question_id: str) -> Optional[WrongAnswerRecord]:
        """获取错题记录"""
        for record in self._wrong_answers.values():
            if record.student_id == student_id and record.question_id == question_id:
                return record
        return None

    def get_student_wrong_answers(self, student_id: int) -> list[WrongAnswerRecord]:
        """获取学生的所有错题"""
        return [
            r for r in self._wrong_answers.values()
            if r.student_id == student_id
        ]


class AdaptiveRemedyRepository(BaseRepository):
    """自适应补救Repository"""

    def __init__(self, db):
        self._db = db
        self._remedy_plans: dict[int, AdaptiveRemedyPlan] = {}
        self._plan_id_counter = 0

    # ============= BaseRepository 抽象方法实现 =============
    
    def get_by_id(self, id: int) -> Optional[AdaptiveRemedyPlan]:
        """获取实体"""
        return self._remedy_plans.get(id)
    
    def get_all(self) -> list[AdaptiveRemedyPlan]:
        """获取所有实体"""
        return list(self._remedy_plans.values())
    
    def create(self, entity: AdaptiveRemedyPlan) -> AdaptiveRemedyPlan:
        """创建实体"""
        return self.save_remedy_plan(entity)
    
    def update(self, entity: AdaptiveRemedyPlan) -> AdaptiveRemedyPlan:
        """更新实体"""
        self._remedy_plans[entity.id] = entity
        return entity
    
    def delete(self, id: int) -> bool:
        """删除实体"""
        if id in self._remedy_plans:
            del self._remedy_plans[id]
            return True
        return False

    def save_remedy_plan(self, plan: AdaptiveRemedyPlan) -> AdaptiveRemedyPlan:
        """保存补救计划"""
        if plan.id == 0:
            self._plan_id_counter += 1
            plan.id = self._plan_id_counter
        
        self._remedy_plans[plan.id] = plan
        return plan

    def get_remedy_plan(self, plan_id: int) -> Optional[AdaptiveRemedyPlan]:
        """获取补救计划"""
        return self._remedy_plans.get(plan_id)

    def get_active_remedy_plan(self, student_id: int, kp_id: str) -> Optional[AdaptiveRemedyPlan]:
        """获取活跃的补救计划"""
        for plan in self._remedy_plans.values():
            if (plan.student_id == student_id and 
                plan.current_kp_id == kp_id and
                plan.status in [RemedyStatus.PENDING, RemedyStatus.IN_PROGRESS]):
                return plan
        return None

    def get_student_remedy_plans(self, student_id: int) -> list[AdaptiveRemedyPlan]:
        """获取学生的所有补救计划"""
        return [
            p for p in self._remedy_plans.values()
            if p.student_id == student_id
        ]
