"""Grade repository for data persistence."""

import json
import logging
from pathlib import Path
from typing import Optional

from app.models import Grade, GradeSubject, GradeLevel, Status
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class GradeRepository(BaseRepository[Grade, str]):
    """Repository for Grade entities.

    Manages persistence of Grade aggregates including GradeSubject associations.
    """

    def __init__(self, data_file: str = "data/grades.json"):
        """Initialize the repository.

        Args:
            data_file: Path to the JSON file for persistence.
        """
        self._data_file = data_file
        self._grades: dict[str, Grade] = {}
        self._load_from_file()

    def _get_data_file_path(self) -> Path:
        """Get the absolute path to the data file.

        Returns:
            Path to the data file.
        """
        project_root = Path(__file__).parent.parent.parent
        return project_root / self._data_file

    def _load_from_file(self) -> None:
        """Load grades from JSON file."""
        file_path = self._get_data_file_path()

        if not file_path.exists():
            logger.debug(f"Grade data file not found: {file_path}")
            self._initialize_seed_data()
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for grade_dict in data.get("grades", []):
                grade = Grade.from_dict(grade_dict)
                self._grades[grade.id] = grade

            logger.info(f"Loaded {len(self._grades)} grades from {file_path}")

        except Exception as e:
            logger.error(f"Failed to load grades from file: {e}")
            self._initialize_seed_data()

    def _save_to_file(self) -> None:
        """Save grades to JSON file."""
        file_path = self._get_data_file_path()

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            grades_data = [grade.to_dict() for grade in self._grades.values()]

            data = {
                "grades": grades_data,
                "updated_at": datetime.now().isoformat(),
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(grades_data)} grades to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save grades to file: {e}")

    def _initialize_seed_data(self) -> None:
        """Initialize with seed data."""
        from datetime import datetime

        seed_grades = [
            Grade(
                id="G_C1",
                name="初一",
                code="C1",
                level=GradeLevel.MIDDLE,
                sort_order=1,
                description="初中一年级",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Grade(
                id="G_C2",
                name="初二",
                code="C2",
                level=GradeLevel.MIDDLE,
                sort_order=2,
                description="初中二年级",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Grade(
                id="G_C3",
                name="初三",
                code="C3",
                level=GradeLevel.MIDDLE,
                sort_order=3,
                description="初中三年级",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Grade(
                id="G_S1",
                name="高一",
                code="S1",
                level=GradeLevel.HIGH,
                sort_order=4,
                description="高中一年级",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Grade(
                id="G_S2",
                name="高二",
                code="S2",
                level=GradeLevel.HIGH,
                sort_order=5,
                description="高中二年级",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Grade(
                id="G_S3",
                name="高三",
                code="S3",
                level=GradeLevel.HIGH,
                sort_order=6,
                description="高中三年级",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        for grade in seed_grades:
            self._grades[grade.id] = grade

        self._save_to_file()
        logger.info("Initialized seed data for grades")

    def get_by_id(self, id: str) -> Optional[Grade]:
        """Get a grade by its ID.

        Args:
            id: Grade identifier.

        Returns:
            Grade if found, None otherwise.
        """
        return self._grades.get(id)

    def get_all(self) -> list[Grade]:
        """Get all grades.

        Returns:
            List of all grades.
        """
        return sorted(self._grades.values(), key=lambda g: g.sort_order)

    def create(self, entity: Grade) -> Grade:
        """Create a new grade.

        Args:
            entity: Grade to create.

        Returns:
            The created grade.

        Raises:
            ValueError: If grade with same ID or name already exists.
        """
        # Check for duplicate ID
        if entity.id in self._grades:
            raise ValueError(f"Grade with id '{entity.id}' already exists")

        # Check for duplicate name
        if any(g.name == entity.name for g in self._grades.values()):
            raise ValueError(f"Grade with name '{entity.name}' already exists")

        self._grades[entity.id] = entity
        self._save_to_file()
        return entity

    def update(self, entity: Grade) -> Grade:
        """Update an existing grade.

        Args:
            entity: Grade to update.

        Returns:
            The updated grade.

        Raises:
            ValueError: If grade not found or name conflict.
        """
        if entity.id not in self._grades:
            raise ValueError(f"Grade with id '{entity.id}' not found")

        # Check for name conflict (excluding self)
        for grade in self._grades.values():
            if grade.id != entity.id and grade.name == entity.name:
                raise ValueError(f"Grade with name '{entity.name}' already exists")

        self._grades[entity.id] = entity
        self._save_to_file()
        return entity

    def delete(self, id: str) -> bool:
        """Delete a grade by its ID.

        Args:
            id: Grade identifier.

        Returns:
            True if deleted, False if not found.
        """
        if id not in self._grades:
            return False

        del self._grades[id]
        self._save_to_file()
        return True

    def add_subject_to_grade(self, grade_id: str, subject_id: str, sort_order: int = 0) -> GradeSubject:
        """Add a subject to a grade.

        Args:
            grade_id: ID of the grade.
            subject_id: ID of the subject.
            sort_order: Display order.

        Returns:
            The created GradeSubject association.

        Raises:
            ValueError: If grade not found or subject already added.
        """
        grade = self.get_by_id(grade_id)
        if not grade:
            raise ValueError(f"Grade with id '{grade_id}' not found")

        # Check if subject already added
        if any(s.subject_id == subject_id for s in grade.subjects):
            raise ValueError(f"Subject '{subject_id}' already added to grade '{grade_id}'")

        association = grade.add_subject(subject_id, sort_order)
        self._save_to_file()
        return association

    def remove_subject_from_grade(self, grade_id: str, subject_id: str) -> bool:
        """Remove a subject from a grade.

        Args:
            grade_id: ID of the grade.
            subject_id: ID of the subject.

        Returns:
            True if removed, False if not found.

        Raises:
            ValueError: If grade not found.
        """
        grade = self.get_by_id(grade_id)
        if not grade:
            raise ValueError(f"Grade with id '{grade_id}' not found")

        removed = grade.remove_subject(subject_id)
        if removed:
            self._save_to_file()
        return removed

    def get_grades_by_level(self, level: GradeLevel) -> list[Grade]:
        """Get grades by level.

        Args:
            level: Grade level to filter by.

        Returns:
            List of grades with the specified level.
        """
        return [g for g in self.get_all() if g.level == level]

    def get_active_grades(self) -> list[Grade]:
        """Get all active grades.

        Returns:
            List of active grades.
        """
        return [g for g in self.get_all() if g.status == Status.ACTIVE]


# Import datetime for seed data
from datetime import datetime

# Global repository instance
grade_repository = GradeRepository()
