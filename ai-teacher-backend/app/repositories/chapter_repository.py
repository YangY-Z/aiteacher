"""Chapter repository for data persistence."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models.course import Chapter, Edition, Subject, CourseStatus
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ChapterRepository(BaseRepository[Chapter, str]):
    """Repository for Chapter entities.

    Manages persistence of Chapter aggregates.
    """

    def __init__(self, data_file: str = "data/chapters.json"):
        """Initialize the repository.

        Args:
            data_file: Path to the JSON file for persistence.
        """
        self._data_file = data_file
        self._chapters: dict[str, Chapter] = {}
        self._load_from_file()

    def _get_data_file_path(self) -> Path:
        """Get the absolute path to the data file.

        Returns:
            Path to the data file.
        """
        project_root = Path(__file__).parent.parent.parent
        return project_root / self._data_file

    def _load_from_file(self) -> None:
        """Load chapters from JSON file."""
        file_path = self._get_data_file_path()

        if not file_path.exists():
            logger.debug(f"Chapter data file not found: {file_path}")
            # Try to load from existing in-memory database
            self._load_from_memory_db()
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for chapter_dict in data.get("chapters", []):
                chapter = Chapter(
                    id=chapter_dict["id"],
                    name=chapter_dict["name"],
                    grade=chapter_dict.get("grade", ""),
                    edition=Edition(chapter_dict.get("edition", "人教版")),
                    subject=Subject(chapter_dict.get("subject", "数学")),
                    grade_id=chapter_dict.get("grade_id"),
                    subject_id=chapter_dict.get("subject_id"),
                    description=chapter_dict.get("description"),
                    sort_order=chapter_dict.get("sort_order", 0),
                    total_knowledge_points=chapter_dict.get("total_knowledge_points", 0),
                    estimated_hours=chapter_dict.get("estimated_hours"),
                    level_descriptions=chapter_dict.get("level_descriptions", {}),
                    status=CourseStatus(chapter_dict.get("status", "active")),
                    created_at=datetime.fromisoformat(chapter_dict["created_at"]),
                    updated_at=datetime.fromisoformat(chapter_dict["updated_at"]),
                )
                self._chapters[chapter.id] = chapter

            logger.info(f"Loaded {len(self._chapters)} chapters from {file_path}")

        except Exception as e:
            logger.error(f"Failed to load chapters from file: {e}")
            self._load_from_memory_db()

    def _load_from_memory_db(self) -> None:
        """Load chapters from in-memory database for migration."""
        from app.repositories.memory_db import db

        for chapter_id, chapter in db._chapters.items():
            self._chapters[chapter_id] = chapter

        if self._chapters:
            logger.info(f"Loaded {len(self._chapters)} chapters from in-memory database")
            self._save_to_file()

    def _save_to_file(self) -> None:
        """Save chapters to JSON file."""
        file_path = self._get_data_file_path()

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            chapters_data = []
            for chapter in self._chapters.values():
                chapters_data.append({
                    "id": chapter.id,
                    "name": chapter.name,
                    "grade": chapter.grade,
                    "edition": chapter.edition.value,
                    "subject": chapter.subject.value,
                    "grade_id": chapter.grade_id,
                    "subject_id": chapter.subject_id,
                    "description": chapter.description,
                    "sort_order": chapter.sort_order,
                    "total_knowledge_points": chapter.total_knowledge_points,
                    "estimated_hours": chapter.estimated_hours,
                    "level_descriptions": chapter.level_descriptions,
                    "status": chapter.status.value,
                    "created_at": chapter.created_at.isoformat(),
                    "updated_at": chapter.updated_at.isoformat(),
                })

            data = {
                "chapters": chapters_data,
                "updated_at": datetime.now().isoformat(),
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(chapters_data)} chapters to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save chapters to file: {e}")

    def get_by_id(self, id: str) -> Optional[Chapter]:
        """Get a chapter by its ID.

        Args:
            id: Chapter identifier.

        Returns:
            Chapter if found, None otherwise.
        """
        return self._chapters.get(id)

    def get_all(self) -> list[Chapter]:
        """Get all chapters.

        Returns:
            List of all chapters.
        """
        return list(self._chapters.values())

    def create(self, entity: Chapter) -> Chapter:
        """Create a new chapter.

        Args:
            entity: Chapter to create.

        Returns:
            The created chapter.

        Raises:
            ValueError: If chapter with same ID already exists.
        """
        if entity.id in self._chapters:
            raise ValueError(f"Chapter with id '{entity.id}' already exists")

        self._chapters[entity.id] = entity
        self._save_to_file()
        return entity

    def update(self, entity: Chapter) -> Chapter:
        """Update an existing chapter.

        Args:
            entity: Chapter to update.

        Returns:
            The updated chapter.

        Raises:
            ValueError: If chapter not found.
        """
        if entity.id not in self._chapters:
            raise ValueError(f"Chapter with id '{entity.id}' not found")

        self._chapters[entity.id] = entity
        self._save_to_file()
        return entity

    def delete(self, id: str) -> bool:
        """Delete a chapter by its ID.

        Args:
            id: Chapter identifier.

        Returns:
            True if deleted, False if not found.
        """
        if id not in self._chapters:
            return False

        del self._chapters[id]
        self._save_to_file()
        return True

    def get_chapters_by_grade(self, grade_id: str) -> list[Chapter]:
        """Get chapters by grade ID.

        Args:
            grade_id: Grade ID to filter by.

        Returns:
            List of chapters for the grade.
        """
        return [c for c in self._chapters.values() if c.grade_id == grade_id]

    def get_chapters_by_subject(self, subject_id: str) -> list[Chapter]:
        """Get chapters by subject ID.

        Args:
            subject_id: Subject ID to filter by.

        Returns:
            List of chapters for the subject.
        """
        return [c for c in self._chapters.values() if c.subject_id == subject_id]

    def get_chapters_by_grade_and_subject(
        self, grade_id: str, subject_id: str
    ) -> list[Chapter]:
        """Get chapters by grade and subject IDs.

        Args:
            grade_id: Grade ID to filter by.
            subject_id: Subject ID to filter by.

        Returns:
            List of chapters for the grade and subject.
        """
        return [
            c
            for c in self._chapters.values()
            if c.grade_id == grade_id and c.subject_id == subject_id
        ]

    def migrate_grade_subject_references(
        self, grade_mapping: dict[str, str], subject_mapping: dict[str, str]
    ) -> int:
        """Migrate grade and subject references from string to IDs.

        Args:
            grade_mapping: Mapping from grade name to grade ID.
            subject_mapping: Mapping from subject name to subject ID.

        Returns:
            Number of chapters updated.
        """
        updated_count = 0

        for chapter in self._chapters.values():
            # Map grade name to ID
            if chapter.grade and not chapter.grade_id:
                if chapter.grade in grade_mapping:
                    chapter.grade_id = grade_mapping[chapter.grade]
                    updated_count += 1

            # Map subject name to ID
            if chapter.subject and not chapter.subject_id:
                subject_name = chapter.subject.value
                if subject_name in subject_mapping:
                    chapter.subject_id = subject_mapping[subject_name]
                    updated_count += 1

        if updated_count > 0:
            self._save_to_file()
            logger.info(f"Migrated {updated_count} grade/subject references")

        return updated_count


# Global repository instance
chapter_repository = ChapterRepository()
