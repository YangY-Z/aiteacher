"""Resource repositories for teaching materials."""

import logging
from datetime import datetime
from typing import Optional
import uuid

from app.models.resource import (
    TeachingImage,
    ImageTemplate,
    TeachingVideo,
    InteractiveDemo,
    ToolUsageLog,
    ImageType,
    ImageStatus,
    ResourceType,
)
from app.repositories.base import BaseRepository
from app.repositories.memory_db import db
from app.services.tools.protocols import (
    ImageRepositoryProtocol,
    UsageLogRepositoryProtocol,
)

logger = logging.getLogger(__name__)


class TeachingImageRepository(
    BaseRepository[TeachingImage, str],
    ImageRepositoryProtocol
):
    """Repository for teaching images using in-memory storage."""
    
    def __init__(self):
        """Initialize the repository."""
        if not hasattr(db, "_teaching_images"):
            db._teaching_images = {}
        self._images = db._teaching_images
    
    def get_by_id(self, id: str) -> Optional[TeachingImage]:
        """Get an image by ID.
        
        Args:
            id: Image ID.
            
        Returns:
            TeachingImage if found, None otherwise.
        """
        return self._images.get(id)
    
    def get_by_knowledge_point(
        self, 
        knowledge_point_id: str,
        image_type: Optional[ImageType] = None,
        limit: int = 10
    ) -> list[TeachingImage]:
        """Get images for a knowledge point.
        
        Args:
            knowledge_point_id: Knowledge point ID.
            image_type: Optional filter by image type.
            limit: Maximum number of images to return.
            
        Returns:
            List of teaching images.
        """
        images = []
        for img in self._images.values():
            if img.knowledge_point_id == knowledge_point_id:
                if image_type is None or img.image_type == image_type:
                    if img.status == ImageStatus.READY:
                        images.append(img)
        
        # Sort by usage count and rating
        images.sort(key=lambda x: (x.usage_count, x.rating), reverse=True)
        return images[:limit]
    
    def search_by_tags(
        self,
        tags: list[str],
        knowledge_point_id: Optional[str] = None,
        limit: int = 10
    ) -> list[TeachingImage]:
        """Search images by tags.
        
        Args:
            tags: Tags to search for.
            knowledge_point_id: Optional filter by knowledge point.
            limit: Maximum number of images to return.
            
        Returns:
            List of matching images.
        """
        images = []
        for img in self._images.values():
            # Check if any tag matches
            if any(tag in img.tags for tag in tags):
                # Filter by knowledge point if provided
                if knowledge_point_id is None or img.knowledge_point_id == knowledge_point_id:
                    if img.status == ImageStatus.READY:
                        images.append(img)
        
        images.sort(key=lambda x: (x.usage_count, x.rating), reverse=True)
        return images[:limit]
    
    def create(self, entity: TeachingImage) -> TeachingImage:
        """Create a new image.
        
        Args:
            entity: Image to create.
            
        Returns:
            Created image.
        """
        if not entity.id:
            entity.id = str(uuid.uuid4())
        entity.created_at = datetime.now()
        entity.updated_at = datetime.now()
        self._images[entity.id] = entity
        logger.info(f"Created image: {entity.id} - {entity.title}")
        return entity
    
    def update(self, entity: TeachingImage) -> TeachingImage:
        """Update an existing image.
        
        Args:
            entity: Image to update.
            
        Returns:
            Updated image.
        """
        entity.updated_at = datetime.now()
        self._images[entity.id] = entity
        logger.info(f"Updated image: {entity.id}")
        return entity
    
    def increment_usage(self, id: str) -> None:
        """Increment usage count for an image.
        
        Args:
            id: Image ID.
        """
        if id in self._images:
            self._images[id].usage_count += 1
            self._images[id].updated_at = datetime.now()
    
    def get_all(self) -> list[TeachingImage]:
        """Get all images.
        
        Returns:
            List of all images.
        """
        return list(self._images.values())
    
    def delete(self, id: str) -> bool:
        """Delete an image.
        
        Args:
            id: Image ID.
            
        Returns:
            True if deleted, False if not found.
        """
        if id in self._images:
            del self._images[id]
            logger.info(f"Deleted image: {id}")
            return True
        return False


class ImageTemplateRepository(BaseRepository[ImageTemplate, str]):
    """Repository for image templates."""
    
    def __init__(self):
        """Initialize the repository."""
        if not hasattr(db, "_image_templates"):
            db._image_templates = {}
        self._templates = db._image_templates
    
    def get_by_id(self, id: str) -> Optional[ImageTemplate]:
        """Get a template by ID."""
        return self._templates.get(id)
    
    def find_template(
        self,
        concept: str,
        template_type: Optional[ImageType] = None
    ) -> Optional[ImageTemplate]:
        """Find a suitable template for a concept.
        
        Args:
            concept: Concept description.
            template_type: Optional filter by type.
            
        Returns:
            Matching template if found.
        """
        # Simple keyword matching for now
        # Can be enhanced with vector search later
        for template in self._templates.values():
            if template_type and template.template_type != template_type:
                continue
            
            # Check if concept keywords match template name/description
            if any(keyword in concept for keyword in template.name.lower().split()):
                return template
        
        return None
    
    def create(self, entity: ImageTemplate) -> ImageTemplate:
        """Create a new template."""
        if not entity.id:
            entity.id = str(uuid.uuid4())
        entity.created_at = datetime.now()
        self._templates[entity.id] = entity
        logger.info(f"Created template: {entity.id} - {entity.name}")
        return entity
    
    def get_all(self) -> list[ImageTemplate]:
        """Get all templates."""
        return list(self._templates.values())
    
    def update(self, entity: ImageTemplate) -> ImageTemplate:
        """Update an existing template.
        
        Args:
            entity: Template to update.
            
        Returns:
            Updated template.
        """
        self._templates[entity.id] = entity
        logger.info(f"Updated template: {entity.id}")
        return entity
    
    def delete(self, id: str) -> bool:
        """Delete a template.
        
        Args:
            id: Template ID.
            
        Returns:
            True if deleted, False if not found.
        """
        if id in self._templates:
            del self._templates[id]
            logger.info(f"Deleted template: {id}")
            return True
        return False


class ToolUsageLogRepository(
    BaseRepository[ToolUsageLog, str],
    UsageLogRepositoryProtocol
):
    """Repository for tool usage logs."""
    
    def __init__(self):
        """Initialize the repository."""
        if not hasattr(db, "_tool_usage_logs"):
            db._tool_usage_logs = []
        self._logs = db._tool_usage_logs
    
    def get_by_id(self, id: str) -> Optional[ToolUsageLog]:
        """Get a log by ID."""
        for log in self._logs:
            if log.id == id:
                return log
        return None
    
    def create(self, entity: ToolUsageLog) -> ToolUsageLog:
        """Create a new log entry."""
        if not entity.id:
            entity.id = str(uuid.uuid4())
        entity.created_at = datetime.now()
        self._logs.append(entity)
        return entity
    
    def get_all(self) -> list[ToolUsageLog]:
        """Get all logs."""
        return list(self._logs)
    
    def get_by_knowledge_point(self, knowledge_point_id: str, limit: int = 100) -> list[ToolUsageLog]:
        """Get logs for a knowledge point."""
        logs = [log for log in self._logs if log.knowledge_point_id == knowledge_point_id]
        logs.sort(key=lambda x: x.created_at, reverse=True)
        return logs[:limit]
    
    def update(self, entity: ToolUsageLog) -> ToolUsageLog:
        """Update an existing log entry.
        
        Args:
            entity: Log entry to update.
            
        Returns:
            Updated log entry.
        """
        for i, log in enumerate(self._logs):
            if log.id == entity.id:
                self._logs[i] = entity
                logger.info(f"Updated log: {entity.id}")
                return entity
        raise ValueError(f"Log not found: {entity.id}")
    
    def delete(self, id: str) -> bool:
        """Delete a log entry.
        
        Args:
            id: Log ID.
            
        Returns:
            True if deleted, False if not found.
        """
        for i, log in enumerate(self._logs):
            if log.id == id:
                del self._logs[i]
                logger.info(f"Deleted log: {id}")
                return True
        return False


# Global instances
teaching_image_repository = TeachingImageRepository()
image_template_repository = ImageTemplateRepository()
tool_usage_log_repository = ToolUsageLogRepository()
