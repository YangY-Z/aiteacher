"""Learner profile repository implementation."""

from typing import Optional

from app.models.learner_profile import LearnerProfile
from app.repositories.base import BaseRepository
from app.repositories.memory_db import db


class LearnerProfileRepository(BaseRepository[LearnerProfile, int]):
    """Repository for LearnerProfile entities using in-memory storage."""

    def get_by_id(self, id: int) -> Optional[LearnerProfile]:
        """Get a learner profile by ID.

        Args:
            id: Learner profile ID.

        Returns:
            LearnerProfile if found, None otherwise.
        """
        return db._learner_profiles.get(id)

    def get_by_student_and_course(
        self, student_id: int, course_id: str
    ) -> Optional[LearnerProfile]:
        """Get a learner profile by student ID and course ID.

        Args:
            student_id: Student ID.
            course_id: Course ID.

        Returns:
            LearnerProfile if found, None otherwise.
        """
        for profile in db._learner_profiles.values():
            if profile.student_id == student_id and profile.course_id == course_id:
                return profile
        return None

    def get_all(self) -> list[LearnerProfile]:
        """Get all learner profiles.

        Returns:
            List of all learner profiles.
        """
        return list(db._learner_profiles.values())

    def get_by_student(self, student_id: int) -> list[LearnerProfile]:
        """Get all learner profiles for a student.

        Args:
            student_id: Student ID.

        Returns:
            List of learner profiles for the student.
        """
        return [
            p for p in db._learner_profiles.values() if p.student_id == student_id
        ]

    def get_by_course(self, course_id: str) -> list[LearnerProfile]:
        """Get all learner profiles for a course.

        Args:
            course_id: Course ID.

        Returns:
            List of learner profiles for the course.
        """
        return [
            p for p in db._learner_profiles.values() if p.course_id == course_id
        ]

    def create(self, entity: LearnerProfile) -> LearnerProfile:
        """Create a new learner profile.

        Args:
            entity: LearnerProfile to create.

        Returns:
            The created learner profile.
        """
        if entity.id is None or entity.id == 0:
            entity.id = db.get_next_learner_profile_id()
        db._learner_profiles[entity.id] = entity
        db.save_learner_profile_data()
        return entity

    def update(self, entity: LearnerProfile) -> LearnerProfile:
        """Update an existing learner profile.

        Args:
            entity: LearnerProfile to update.

        Returns:
            The updated learner profile.
        """
        db._learner_profiles[entity.id] = entity
        db.save_learner_profile_data()
        return entity

    def delete(self, id: int) -> bool:
        """Delete a learner profile by ID.

        Args:
            id: Learner profile ID.

        Returns:
            True if deleted, False if not found.
        """
        if id in db._learner_profiles:
            del db._learner_profiles[id]
            db.save_learner_profile_data()
            return True
        return False

    def upsert_by_student_course(self, entity: LearnerProfile) -> LearnerProfile:
        """Create or update learner profile by student and course.

        Args:
            entity: LearnerProfile to create or update.

        Returns:
            The created or updated learner profile.
        """
        existing = self.get_by_student_and_course(entity.student_id, entity.course_id)
        if existing:
            entity.id = existing.id
            return self.update(entity)
        return self.create(entity)


# Global repository instance
learner_profile_repository = LearnerProfileRepository()
