"""Diagnostic-related repositories implementation."""

from datetime import datetime
from typing import Optional
import uuid

from app.models.diagnostic import (
    DiagnosticSession,
    DiagnosticQuestion,
    DiagnosticAnswer,
    DiagnosticResult,
    DiagnosticStatus,
    QuestionCategory,
    DiagnosticQuestionType,
)
from app.repositories.base import BaseRepository
from app.repositories.memory_db import db


class DiagnosticSessionRepository(BaseRepository[DiagnosticSession, str]):
    """Repository for DiagnosticSession entities using in-memory storage."""

    def get_by_id(self, id: str) -> Optional[DiagnosticSession]:
        """Get a diagnostic session by ID.

        Args:
            id: Session ID.

        Returns:
            DiagnosticSession if found, None otherwise.
        """
        return db._diagnostic_sessions.get(id)

    def get_by_student_and_kp(
        self, student_id: int, kp_id: str
    ) -> Optional[DiagnosticSession]:
        """Get the latest diagnostic session for a student and knowledge point.

        Args:
            student_id: Student ID.
            kp_id: Knowledge point ID.

        Returns:
            Latest DiagnosticSession if found, None otherwise.
        """
        sessions = [
            s
            for s in db._diagnostic_sessions.values()
            if s.student_id == student_id and s.target_kp_id == kp_id
        ]
        if sessions:
            return max(sessions, key=lambda s: s.created_at)
        return None

    def get_active_by_student(
        self, student_id: int, course_id: Optional[str] = None
    ) -> Optional[DiagnosticSession]:
        """Get the active diagnostic session for a student.

        Args:
            student_id: Student ID.
            course_id: Optional course ID filter.

        Returns:
            Active DiagnosticSession if found, None otherwise.
        """
        for session in db._diagnostic_sessions.values():
            if (
                session.student_id == student_id
                and session.status == DiagnosticStatus.IN_PROGRESS
            ):
                if course_id is None or session.course_id == course_id:
                    return session
        return None

    def get_by_student(self, student_id: int) -> list[DiagnosticSession]:
        """Get all diagnostic sessions for a student.

        Args:
            student_id: Student ID.

        Returns:
            List of diagnostic sessions for the student.
        """
        return [
            session
            for session in db._diagnostic_sessions.values()
            if session.student_id == student_id
        ]

    def get_all(self) -> list[DiagnosticSession]:
        """Get all diagnostic sessions.

        Returns:
            List of all diagnostic sessions.
        """
        return list(db._diagnostic_sessions.values())

    def create(self, entity: DiagnosticSession) -> DiagnosticSession:
        """Create a new diagnostic session.

        Args:
            entity: DiagnosticSession to create.

        Returns:
            The created diagnostic session.
        """
        if not entity.id:
            entity.id = f"DIAG_{uuid.uuid4().hex[:8].upper()}"
        db._diagnostic_sessions[entity.id] = entity
        return entity

    def update(self, entity: DiagnosticSession) -> DiagnosticSession:
        """Update an existing diagnostic session.

        Args:
            entity: DiagnosticSession to update.

        Returns:
            The updated diagnostic session.
        """
        db._diagnostic_sessions[entity.id] = entity
        return entity

    def delete(self, id: str) -> bool:
        """Delete a diagnostic session by ID.

        Args:
            id: Session ID.

        Returns:
            True if deleted, False if not found.
        """
        if id in db._diagnostic_sessions:
            del db._diagnostic_sessions[id]
            return True
        return False


class DiagnosticQuestionRepository(BaseRepository[DiagnosticQuestion, str]):
    """Repository for DiagnosticQuestion entities using in-memory storage."""

    def get_by_id(self, id: str) -> Optional[DiagnosticQuestion]:
        """Get a diagnostic question by ID.

        Args:
            id: Question ID.

        Returns:
            DiagnosticQuestion if found, None otherwise.
        """
        return db._diagnostic_questions.get(id)

    def get_by_session(self, session_id: str) -> list[DiagnosticQuestion]:
        """Get all questions for a diagnostic session.

        Args:
            session_id: Session ID.

        Returns:
            List of diagnostic questions ordered by order.
        """
        questions = [
            q
            for q in db._diagnostic_questions.values()
            if q.session_id == session_id
        ]
        return sorted(questions, key=lambda q: q.order)

    def get_all(self) -> list[DiagnosticQuestion]:
        """Get all diagnostic questions.

        Returns:
            List of all diagnostic questions.
        """
        return list(db._diagnostic_questions.values())

    def create(self, entity: DiagnosticQuestion) -> DiagnosticQuestion:
        """Create a new diagnostic question.

        Args:
            entity: DiagnosticQuestion to create.

        Returns:
            The created diagnostic question.
        """
        if not entity.id:
            entity.id = f"DQ_{uuid.uuid4().hex[:8].upper()}"
        db._diagnostic_questions[entity.id] = entity
        return entity

    def create_batch(self, entities: list[DiagnosticQuestion]) -> list[DiagnosticQuestion]:
        """Create multiple diagnostic questions.

        Args:
            entities: List of DiagnosticQuestion to create.

        Returns:
            List of created diagnostic questions.
        """
        created = []
        for entity in entities:
            created.append(self.create(entity))
        return created

    def update(self, entity: DiagnosticQuestion) -> DiagnosticQuestion:
        """Update an existing diagnostic question.

        Args:
            entity: DiagnosticQuestion to update.

        Returns:
            The updated diagnostic question.
        """
        db._diagnostic_questions[entity.id] = entity
        return entity

    def delete(self, id: str) -> bool:
        """Delete a diagnostic question by ID.

        Args:
            id: Question ID.

        Returns:
            True if deleted, False if not found.
        """
        if id in db._diagnostic_questions:
            del db._diagnostic_questions[id]
            return True
        return False

    def delete_by_session(self, session_id: str) -> int:
        """Delete all questions for a diagnostic session.

        Args:
            session_id: Session ID.

        Returns:
            Number of questions deleted.
        """
        to_delete = [
            qid for qid, q in db._diagnostic_questions.items()
            if q.session_id == session_id
        ]
        for qid in to_delete:
            del db._diagnostic_questions[qid]
        return len(to_delete)


class DiagnosticAnswerRepository(BaseRepository[DiagnosticAnswer, int]):
    """Repository for DiagnosticAnswer entities using in-memory storage."""

    def get_by_id(self, id: int) -> Optional[DiagnosticAnswer]:
        """Get a diagnostic answer by ID.

        Args:
            id: Answer ID.

        Returns:
            DiagnosticAnswer if found, None otherwise.
        """
        return db._diagnostic_answers.get(id)

    def get_by_session(self, session_id: str) -> list[DiagnosticAnswer]:
        """Get all answers for a diagnostic session.

        Args:
            session_id: Session ID.

        Returns:
            List of diagnostic answers.
        """
        return [
            a
            for a in db._diagnostic_answers.values()
            if a.session_id == session_id
        ]

    def get_by_question(self, question_id: str) -> Optional[DiagnosticAnswer]:
        """Get the answer for a specific question.

        Args:
            question_id: Question ID.

        Returns:
            DiagnosticAnswer if found, None otherwise.
        """
        for answer in db._diagnostic_answers.values():
            if answer.question_id == question_id:
                return answer
        return None

    def get_all(self) -> list[DiagnosticAnswer]:
        """Get all diagnostic answers.

        Returns:
            List of all diagnostic answers.
        """
        return list(db._diagnostic_answers.values())

    def create(self, entity: DiagnosticAnswer) -> DiagnosticAnswer:
        """Create a new diagnostic answer.

        Args:
            entity: DiagnosticAnswer to create.

        Returns:
            The created diagnostic answer.
        """
        if entity.id is None or entity.id == 0:
            entity.id = db.get_next_diagnostic_answer_id()
        db._diagnostic_answers[entity.id] = entity
        return entity

    def update(self, entity: DiagnosticAnswer) -> DiagnosticAnswer:
        """Update an existing diagnostic answer.

        Args:
            entity: DiagnosticAnswer to update.

        Returns:
            The updated diagnostic answer.
        """
        db._diagnostic_answers[entity.id] = entity
        return entity

    def delete(self, id: int) -> bool:
        """Delete a diagnostic answer by ID.

        Args:
            id: Answer ID.

        Returns:
            True if deleted, False if not found.
        """
        if id in db._diagnostic_answers:
            del db._diagnostic_answers[id]
            return True
        return False


# Global repository instances
diagnostic_session_repository = DiagnosticSessionRepository()
diagnostic_question_repository = DiagnosticQuestionRepository()
diagnostic_answer_repository = DiagnosticAnswerRepository()
