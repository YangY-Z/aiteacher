"""Subject domain service."""

import logging
from datetime import datetime
from typing import Optional

from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.models import Subject, SubjectCategory, Status
from app.repositories.subject_repository import subject_repository

logger = logging.getLogger(__name__)


class SubjectService:
    """Subject domain service.

    Provides business logic for subject management operations.
    """

    def __init__(self):
        """Initialize the service with repository."""
        self.subject_repo = subject_repository

    def create_subject(
        self,
        name: str,
        code: str,
        category: SubjectCategory,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        sort_order: int = 0,
        description: Optional[str] = None,
    ) -> Subject:
        """Create a new subject.

        Args:
            name: Subject name.
            code: Subject code.
            category: Subject category.
            icon: Optional icon.
            color: Optional theme color.
            sort_order: Display order.
            description: Optional description.

        Returns:
            The created subject.

        Raises:
            DuplicateEntityError: If subject with same name already exists.
        """
        # Check for duplicate name
        existing_subjects = self.subject_repo.get_all()
        if any(s.name == name for s in existing_subjects):
            raise DuplicateEntityError(
                entity_type="Subject",
                field="name",
                value=name,
            )

        # Generate ID
        subject_id = f"S_{code}"

        # Create subject
        subject = Subject(
            id=subject_id,
            name=name,
            code=code,
            category=category,
            icon=icon,
            color=color,
            sort_order=sort_order,
            description=description,
            status=Status.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        return self.subject_repo.create(subject)

    def update_subject(
        self,
        subject_id: str,
        name: Optional[str] = None,
        category: Optional[SubjectCategory] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        sort_order: Optional[int] = None,
        description: Optional[str] = None,
        status: Optional[Status] = None,
    ) -> Subject:
        """Update a subject.

        Args:
            subject_id: Subject ID.
            name: New name (optional).
            category: New category (optional).
            icon: New icon (optional).
            color: New color (optional).
            sort_order: New sort order (optional).
            description: New description (optional).
            status: New status (optional).

        Returns:
            The updated subject.

        Raises:
            EntityNotFoundError: If subject not found.
            DuplicateEntityError: If name conflict.
        """
        subject = self.subject_repo.get_by_id(subject_id)
        if not subject:
            raise EntityNotFoundError(entity_type="Subject", entity_id=subject_id)

        # Check for name conflict
        if name and name != subject.name:
            existing_subjects = self.subject_repo.get_all()
            if any(s.id != subject_id and s.name == name for s in existing_subjects):
                raise DuplicateEntityError(
                    entity_type="Subject",
                    field="name",
                    value=name,
                )
            subject.name = name

        # Update fields
        if category is not None:
            subject.category = category
        if icon is not None:
            subject.icon = icon
        if color is not None:
            subject.color = color
        if sort_order is not None:
            subject.sort_order = sort_order
        if description is not None:
            subject.description = description
        if status is not None:
            subject.status = status

        subject.updated_at = datetime.now()

        return self.subject_repo.update(subject)

    def delete_subject(self, subject_id: str) -> bool:
        """Delete a subject.

        Args:
            subject_id: Subject ID.

        Returns:
            True if deleted.

        Raises:
            EntityNotFoundError: If subject not found.
            ValidationError: If subject has associated chapters.
        """
        subject = self.subject_repo.get_by_id(subject_id)
        if not subject:
            raise EntityNotFoundError(entity_type="Subject", entity_id=subject_id)

        # TODO: Check if subject has associated chapters
        # This would require querying the chapter repository

        return self.subject_repo.delete(subject_id)

    def get_subject(self, subject_id: str) -> Subject:
        """Get a subject by ID.

        Args:
            subject_id: Subject ID.

        Returns:
            The subject.

        Raises:
            EntityNotFoundError: If subject not found.
        """
        subject = self.subject_repo.get_by_id(subject_id)
        if not subject:
            raise EntityNotFoundError(entity_type="Subject", entity_id=subject_id)
        return subject

    def get_all_subjects(
        self, category: Optional[SubjectCategory] = None, active_only: bool = False
    ) -> list[Subject]:
        """Get all subjects.

        Args:
            category: Filter by category (optional).
            active_only: Only return active subjects.

        Returns:
            List of subjects.
        """
        if category:
            subjects = self.subject_repo.get_subjects_by_category(category)
        else:
            subjects = self.subject_repo.get_all()

        if active_only:
            subjects = [s for s in subjects if s.status == Status.ACTIVE]

        return subjects


# Global service instance
subject_service = SubjectService()
