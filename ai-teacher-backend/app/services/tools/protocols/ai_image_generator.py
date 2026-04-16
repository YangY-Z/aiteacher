"""Protocol for AI image generator operations.

This module defines the interface for AI image generator implementations.
"""

from typing import Any, Protocol

from app.models.resource import ImageType


class AIImageGeneratorProtocol(Protocol):
    """Protocol for AI image generator operations.
    
    This interface defines the contract for AI-based image generation.
    Any class that implements these methods can be used as an AI image generator.
    
    Implementations:
        - AIImageGenerator: Main implementation using AI service
    
    Example:
        >>> class MyAIImageGenerator(AIImageGeneratorProtocol):
        ...     async def generate_with_retry(
        ...         self,
        ...         concept: str,
        ...         image_type: ImageType,
        ...         params: dict[str, Any],
        ...         max_retries: int = 2
        ...     ) -> dict[str, Any]:
        ...         for attempt in range(max_retries):
        ...             try:
        ...                 return await self._generate(concept, image_type, params)
        ...             except Exception as e:
        ...                 if attempt == max_retries - 1:
        ...                     raise
        ...                 await asyncio.sleep(2 ** attempt)
    """

    async def generate_with_retry(
        self,
        concept: str,
        image_type: ImageType,
        params: dict[str, Any],
        max_retries: int = 2,
    ) -> dict[str, Any]:
        """Generate image with AI and retry on failure.
        
        Args:
            concept: Concept description for image generation.
            image_type: Type of image to generate.
                - INFOGRAPHIC: Informational graphics
                - PROOF_DIAGRAM: Mathematical proof diagrams
                - STEP_BY_STEP: Step-by-step process visualization
                - COMPARISON: Comparison charts
                - EXAMPLE: Example illustrations
                - CONCEPT_MAP: Concept relationship maps
            params: Additional parameters for generation.
            max_retries: Maximum number of retry attempts on failure.
        
        Returns:
            Dictionary containing:
                - id: Unique identifier for generated image
                - url: URL to generated image
                - thumbnail_url: URL to thumbnail image
                - title: Title of generated image
                - description: Description of generated image
                - source: "ai_generated"
        
        Raises:
            ImageGenerationError: If image generation fails after all retries.
            AIServiceError: If AI service is unavailable.
        """
        ...
