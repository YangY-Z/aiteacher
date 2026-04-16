"""Protocol for image repository operations.

This module defines the interface for image repository implementations.
"""

from typing import Any, Optional, Protocol


class ImageRepositoryProtocol(Protocol):
    """Protocol for image repository operations.
    
    This interface defines the contract for image repository implementations.
    Any class that implements these methods can be used as an image repository.
    
    Implementations:
        - TeachingImageRepository: In-memory storage implementation
        - DatabaseImageRepository: Database storage implementation (future)
    
    Example:
        >>> class MyImageRepository(ImageRepositoryProtocol):
        ...     def get_by_id(self, image_id: str) -> Optional[Any]:
        ...         return self._images.get(image_id)
        ...
        ...     def get_by_knowledge_point(self, kp_id: str, limit: int = 10) -> list[Any]:
        ...         return [img for img in self._images.values() 
        ...                 if img.knowledge_point_id == kp_id][:limit]
        ...
        ...     def increment_usage(self, image_id: str) -> bool:
        ...         if image_id in self._images:
        ...             self._images[image_id].usage_count += 1
        ...             return True
        ...         return False
    """

    def get_by_id(self, image_id: str) -> Optional[Any]:
        """Get image by ID.
        
        Args:
            image_id: Unique identifier of the image.
        
        Returns:
            Image object if found, None otherwise.
        """
        ...

    def get_by_knowledge_point(
        self, 
        knowledge_point_id: str, 
        limit: int = 10
    ) -> list[Any]:
        """Get images by knowledge point ID.
        
        Args:
            knowledge_point_id: Knowledge point ID to filter by.
            limit: Maximum number of images to return.
        
        Returns:
            List of image objects sorted by usage count and rating.
        """
        ...

    def increment_usage(self, image_id: str) -> bool:
        """Increment usage count for an image.
        
        Args:
            image_id: ID of the image to increment.
        
        Returns:
            True if image exists and count was incremented, False otherwise.
        """
        ...
