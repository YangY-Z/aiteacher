"""Course service for course-related business logic."""

from typing import Optional

from app.core.exceptions import EntityNotFoundError
from app.models.course import Course, KnowledgePoint
from app.repositories.course_repository import (
    course_repository,
    knowledge_point_repository,
    knowledge_point_dependency_repository,
)


class CourseService:
    """Service for course-related business logic."""

    def get_course(self, course_id: str) -> Course:
        """Get a course by ID with all knowledge points.

        Args:
            course_id: Course ID.

        Returns:
            Course with knowledge points.

        Raises:
            EntityNotFoundError: If course not found.
        """
        course = course_repository.get_by_id(course_id)
        if not course:
            raise EntityNotFoundError("课程", course_id)
        return course

    def get_all_courses(self) -> list[Course]:
        """Get all courses.

        Returns:
            List of all courses.
        """
        return course_repository.get_all()

    def get_knowledge_point(self, kp_id: str) -> KnowledgePoint:
        """Get a knowledge point by ID.

        Args:
            kp_id: Knowledge point ID.

        Returns:
            Knowledge point with dependencies.

        Raises:
            EntityNotFoundError: If knowledge point not found.
        """
        kp = knowledge_point_repository.get_by_id(kp_id)
        if not kp:
            raise EntityNotFoundError("知识点", kp_id)
        return kp

    def get_course_knowledge_points(self, course_id: str) -> list[KnowledgePoint]:
        """Get all knowledge points for a course.

        Args:
            course_id: Course ID.

        Returns:
            List of knowledge points ordered by level and sort order.
        """
        kps = knowledge_point_repository.get_by_course(course_id)
        return sorted(kps, key=lambda x: (x.level, x.sort_order))

    def get_knowledge_point_dependencies(self, kp_id: str) -> list[str]:
        """Get prerequisite knowledge point IDs for a knowledge point.

        Args:
            kp_id: Knowledge point ID.

        Returns:
            List of prerequisite knowledge point IDs.
        """
        return knowledge_point_dependency_repository.get_dependencies(kp_id)

    def get_next_knowledge_point(
        self,
        course_id: str,
        current_kp_id: Optional[str],
        completed_kp_ids: list[str],
    ) -> Optional[KnowledgePoint]:
        """Get the next knowledge point to study.

        Args:
            course_id: Course ID.
            current_kp_id: Current knowledge point ID.
            completed_kp_ids: List of completed knowledge point IDs.

        Returns:
            Next knowledge point to study, or None if all completed.
        """
        all_kps = self.get_course_knowledge_points(course_id)

        # Find the first KP that is not completed
        for kp in all_kps:
            if kp.id not in completed_kp_ids:
                # Check if all prerequisites are completed
                prereqs = self.get_knowledge_point_dependencies(kp.id)
                if all(p in completed_kp_ids for p in prereqs):
                    return kp

        return None

    def get_first_knowledge_point(self, course_id: str) -> KnowledgePoint:
        """Get the first knowledge point for a course.

        Args:
            course_id: Course ID.

        Returns:
            First knowledge point (lowest level, lowest sort order).

        Raises:
            EntityNotFoundError: If no knowledge points found.
        """
        kps = self.get_course_knowledge_points(course_id)
        if not kps:
            raise EntityNotFoundError("知识点", f"course:{course_id}")

        # Get level 0 KPs and return the first one
        level_0_kps = [kp for kp in kps if kp.level == 0]
        if level_0_kps:
            return sorted(level_0_kps, key=lambda x: x.sort_order)[0]

        return kps[0]

    def get_knowledge_point_info(self, kp_id: str) -> dict:
        """Get detailed information about a knowledge point.

        Args:
            kp_id: Knowledge point ID.

        Returns:
            Dict with knowledge point info and dependencies.
        """
        kp = self.get_knowledge_point(kp_id)
        dependencies = self.get_knowledge_point_dependencies(kp_id)

        # Get dependency names
        dep_names = []
        for dep_id in dependencies:
            dep_kp = knowledge_point_repository.get_by_id(dep_id)
            if dep_kp:
                dep_names.append(dep_kp.name)

        return {
            "id": kp.id,
            "name": kp.name,
            "type": kp.type.value,
            "description": kp.description,
            "level": kp.level,
            "dependencies": dependencies,
            "dependency_names": dep_names,
            "mastery_criteria": kp.mastery_criteria.to_dict() if kp.mastery_criteria else None,
            "teaching_config": kp.teaching_config.to_dict() if kp.teaching_config else None,
        }


# Global service instance
course_service = CourseService()
