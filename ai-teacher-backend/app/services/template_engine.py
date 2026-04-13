"""Template engine for rendering teaching images."""

import logging
from typing import Any, Optional

from app.models.resource import ImageTemplate, ImageType
from app.repositories.resource_repository import image_template_repository

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Engine for rendering images from templates."""
    
    def __init__(self):
        """Initialize the template engine."""
        self.template_repo = image_template_repository
    
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
            Matching template if found, None otherwise.
        """
        return self.template_repo.find_template(concept, template_type)
    
    async def render(
        self,
        template: ImageTemplate,
        params: dict[str, Any]
    ) -> dict[str, Any]:
        """Render an image from a template.
        
        Args:
            template: Template to render.
            params: Parameters for rendering.
            
        Returns:
            Rendered image resource info.
        
        Note:
            This is a simplified implementation. In production, this would:
            1. Load the template file (SVG, HTML, or other format)
            2. Substitute variables with params
            3. Convert to image format (PNG/JPEG)
            4. Upload to storage
            5. Return the image URL
        """
        logger.info(f"Rendering template: {template.name} with params: {params}")
        
        # Validate required variables
        missing_vars = []
        for var in template.variables:
            if var not in params:
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"Missing variables for template {template.id}: {missing_vars}")
        
        # Increment usage count
        template.usage_count += 1
        
        # Mock implementation - return a mock image URL
        # In production, this would render the actual template
        return {
            "id": f"rendered_{template.id}",
            "type": "image",
            "url": f"/static/images/rendered/{template.id}.png",
            "thumbnail_url": f"/static/images/rendered/{template.id}_thumb.png",
            "title": template.name,
            "description": template.description,
            "source": "template_rendered",
            "template_id": template.id,
            "render_params": params,
        }
    
    async def render_quick(
        self,
        concept: str,
        template_type: Optional[ImageType] = None,
        params: Optional[dict[str, Any]] = None
    ) -> Optional[dict[str, Any]]:
        """Quick render: find template and render in one call.
        
        Args:
            concept: Concept description.
            template_type: Optional filter by type.
            params: Parameters for rendering.
            
        Returns:
            Rendered image resource info if template found, None otherwise.
        """
        template = self.find_template(concept, template_type)
        if not template:
            logger.info(f"No template found for concept: {concept}")
            return None
        
        params = params or {}
        return await self.render(template, params)


# Global instance
template_engine = TemplateEngine()
