"""Core module: config, security, exceptions."""

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    ValidationError,
    EntityNotFoundError,
    DuplicateEntityError,
    AuthenticationError,
    AuthorizationError,
)

__all__ = [
    "settings",
    "AppException",
    "ValidationError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "AuthenticationError",
    "AuthorizationError",
]
