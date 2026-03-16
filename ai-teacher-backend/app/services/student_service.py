"""Student service for student-related business logic."""

from typing import Optional

from app.core.exceptions import (
    AuthenticationError,
    DuplicateEntityError,
    EntityNotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.student import Student, Grade, StudentStatus
from app.repositories.student_repository import student_repository


class StudentService:
    """Service for student-related business logic."""

    def register(
        self,
        name: str,
        grade: str,
        phone: str,
        password: str,
    ) -> Student:
        """Register a new student.

        Args:
            name: Student name.
            grade: Student grade.
            phone: Phone number.
            password: Plain text password.

        Returns:
            Created student.

        Raises:
            DuplicateEntityError: If phone number already exists.
        """
        # Check if phone already exists
        existing = student_repository.get_by_phone(phone)
        if existing:
            raise DuplicateEntityError("学生", "phone", phone)

        # Create student
        student = Student(
            id=0,
            name=name,
            grade=Grade(grade),
            phone=phone,
            password_hash=hash_password(password),
            status=StudentStatus.ACTIVE,
        )

        return student_repository.create(student)

    def login(self, phone: str, password: str) -> dict[str, str]:
        """Authenticate a student and return a token.

        Args:
            phone: Phone number.
            password: Plain text password.

        Returns:
            Dict with access token and student info.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        student = student_repository.get_by_phone(phone)

        if not student:
            raise AuthenticationError("手机号或密码错误")

        if not verify_password(password, student.password_hash):
            raise AuthenticationError("手机号或密码错误")

        if not student.is_active():
            raise AuthenticationError("账户已被禁用")

        # Update last login
        student.update_last_login()
        student_repository.update(student)

        # Create token
        token = create_access_token({"sub": student.id})

        return {
            "access_token": token,
            "token_type": "bearer",
            "student_id": student.id,
            "student_name": student.name,
        }

    def get_by_id(self, student_id: int) -> Student:
        """Get a student by ID.

        Args:
            student_id: Student ID.

        Returns:
            Student.

        Raises:
            EntityNotFoundError: If student not found.
        """
        student = student_repository.get_by_id(student_id)
        if not student:
            raise EntityNotFoundError("学生", str(student_id))
        return student

    def get_by_phone(self, phone: str) -> Optional[Student]:
        """Get a student by phone number.

        Args:
            phone: Phone number.

        Returns:
            Student if found, None otherwise.
        """
        return student_repository.get_by_phone(phone)


# Global service instance
student_service = StudentService()
