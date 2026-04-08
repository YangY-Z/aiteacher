"""Subject repository for data persistence."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models import Subject, SubjectCategory, Status
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class SubjectRepository(BaseRepository[Subject, str]):
    """Repository for Subject entities.

    Manages persistence of Subject aggregates.
    """

    def __init__(self, data_file: str = "data/subjects.json"):
        """Initialize the repository.

        Args:
            data_file: Path to the JSON file for persistence.
        """
        self._data_file = data_file
        self._subjects: dict[str, Subject] = {}
        self._load_from_file()

    def _get_data_file_path(self) -> Path:
        """Get the absolute path to the data file.

        Returns:
            Path to the data file.
        """
        project_root = Path(__file__).parent.parent.parent
        return project_root / self._data_file

    def _load_from_file(self) -> None:
        """Load subjects from JSON file."""
        file_path = self._get_data_file_path()

        if not file_path.exists():
            logger.debug(f"Subject data file not found: {file_path}")
            self._initialize_seed_data()
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for subject_dict in data.get("subjects", []):
                subject = Subject.from_dict(subject_dict)
                self._subjects[subject.id] = subject

            logger.info(f"Loaded {len(self._subjects)} subjects from {file_path}")

        except Exception as e:
            logger.error(f"Failed to load subjects from file: {e}")
            self._initialize_seed_data()

    def _save_to_file(self) -> None:
        """Save subjects to JSON file."""
        file_path = self._get_data_file_path()

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            subjects_data = [subject.to_dict() for subject in self._subjects.values()]

            data = {
                "subjects": subjects_data,
                "updated_at": datetime.now().isoformat(),
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(subjects_data)} subjects to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save subjects to file: {e}")

    def _initialize_seed_data(self) -> None:
        """Initialize with seed data."""
        seed_subjects = [
            Subject(
                id="S_MATH",
                name="数学",
                code="MATH",
                category=SubjectCategory.SCIENCE,
                sort_order=1,
                description="数学科目",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Subject(
                id="S_CHINESE",
                name="语文",
                code="CHINESE",
                category=SubjectCategory.LANGUAGE,
                sort_order=2,
                description="语文科目",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Subject(
                id="S_ENGLISH",
                name="英语",
                code="ENGLISH",
                category=SubjectCategory.LANGUAGE,
                sort_order=3,
                description="英语科目",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Subject(
                id="S_PHYSICS",
                name="物理",
                code="PHYSICS",
                category=SubjectCategory.SCIENCE,
                sort_order=4,
                description="物理科目",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Subject(
                id="S_CHEMISTRY",
                name="化学",
                code="CHEMISTRY",
                category=SubjectCategory.SCIENCE,
                sort_order=5,
                description="化学科目",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        for subject in seed_subjects:
            self._subjects[subject.id] = subject

        self._save_to_file()
        logger.info("Initialized seed data for subjects")

    def get_by_id(self, id: str) -> Optional[Subject]:
        """Get a subject by its ID.

        Args:
            id: Subject identifier.

        Returns:
            Subject if found, None otherwise.
        """
        return self._subjects.get(id)

    def get_all(self) -> list[Subject]:
        """Get all subjects.

        Returns:
            List of all subjects.
        """
        return sorted(self._subjects.values(), key=lambda s: s.sort_order)

    def create(self, entity: Subject) -> Subject:
        """Create a new subject.

        Args:
            entity: Subject to create.

        Returns:
            The created subject.

        Raises:
            ValueError: If subject with same ID or name already exists.
        """
        # Check for duplicate ID
        if entity.id in self._subjects:
            raise ValueError(f"Subject with id '{entity.id}' already exists")

        # Check for duplicate name
        if any(s.name == entity.name for s in self._subjects.values()):
            raise ValueError(f"Subject with name '{entity.name}' already exists")

        self._subjects[entity.id] = entity
        self._save_to_file()
        return entity

    def update(self, entity: Subject) -> Subject:
        """Update an existing subject.

        Args:
            entity: Subject to update.

        Returns:
            The updated subject.

        Raises:
            ValueError: If subject not found or name conflict.
        """
        if entity.id not in self._subjects:
            raise ValueError(f"Subject with id '{entity.id}' not found")

        # Check for name conflict (excluding self)
        for subject in self._subjects.values():
            if subject.id != entity.id and subject.name == entity.name:
                raise ValueError(f"Subject with name '{entity.name}' already exists")

        self._subjects[entity.id] = entity
        self._save_to_file()
        return entity

    def delete(self, id: str) -> bool:
        """Delete a subject by its ID.

        Args:
            id: Subject identifier.

        Returns:
            True if deleted, False if not found.
        """
        if id not in self._subjects:
            return False

        del self._subjects[id]
        self._save_to_file()
        return True

    def get_subjects_by_category(self, category: SubjectCategory) -> list[Subject]:
        """Get subjects by category.

        Args:
            category: Subject category to filter by.

        Returns:
            List of subjects with the specified category.
        """
        return [s for s in self.get_all() if s.category == category]

    def get_active_subjects(self) -> list[Subject]:
        """Get all active subjects.

        Returns:
            List of active subjects.
        """
        return [s for s in self.get_all() if s.status == Status.ACTIVE]


# Global repository instance
subject_repository = SubjectRepository()
