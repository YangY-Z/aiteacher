"""Course repository implementation."""

from typing import Optional

from app.models.course import Course, KnowledgePoint, KnowledgePointDependency
from app.repositories.base import BaseRepository
from app.repositories.memory_db import db


class CourseRepository(BaseRepository[Course, str]):
    """Repository for Course entities using in-memory storage."""

    def get_by_id(self, id: str) -> Optional[Course]:
        """Get a course by ID.

        Args:
            id: Course ID.

        Returns:
            Course if found, None otherwise.
        """
        return db._courses.get(id)

    def get_all(self) -> list[Course]:
        """Get all courses.

        Returns:
            List of all courses.
        """
        return list(db._courses.values())

    def create(self, entity: Course) -> Course:
        """Create a new course.

        Args:
            entity: Course to create.

        Returns:
            The created course.
        """
        db._courses[entity.id] = entity
        return entity

    def update(self, entity: Course) -> Course:
        """Update an existing course.

        Args:
            entity: Course to update.

        Returns:
            The updated course.
        """
        db._courses[entity.id] = entity
        return entity

    def delete(self, id: str) -> bool:
        """Delete a course by ID.

        Args:
            id: Course ID.

        Returns:
            True if deleted, False if not found.
        """
        if id in db._courses:
            del db._courses[id]
            return True
        return False


class KnowledgePointRepository(BaseRepository[KnowledgePoint, str]):
    """Repository for KnowledgePoint entities using in-memory storage."""

    def get_by_id(self, id: str) -> Optional[KnowledgePoint]:
        """Get a knowledge point by ID.

        Args:
            id: Knowledge point ID.

        Returns:
            KnowledgePoint if found, None otherwise.
        """
        return db._knowledge_points.get(id)

    def get_all(self) -> list[KnowledgePoint]:
        """Get all knowledge points.

        Returns:
            List of all knowledge points.
        """
        return list(db._knowledge_points.values())

    def get_by_course(self, course_id: str) -> list[KnowledgePoint]:
        """Get all knowledge points for a course.

        Args:
            course_id: Course ID.

        Returns:
            List of knowledge points for the course.
        """
        return [
            kp
            for kp in db._knowledge_points.values()
            if kp.course_id == course_id
        ]

    def get_by_level(self, course_id: str, level: int) -> list[KnowledgePoint]:
        """Get knowledge points by level.

        Args:
            course_id: Course ID.
            level: Knowledge point level.

        Returns:
            List of knowledge points at the specified level.
        """
        return [
            kp
            for kp in db._knowledge_points.values()
            if kp.course_id == course_id and kp.level == level
        ]

    def create(self, entity: KnowledgePoint) -> KnowledgePoint:
        """Create a new knowledge point.

        Args:
            entity: Knowledge point to create.

        Returns:
            The created knowledge point.
        """
        db._knowledge_points[entity.id] = entity
        return entity

    def update(self, entity: KnowledgePoint) -> KnowledgePoint:
        """Update an existing knowledge point.

        Args:
            entity: Knowledge point to update.

        Returns:
            The updated knowledge point.
        """
        db._knowledge_points[entity.id] = entity
        return entity

    def delete(self, id: str) -> bool:
        """Delete a knowledge point by ID.

        Args:
            id: Knowledge point ID.

        Returns:
            True if deleted, False if not found.
        """
        if id in db._knowledge_points:
            del db._knowledge_points[id]
            return True
        return False


class KnowledgePointDependencyRepository:
    """Repository for KnowledgePointDependency entities."""

    def get_dependencies(self, kp_id: str) -> list[str]:
        """Get all prerequisite knowledge point IDs for a given knowledge point.

        Args:
            kp_id: Knowledge point ID.

        Returns:
            List of prerequisite knowledge point IDs.
        """
        return [
            dep.depends_on_kp_id
            for dep in db._kp_dependencies
            if dep.kp_id == kp_id
        ]

    def get_dependents(self, kp_id: str) -> list[str]:
        """Get all knowledge point IDs that depend on the given knowledge point.

        Args:
            kp_id: Knowledge point ID.

        Returns:
            List of dependent knowledge point IDs.
        """
        return [
            dep.kp_id
            for dep in db._kp_dependencies
            if dep.depends_on_kp_id == kp_id
        ]

    def add_dependency(
        self,
        kp_id: str,
        depends_on_kp_id: str,
        dependency_type: str = "prerequisite",
    ) -> KnowledgePointDependency:
        """Add a dependency relationship.

        Args:
            kp_id: Knowledge point ID.
            depends_on_kp_id: Prerequisite knowledge point ID.
            dependency_type: Type of dependency.

        Returns:
            The created dependency.
        """
        dep = KnowledgePointDependency(
            id=db._kp_dependency_id_counter,
            kp_id=kp_id,
            depends_on_kp_id=depends_on_kp_id,
        )
        db._kp_dependencies.append(dep)
        db._kp_dependency_id_counter += 1
        return dep


# Global repository instances
course_repository = CourseRepository()
knowledge_point_repository = KnowledgePointRepository()
knowledge_point_dependency_repository = KnowledgePointDependencyRepository()
