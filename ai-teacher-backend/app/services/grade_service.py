"""Grade domain service."""

import logging
from datetime import datetime
from typing import Optional

from app.core.exceptions import DuplicateEntityError, EntityNotFoundError, ValidationError
from app.models import Grade, GradeSubject, GradeLevel, Status
from app.repositories.grade_repository import grade_repository
from app.repositories.subject_repository import subject_repository

logger = logging.getLogger(__name__)


class GradeService:
    """Grade domain service.

    Provides business logic for grade management operations.
    """

    def __init__(self):
        """Initialize the service with repositories."""
        self.grade_repo = grade_repository
        self.subject_repo = subject_repository

    def create_grade(
        self,
        name: str,
        code: str,
        level: GradeLevel,
        sort_order: int = 0,
        description: Optional[str] = None,
    ) -> Grade:
        """Create a new grade.

        Args:
            name: Grade name.
            code: Grade code.
            level: Grade level.
            sort_order: Display order.
            description: Optional description.

        Returns:
            The created grade.

        Raises:
            DuplicateEntityError: If grade with same name already exists.
        """
        # Check for duplicate name
        existing_grades = self.grade_repo.get_all()
        if any(g.name == name for g in existing_grades):
            raise DuplicateEntityError(
                entity_type="Grade",
                field="name",
                value=name,
            )

        # Generate ID
        grade_id = f"G_{code}"

        # Create grade
        grade = Grade(
            id=grade_id,
            name=name,
            code=code,
            level=level,
            sort_order=sort_order,
            description=description,
            status=Status.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        return self.grade_repo.create(grade)

    def update_grade(
        self,
        grade_id: str,
        name: Optional[str] = None,
        level: Optional[GradeLevel] = None,
        sort_order: Optional[int] = None,
        description: Optional[str] = None,
        status: Optional[Status] = None,
    ) -> Grade:
        """Update a grade.

        Args:
            grade_id: Grade ID.
            name: New name (optional).
            level: New level (optional).
            sort_order: New sort order (optional).
            description: New description (optional).
            status: New status (optional).

        Returns:
            The updated grade.

        Raises:
            EntityNotFoundError: If grade not found.
            DuplicateEntityError: If name conflict.
        """
        grade = self.grade_repo.get_by_id(grade_id)
        if not grade:
            raise EntityNotFoundError(entity_type="Grade", entity_id=grade_id)

        # Check for name conflict
        if name and name != grade.name:
            existing_grades = self.grade_repo.get_all()
            if any(g.id != grade_id and g.name == name for g in existing_grades):
                raise DuplicateEntityError(
                    entity_type="Grade",
                    field="name",
                    value=name,
                )
            grade.name = name

        # Update fields
        if level is not None:
            grade.level = level
        if sort_order is not None:
            grade.sort_order = sort_order
        if description is not None:
            grade.description = description
        if status is not None:
            grade.status = status

        grade.updated_at = datetime.now()

        return self.grade_repo.update(grade)

    def delete_grade(self, grade_id: str) -> bool:
        """Delete a grade.

        Args:
            grade_id: Grade ID.

        Returns:
            True if deleted.

        Raises:
            EntityNotFoundError: If grade not found.
            ValidationError: If grade has associated chapters.
        """
        grade = self.grade_repo.get_by_id(grade_id)
        if not grade:
            raise EntityNotFoundError(entity_type="Grade", entity_id=grade_id)

        # TODO: Check if grade has associated chapters
        # This would require querying the chapter repository

        return self.grade_repo.delete(grade_id)

    def get_grade(self, grade_id: str) -> Grade:
        """Get a grade by ID.

        Args:
            grade_id: Grade ID.

        Returns:
            The grade.

        Raises:
            EntityNotFoundError: If grade not found.
        """
        grade = self.grade_repo.get_by_id(grade_id)
        if not grade:
            raise EntityNotFoundError(entity_type="Grade", entity_id=grade_id)
        return grade

    def get_all_grades(self, level: Optional[GradeLevel] = None, active_only: bool = False) -> list[Grade]:
        """Get all grades.

        Args:
            level: Filter by level (optional).
            active_only: Only return active grades.

        Returns:
            List of grades.
        """
        if level:
            grades = self.grade_repo.get_grades_by_level(level)
        else:
            grades = self.grade_repo.get_all()

        if active_only:
            grades = [g for g in grades if g.status == Status.ACTIVE]

        return grades

    def add_subject_to_grade(
        self,
        grade_id: str,
        subject_id: str,
        sort_order: int = 0,
    ) -> GradeSubject:
        """Add a subject to a grade.

        Args:
            grade_id: Grade ID.
            subject_id: Subject ID.
            sort_order: Display order.

        Returns:
            The created association.

        Raises:
            EntityNotFoundError: If grade or subject not found.
            ValidationError: If subject already added.
        """
        # Validate grade exists
        grade = self.grade_repo.get_by_id(grade_id)
        if not grade:
            raise EntityNotFoundError(entity_type="Grade", entity_id=grade_id)

        # Validate subject exists
        subject = self.subject_repo.get_by_id(subject_id)
        if not subject:
            raise EntityNotFoundError(entity_type="Subject", entity_id=subject_id)

        # Check if subject already added
        if any(s.subject_id == subject_id for s in grade.subjects):
            raise ValidationError(
                message=f"Subject '{subject_id}' already added to grade '{grade_id}'",
                details={"grade_id": grade_id, "subject_id": subject_id},
            )

        return self.grade_repo.add_subject_to_grade(grade_id, subject_id, sort_order)

    def remove_subject_from_grade(self, grade_id: str, subject_id: str) -> bool:
        """Remove a subject from a grade.

        Args:
            grade_id: Grade ID.
            subject_id: Subject ID.

        Returns:
            True if removed.

        Raises:
            EntityNotFoundError: If grade not found.
            ValidationError: If subject has associated chapters.
        """
        # Validate grade exists
        grade = self.grade_repo.get_by_id(grade_id)
        if not grade:
            raise EntityNotFoundError(entity_type="Grade", entity_id=grade_id)

        # TODO: Check if subject has associated chapters in this grade

        return self.grade_repo.remove_subject_from_grade(grade_id, subject_id)

    def update_subject_order_in_grade(self, grade_id: str, subject_id: str, new_order: int) -> Grade:
        """Update the sort order of a subject in a grade.

        Args:
            grade_id: Grade ID.
            subject_id: Subject ID.
            new_order: New sort order.

        Returns:
            The updated grade.

        Raises:
            EntityNotFoundError: If grade or subject association not found.
        """
        grade = self.grade_repo.get_by_id(grade_id)
        if not grade:
            raise EntityNotFoundError(entity_type="Grade", entity_id=grade_id)

        # Find the subject association
        for subject in grade.subjects:
            if subject.subject_id == subject_id:
                subject.sort_order = new_order
                subject.updated_at = datetime.now()
                grade.updated_at = datetime.now()
                return self.grade_repo.update(grade)

        raise EntityNotFoundError(
            entity_type="GradeSubject",
            entity_id=f"{grade_id}/{subject_id}",
        )

    def get_grade_subjects(self, grade_id: str) -> list[GradeSubject]:
        """Get all subjects in a grade.

        Args:
            grade_id: Grade ID.

        Returns:
            List of grade-subject associations.

        Raises:
            EntityNotFoundError: If grade not found.
        """
        grade = self.grade_repo.get_by_id(grade_id)
        if not grade:
            raise EntityNotFoundError(entity_type="Grade", entity_id=grade_id)

        return sorted(grade.subjects, key=lambda s: s.sort_order)


# Global service instance
grade_service = GradeService()
