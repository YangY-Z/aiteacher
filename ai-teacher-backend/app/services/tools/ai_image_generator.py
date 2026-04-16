"""AI image generation service."""

import logging
import os
from typing import Any, Optional

import httpx

from app.models.resource import ImageType
from app.services.tools.protocols import AIImageGeneratorProtocol

logger = logging.getLogger(__name__)


class AIImageGenerator(AIImageGeneratorProtocol):
    """Service for generating images using AI APIs."""
    
    def __init__(self):
        """Initialize the AI image generator."""
        self.api_key = os.getenv("ZHIPU_API_KEY")
        self.api_base = "https://open.bigmodel.cn/api/paas/v3/model-api"
        self.model = "cogview-3"  # 智谱AI的文生图模型
        
        if not self.api_key:
            logger.warning("ZHIPU_API_KEY not found in environment")
    
    async def generate(
        self,
        concept: str,
        image_type: ImageType,
        params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Generate an image using AI.
        
        Args:
            concept: Concept description.
            image_type: Type of image to generate.
            params: Additional parameters for generation.
            
        Returns:
            Generated image resource info.
        
        Raises:
            Exception: If generation fails.
        """
        logger.info(f"Generating image with AI: {concept}, type: {image_type.value}")
        
        # Build the prompt
        prompt = self._build_prompt(concept, image_type, params)
        
        # Call AI API
        try:
            image_url = await self._call_api(prompt)
            
            return {
                "id": f"ai_generated_{hash(concept)}",
                "type": "image",
                "url": image_url,
                "thumbnail_url": image_url,  # Use same URL for thumbnail
                "title": concept,
                "description": f"AI生成的{image_type.value}图片",
                "source": "ai_generated",
                "prompt": prompt,
            }
        except Exception as e:
            logger.error(f"AI image generation failed: {e}")
            raise
    
    def _build_prompt(
        self,
        concept: str,
        image_type: ImageType,
        params: Optional[dict[str, Any]] = None
    ) -> str:
        """Build a prompt for image generation.
        
        Args:
            concept: Concept description.
            image_type: Type of image.
            params: Additional parameters.
            
        Returns:
            Generated prompt.
        """
        # Map image type to prompt template
        type_prompts = {
            ImageType.INFOGRAPHIC: "教学信息图表，清晰展示概念关系",
            ImageType.PROOF_DIAGRAM: "数学证明图，步骤清晰，逻辑严密",
            ImageType.STEP_BY_STEP: "步骤分解图，循序渐进",
            ImageType.COMPARISON: "对比图，清晰展示异同",
            ImageType.EXAMPLE: "教学示例图，具体生动",
            ImageType.CONCEPT_MAP: "概念图，层次分明，关系清晰",
        }
        
        base_prompt = type_prompts.get(image_type, "教学图片")
        
        # Combine concept and type description
        prompt = f"{base_prompt}：{concept}"
        
        # Add style guidance
        prompt += "，简洁清晰，适合中学生理解，教学风格"
        
        # Add any additional params
        if params:
            if "style" in params:
                prompt += f"，{params['style']}"
            if "focus" in params:
                prompt += f"，重点突出{params['focus']}"
        
        return prompt
    
    async def _call_api(self, prompt: str) -> str:
        """Call the AI image generation API.
        
        Args:
            prompt: Generation prompt.
            
        Returns:
            Generated image URL.
        """
        if not self.api_key:
            # Mock response for development
            logger.warning("No API key, returning mock image URL")
            return f"/static/images/mock/{hash(prompt)}.png"
        
        async with httpx.AsyncClient() as client:
            # Call Zhipu AI CogView API
            response = await client.post(
                f"{self.api_base}/{self.model}/text-to-image",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": prompt,
                    "size": "1024x1024",
                },
                timeout=60.0,
            )
            
            if response.status_code != 200:
                raise Exception(f"API call failed: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # Extract image URL from response
            # Note: Actual response format depends on API
            if "data" in data and len(data["data"]) > 0:
                return data["data"][0]["url"]
            else:
                raise Exception("No image URL in response")
    
    async def generate_with_retry(
        self,
        concept: str,
        image_type: ImageType,
        params: Optional[dict[str, Any]] = None,
        max_retries: int = 3
    ) -> dict[str, Any]:
        """Generate image with retry logic.
        
        Args:
            concept: Concept description.
            image_type: Type of image.
            params: Additional parameters.
            max_retries: Maximum number of retries.
            
        Returns:
            Generated image resource info.
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self.generate(concept, image_type, params)
            except Exception as e:
                last_error = e
                logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                
                # Adjust prompt for retry
                if attempt < max_retries - 1:
                    params = params or {}
                    params["retry"] = attempt + 1
        
        raise last_error or Exception("Image generation failed after retries")


# Global instance
ai_image_generator = AIImageGenerator()
