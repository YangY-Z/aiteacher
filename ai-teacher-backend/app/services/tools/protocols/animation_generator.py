"""Protocol for animation generator operations.

This module defines the interface for animation generator implementations.
"""

from typing import Any, Optional, Protocol


class AnimationGeneratorProtocol(Protocol):
    """Protocol for animation generator operations.
    
    This interface defines the contract for animation generation using Manim.
    Any class that implements these methods can be used as an animation generator.
    
    Implementations:
        - AnimationGenerator: Main implementation using LLM and OpenSandbox
    
    Example:
        >>> class MyAnimationGenerator(AnimationGeneratorProtocol):
        ...     async def generate_animation(
        ...         self,
        ...         animation_type: str,
        ...         params: dict[str, Any],
        ...         trace_id: Optional[str] = None,
        ...         output_format: str = "video"
        ...     ) -> dict[str, Any]:
        ...         # Generate Manim code with LLM
        ...         code = await self._generate_code(animation_type, params)
        ...         # Execute in sandbox
        ...         result = await self._execute_in_sandbox(code, output_format)
        ...         return result
    """

    async def generate_animation(
        self,
        animation_type: str,
        params: dict[str, Any],
        trace_id: Optional[str] = None,
        output_format: str = "video",
    ) -> dict[str, Any]:
        """Generate animation with Manim.
        
        Args:
            animation_type: Type of animation to generate.
                - "auto": LLM decides what to generate
                - "linear_function": Linear function (requires k, b params)
                - "coordinate_system": Coordinate system
                - "point_on_graph": Point on graph (requires k, b, x params)
            params: Animation parameters including:
                - concept: Concept description
                - k: Slope (for linear functions)
                - b: Intercept (for linear functions)
                - x: X coordinate (for point_on_graph)
                - Other specific parameters
            trace_id: Trace ID for logging and debugging.
            output_format: Output format, either "video" or "image".
                - "video": Generate MP4 animation
                - "image": Generate PNG image (last frame)
        
        Returns:
            Dictionary containing:
                - video_url: URL to video file (if output_format="video")
                - image_url: URL to image file (if output_format="image")
                - duration: Animation duration in seconds
                - cached: Whether result was retrieved from cache
                - file_path: Path to generated file
        
        Raises:
            AnimationGenerationError: If animation generation fails.
            SandboxExecutionError: If sandbox execution fails.
        """
        ...
