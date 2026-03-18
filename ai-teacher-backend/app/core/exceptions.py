"""Custom exception hierarchy for the application."""

from typing import Any, Optional


class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize application exception.

        Args:
            message: Error message.
            error_code: Unique error code for the exception type.
            details: Additional error details.
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(AppException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "VALIDATION_ERROR", details)


class EntityNotFoundError(AppException):
    """Raised when an entity is not found."""

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        message = f"{entity_type} with id '{entity_id}' not found"
        super().__init__(message, "ENTITY_NOT_FOUND", details)
        self.entity_type = entity_type
        self.entity_id = entity_id


class DuplicateEntityError(AppException):
    """Raised when trying to create a duplicate entity."""

    def __init__(
        self,
        entity_type: str,
        field: str,
        value: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        message = f"{entity_type} with {field}='{value}' already exists"
        super().__init__(message, "DUPLICATE_ENTITY", details)


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class AuthorizationError(AppException):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str = "Authorization failed",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class LLMServiceError(AppException):
    """Raised when LLM service fails."""

    def __init__(
        self,
        message: str = "LLM service error",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "LLM_SERVICE_ERROR", details)


class LearningSessionError(AppException):
    """Raised when learning session operation fails."""

    def __init__(
        self,
        message: str = "Learning session error",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "LEARNING_SESSION_ERROR", details)


class DiagnosticError(AppException):
    """Raised when diagnostic operation fails."""

    def __init__(
        self,
        message: str = "Diagnostic error",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "DIAGNOSTIC_ERROR", details)
