"""Base repository interface using Protocol pattern."""

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

T = TypeVar("T")
ID = TypeVar("ID")


class BaseRepository(ABC, Generic[T, ID]):
    """Abstract base repository interface.

    Defines the contract for all repository implementations.
    """

    @abstractmethod
    def get_by_id(self, id: ID) -> Optional[T]:
        """Get an entity by its ID.

        Args:
            id: Entity identifier.

        Returns:
            The entity if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_all(self) -> list[T]:
        """Get all entities.

        Returns:
            List of all entities.
        """
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity.

        Args:
            entity: Entity to create.

        Returns:
            The created entity.
        """
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity.

        Args:
            entity: Entity to update.

        Returns:
            The updated entity.
        """
        pass

    @abstractmethod
    def delete(self, id: ID) -> bool:
        """Delete an entity by its ID.

        Args:
            id: Entity identifier.

        Returns:
            True if deleted, False if not found.
        """
        pass
