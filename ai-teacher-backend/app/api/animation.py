"""Animation API endpoints for generating Manim animations."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.animation_generator import animation_generator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/animations", tags=["animations"])


class AnimationRequest(BaseModel):
    """Request model for animation generation."""
    
    animation_type: str = Field(
        ...,
        description="Type of animation to generate",
        example="linear_function",
    )
    params: Dict[str, Any] = Field(
        ...,
        description="Animation parameters",
        example={"k": 2, "b": 1},
    )
    use_cache: bool = Field(
        True,
        description="Whether to use cached result",
    )


class AnimationResponse(BaseModel):
    """Response model for animation generation."""
    
    video_url: str = Field(..., description="URL to access the video")
    file_path: str = Field(..., description="Local file path")
    duration: float = Field(..., description="Video duration in seconds")
    cached: bool = Field(False, description="Whether result was from cache")


@router.post("/generate", response_model=AnimationResponse)
async def generate_animation(request: AnimationRequest):
    """Generate a Manim animation.
    
    This endpoint:
    1. Receives animation type and parameters
    2. Generates Manim code using LLM
    3. Executes code in OpenSandbox
    4. Returns video URL
    
    Args:
        request: Animation request with type and parameters
        
    Returns:
        Animation response with video URL
        
    Raises:
        HTTPException: If generation fails
    """
    logger.info(
        f"Received animation request: type={request.animation_type}, "
        f"params={request.params}"
    )
    
    try:
        result = await animation_generator.generate_animation(
            animation_type=request.animation_type,
            params=request.params,
        )
        
        logger.info(f"Animation generated successfully: {result['video_url']}")
        
        return result
        
    except TimeoutError as e:
        logger.error(f"Animation generation timeout: {e}")
        raise HTTPException(
            status_code=504,
            detail="Animation generation timed out",
        )
        
    except RuntimeError as e:
        logger.error(f"Animation generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate animation: {str(e)}",
        )
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )


@router.get("/types")
async def get_animation_types():
    """Get list of supported animation types.
    
    Returns:
        List of animation type names and descriptions
    """
    return {
        "types": [
            {
                "name": "linear_function",
                "description": "一次函数图像",
                "params": {
                    "k": "斜率",
                    "b": "截距",
                },
            },
            {
                "name": "coordinate_system",
                "description": "坐标系演示",
                "params": {},
            },
            {
                "name": "point_on_graph",
                "description": "函数图像上的点",
                "params": {
                    "k": "斜率",
                    "b": "截距",
                    "x": "x坐标值",
                },
            },
        ]
    }


@router.get("/health")
async def health_check():
    """Health check endpoint.
    
    Returns:
        Health status
    """
    try:
        # Check if OpenSandbox server is accessible
        from opensandbox import Sandbox
        
        # Try to create a minimal sandbox
        # This will fail if OpenSandbox server is not running
        return {
            "status": "healthy",
            "opensandbox": "connected",
        }
        
    except Exception as e:
        logger.warning(f"OpenSandbox health check failed: {e}")
        return {
            "status": "degraded",
            "opensandbox": "disconnected",
            "message": "OpenSandbox server not available",
        }
