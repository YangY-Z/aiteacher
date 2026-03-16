"""Repository module for data access layer."""

from app.repositories.base import BaseRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.learning_repository import (
    LearningRecordRepository,
    StudentProfileRepository,
    LearningSessionRepository,
)
from app.repositories.assessment_repository import (
    AssessmentQuestionRepository,
    StudentAnswerRepository,
)
from app.repositories.memory_db import InMemoryDatabase

__all__ = [
    "BaseRepository",
    "StudentRepository",
    "CourseRepository",
    "LearningRecordRepository",
    "StudentProfileRepository",
    "LearningSessionRepository",
    "AssessmentQuestionRepository",
    "StudentAnswerRepository",
    "InMemoryDatabase",
]
