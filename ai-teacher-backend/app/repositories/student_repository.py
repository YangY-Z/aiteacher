"""Student repository implementation."""

from typing import Optional

from app.models.student import Student
from app.repositories.base import BaseRepository
from app.repositories.memory_db import db


class StudentRepository(BaseRepository[Student, int]):
    """Repository for Student entities using in-memory storage."""

    def get_by_id(self, id: int) -> Optional[Student]:
        """Get a student by ID.

        Args:
            id: Student ID.

        Returns:
            Student if found, None otherwise.
        """
        return db._students.get(id)

    def get_by_phone(self, phone: str) -> Optional[Student]:
        """Get a student by phone number.

        Args:
            phone: Phone number.

        Returns:
            Student if found, None otherwise.
        """
        for student in db._students.values():
            if student.phone == phone:
                return student
        return None

    def get_all(self) -> list[Student]:
        """Get all students.

        Returns:
            List of all students.
        """
        return list(db._students.values())

    def create(self, entity: Student) -> Student:
        """Create a new student.

        Args:
            entity: Student to create.

        Returns:
            The created student.
        """
        if entity.id is None or entity.id == 0:
            entity.id = db.get_next_student_id()
        db._students[entity.id] = entity
        db.save_student_data()
        return entity

    def update(self, entity: Student) -> Student:
        """Update an existing student.

        Args:
            entity: Student to update.

        Returns:
            The updated student.
        """
        db._students[entity.id] = entity
        db.save_student_data()
        return entity

    def delete(self, id: int) -> bool:
        """Delete a student by ID.

        Args:
            id: Student ID.

        Returns:
            True if deleted, False if not found.
        """
        if id in db._students:
            del db._students[id]
            db.save_student_data()
            return True
        return False


# Global repository instance
student_repository = StudentRepository()
