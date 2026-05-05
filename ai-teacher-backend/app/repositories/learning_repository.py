"""Learning-related repositories implementation."""

from datetime import datetime
from typing import Optional
import uuid

from app.models.learning import (
    StudentProfile,
    LearningRecord,
    LearningSession,
    LearningStatus,
    SessionStatus,
)
from app.repositories.base import BaseRepository
from app.repositories.memory_db import db


class StudentProfileRepository(BaseRepository[StudentProfile, int]):
    """Repository for StudentProfile entities using in-memory storage."""

    def get_by_id(self, id: int) -> Optional[StudentProfile]:
        """Get a student profile by ID.

        Args:
            id: Profile ID.

        Returns:
            StudentProfile if found, None otherwise.
        """
        return db._student_profiles.get(id)

    def get_by_student_and_course(
        self, student_id: int, course_id: str
    ) -> Optional[StudentProfile]:
        """Get a student profile by student ID and course ID.

        Args:
            student_id: Student ID.
            course_id: Course ID.

        Returns:
            StudentProfile if found, None otherwise.
        """
        for profile in db._student_profiles.values():
            if profile.student_id == student_id and profile.course_id == course_id:
                return profile
        return None

    def get_all(self) -> list[StudentProfile]:
        """Get all student profiles.

        Returns:
            List of all student profiles.
        """
        return list(db._student_profiles.values())

    def create(self, entity: StudentProfile) -> StudentProfile:
        """Create a new student profile.

        Args:
            entity: StudentProfile to create.

        Returns:
            The created student profile.
        """
        if entity.id is None or entity.id == 0:
            entity.id = db.get_next_student_profile_id()
        db._student_profiles[entity.id] = entity
        db.save_student_data()
        return entity

    def update(self, entity: StudentProfile) -> StudentProfile:
        """Update an existing student profile.

        Args:
            entity: StudentProfile to update.

        Returns:
            The updated student profile.
        """
        db._student_profiles[entity.id] = entity
        db.save_student_data()
        return entity

    def delete(self, id: int) -> bool:
        """Delete a student profile by ID.

        Args:
            id: Profile ID.

        Returns:
            True if deleted, False if not found.
        """
        if id in db._student_profiles:
            del db._student_profiles[id]
            db.save_student_data()
            return True
        return False


class LearningRecordRepository(BaseRepository[LearningRecord, int]):
    """Repository for LearningRecord entities using in-memory storage."""

    def get_by_id(self, id: int) -> Optional[LearningRecord]:
        """Get a learning record by ID.

        Args:
            id: Record ID.

        Returns:
            LearningRecord if found, None otherwise.
        """
        return db._learning_records.get(id)

    def get_by_student_and_kp(
        self, student_id: int, kp_id: str
    ) -> Optional[LearningRecord]:
        """Get a learning record by student ID and knowledge point ID.

        Args:
            student_id: Student ID.
            kp_id: Knowledge point ID.

        Returns:
            LearningRecord if found, None otherwise.
        """
        for record in db._learning_records.values():
            if record.student_id == student_id and record.kp_id == kp_id:
                return record
        return None

    def get_by_student(self, student_id: int) -> list[LearningRecord]:
        """Get all learning records for a student.

        Args:
            student_id: Student ID.

        Returns:
            List of learning records for the student.
        """
        return [
            record
            for record in db._learning_records.values()
            if record.student_id == student_id
        ]

    def get_by_student_and_course(
        self, student_id: int, course_id: str
    ) -> list[LearningRecord]:
        """Get all learning records for a student in a course.

        Args:
            student_id: Student ID.
            course_id: Course ID.

        Returns:
            List of learning records for the student in the course.
        """
        # Get all KP IDs for the course
        course_kp_ids = {
            kp.id
            for kp in db._knowledge_points.values()
            if kp.course_id == course_id
        }
        return [
            record
            for record in db._learning_records.values()
            if record.student_id == student_id and record.kp_id in course_kp_ids
        ]

    def get_all(self) -> list[LearningRecord]:
        """Get all learning records.

        Returns:
            List of all learning records.
        """
        return list(db._learning_records.values())

    def create(self, entity: LearningRecord) -> LearningRecord:
        """Create a new learning record.

        Args:
            entity: LearningRecord to create.

        Returns:
            The created learning record.
        """
        if entity.id is None or entity.id == 0:
            entity.id = db.get_next_learning_record_id()
        db._learning_records[entity.id] = entity
        return entity

    def update(self, entity: LearningRecord) -> LearningRecord:
        """Update an existing learning record.

        Args:
            entity: LearningRecord to update.

        Returns:
            The updated learning record.
        """
        db._learning_records[entity.id] = entity
        return entity

    def delete(self, id: int) -> bool:
        """Delete a learning record by ID.

        Args:
            id: Record ID.

        Returns:
            True if deleted, False if not found.
        """
        if id in db._learning_records:
            del db._learning_records[id]
            return True
        return False


class LearningSessionRepository(BaseRepository[LearningSession, str]):
    """Repository for LearningSession entities using in-memory storage."""

    def get_by_id(self, id: str) -> Optional[LearningSession]:
        """Get a learning session by ID.

        Args:
            id: Session ID.

        Returns:
            LearningSession if found, None otherwise.
        """
        return db._learning_sessions.get(id)

    def get_active_by_student(
        self, student_id: int, course_id: str, kp_id: Optional[str] = None
    ) -> Optional[LearningSession]:
        """Get the active learning session for a student in a course.

        Args:
            student_id: Student ID.
            course_id: Course ID.
            kp_id: Optional knowledge point ID to further scope the lookup.

        Returns:
            Active LearningSession if found, None otherwise.
        """
        for session in db._learning_sessions.values():
            if (
                session.student_id == student_id
                and session.course_id == course_id
                and session.status == SessionStatus.ACTIVE
            ):
                if kp_id is None or session.kp_id == kp_id:
                    return session
        return None

    def get_by_student(self, student_id: int) -> list[LearningSession]:
        """Get all learning sessions for a student.

        Args:
            student_id: Student ID.

        Returns:
            List of learning sessions for the student.
        """
        return [
            session
            for session in db._learning_sessions.values()
            if session.student_id == student_id
        ]

    def get_all(self) -> list[LearningSession]:
        """Get all learning sessions.

        Returns:
            List of all learning sessions.
        """
        return list(db._learning_sessions.values())

    def create(self, entity: LearningSession) -> LearningSession:
        """Create a new learning session.

        Args:
            entity: LearningSession to create.

        Returns:
            The created learning session.
        """
        if not entity.id:
            entity.id = f"SESSION_{uuid.uuid4().hex[:8].upper()}"
        db._learning_sessions[entity.id] = entity
        db.save_learning_sessions_to_file()
        return entity

    def update(self, entity: LearningSession) -> LearningSession:
        """Update an existing learning session.

        Args:
            entity: LearningSession to update.

        Returns:
            The updated learning session.
        """
        db._learning_sessions[entity.id] = entity
        db.save_learning_sessions_to_file()
        return entity

    def delete(self, id: str) -> bool:
        """Delete a learning session by ID.

        Args:
            id: Session ID.

        Returns:
            True if deleted, False if not found.
        """
        if id in db._learning_sessions:
            del db._learning_sessions[id]
            db.save_learning_sessions_to_file()
            return True
        return False


# Global repository instances
student_profile_repository = StudentProfileRepository()
learning_record_repository = LearningRecordRepository()
learning_session_repository = LearningSessionRepository()
