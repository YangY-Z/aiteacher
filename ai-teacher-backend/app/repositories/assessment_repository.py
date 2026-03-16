"""Assessment repositories implementation."""

from typing import Any, Optional

from app.models.assessment import AssessmentQuestion, StudentAnswer
from app.repositories.base import BaseRepository
from app.repositories.memory_db import db


class AssessmentQuestionRepository(BaseRepository[AssessmentQuestion, str]):
    """Repository for AssessmentQuestion entities using in-memory storage."""

    def get_by_id(self, id: str) -> Optional[AssessmentQuestion]:
        """Get an assessment question by ID.

        Args:
            id: Question ID.

        Returns:
            AssessmentQuestion if found, None otherwise.
        """
        return db._assessment_questions.get(id)

    def get_by_kp(self, kp_id: str) -> list[AssessmentQuestion]:
        """Get all assessment questions for a knowledge point.

        Args:
            kp_id: Knowledge point ID.

        Returns:
            List of assessment questions for the knowledge point.
        """
        return [
            q
            for q in db._assessment_questions.values()
            if q.kp_id == kp_id
        ]

    def get_all(self) -> list[AssessmentQuestion]:
        """Get all assessment questions.

        Returns:
            List of all assessment questions.
        """
        return list(db._assessment_questions.values())

    def create(self, entity: AssessmentQuestion) -> AssessmentQuestion:
        """Create a new assessment question.

        Args:
            entity: AssessmentQuestion to create.

        Returns:
            The created assessment question.
        """
        db._assessment_questions[entity.id] = entity
        return entity

    def update(self, entity: AssessmentQuestion) -> AssessmentQuestion:
        """Update an existing assessment question.

        Args:
            entity: AssessmentQuestion to update.

        Returns:
            The updated assessment question.
        """
        db._assessment_questions[entity.id] = entity
        return entity

    def delete(self, id: str) -> bool:
        """Delete an assessment question by ID.

        Args:
            id: Question ID.

        Returns:
            True if deleted, False if not found.
        """
        if id in db._assessment_questions:
            del db._assessment_questions[id]
            return True
        return False

    def bulk_create(self, questions: list[AssessmentQuestion]) -> list[AssessmentQuestion]:
        """Create multiple assessment questions.

        Args:
            questions: List of questions to create.

        Returns:
            List of created questions.
        """
        for q in questions:
            db._assessment_questions[q.id] = q
        return questions


class StudentAnswerRepository(BaseRepository[dict[str, Any], int]):
    """Repository for StudentAnswer records using in-memory storage."""

    def get_by_id(self, id: int) -> Optional[dict[str, Any]]:
        """Get a student answer by ID.

        Args:
            id: Answer ID.

        Returns:
            Student answer dict if found, None otherwise.
        """
        return db._student_answers.get(id)

    def get_by_session(self, session_id: str) -> list[dict[str, Any]]:
        """Get all student answers for a session.

        Args:
            session_id: Session ID.

        Returns:
            List of student answers for the session.
        """
        return [
            ans
            for ans in db._student_answers.values()
            if ans.get("session_id") == session_id
        ]

    def get_by_student_and_kp(
        self, student_id: int, kp_id: str
    ) -> list[dict[str, Any]]:
        """Get all student answers for a student on a knowledge point.

        Args:
            student_id: Student ID.
            kp_id: Knowledge point ID.

        Returns:
            List of student answers.
        """
        return [
            ans
            for ans in db._student_answers.values()
            if ans.get("student_id") == student_id and ans.get("kp_id") == kp_id
        ]

    def get_all(self) -> list[dict[str, Any]]:
        """Get all student answers.

        Returns:
            List of all student answers.
        """
        return list(db._student_answers.values())

    def create(self, entity: dict[str, Any]) -> dict[str, Any]:
        """Create a new student answer.

        Args:
            entity: Student answer dict to create.

        Returns:
            The created student answer.
        """
        if "id" not in entity or entity["id"] is None:
            entity["id"] = db.get_next_student_answer_id()
        db._student_answers[entity["id"]] = entity
        return entity

    def update(self, entity: dict[str, Any]) -> dict[str, Any]:
        """Update an existing student answer.

        Args:
            entity: Student answer dict to update.

        Returns:
            The updated student answer.
        """
        db._student_answers[entity["id"]] = entity
        return entity

    def delete(self, id: int) -> bool:
        """Delete a student answer by ID.

        Args:
            id: Answer ID.

        Returns:
            True if deleted, False if not found.
        """
        if id in db._student_answers:
            del db._student_answers[id]
            return True
        return False


# Global repository instances
assessment_question_repository = AssessmentQuestionRepository()
student_answer_repository = StudentAnswerRepository()
