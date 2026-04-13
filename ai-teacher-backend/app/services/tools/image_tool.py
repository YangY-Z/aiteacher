"""Image tool implementation with real data sources."""

import logging
import time
from typing import Any, Optional

from app.models.resource import ImageType, ImageStatus
from app.models.tool import (
    ToolContext,
    ToolRequest,
    ToolResult,
    ToolMetadata,
    ResourceType,
)
from app.repositories.resource_repository import (
    teaching_image_repository,
    tool_usage_log_repository,
)
from app.services.ai_image_generator import ai_image_generator
from app.services.template_engine import template_engine
from app.services.tools.base import TeachingTool

logger = logging.getLogger(__name__)


class ImageTool(TeachingTool):
    """Image generation tool with real data sources.
    
    This tool supports three strategies:
    1. Image library retrieval (fastest, lowest cost)
    2. Template rendering (fast, low cost)
    3. AI generation (slowest, highest cost)
    
    Key Features:
    - Three-tier strategy: Library → Template → AI
    - On-demand loading: Only load images for current KP
    - Cost optimization: Prefer library/template over AI
    - Usage tracking: Log all operations
    
    Example:
        >>> tool = ImageTool()
        >>> context = await tool.get_context("K3")
        >>> print(context.description)
        "可用图片资源"
    """
    
    def __init__(self):
        """Initialize the image tool."""
        self.image_repo = teaching_image_repository
        self.template_engine = template_engine
        self.ai_generator = ai_image_generator
        self.usage_log_repo = tool_usage_log_repository
        logger.info("ImageTool initialized with real data sources")
    
    async def get_context(self, kp_id: str) -> ToolContext:
        """Get image context for a knowledge point.
        
        This method:
        1. Queries image library for the KP
        2. Returns context with available images
        3. Provides usage instructions
        
        If images are available:
        - Lists all available images with metadata
        - Provides instructions for referencing images
        
        If no images:
        - Returns empty resource list
        - Provides instructions for generating new images
        
        Args:
            kp_id: Knowledge point ID
            
        Returns:
            ToolContext with available images and usage guide
        """
        logger.info(f"Getting image context for kp_id={kp_id}")
        
        # Query image library from database
        images = self.image_repo.get_by_knowledge_point(kp_id, limit=10)
        
        if images:
            # Case 1: Images available in library
            logger.info(f"Found {len(images)} images in library for kp_id={kp_id}")
            
            return ToolContext(
                tool_name="image_generation",
                description="可用图片资源",
                available_resources=[
                    {
                        "id": img.id,
                        "title": img.title,
                        "description": img.description,
                        "type": img.image_type.value,
                        "usage_count": img.usage_count,
                        "rating": img.rating,
                    }
                    for img in images
                ],
                usage_guide="""
【图片使用方式】
- 在消息中添加: "image_id": "图片ID"
- 示例: {"type":"segment", "message":"让我们看一个例子...", "image_id":"IMG_001"}

【生成新图片】
- 如果没有合适图片,在消息中添加: "need_image": {"concept": "图片描述", "type": "图片类型"}
- 示例: {"type":"segment", "message":"...", "need_image": {"concept": "三角形内角和证明", "type": "proof_diagram"}}

【支持的图片类型】
- infographic: 信息图表(适合概念讲解)
- proof_diagram: 证明图(适合几何证明)
- step_by_step: 步骤图(适合公式推导)
- comparison: 对比图(适合辨析)
- example: 示例图(适合具体例子)
- concept_map: 概念图(适合知识结构)

【重要规则】
- 每个 segment 最多只能引用一个资源
- 如果需要多个图片,请分成多个 segment 输出
- 优先使用图片库中已有的高质量图片(使用次数多、评分高)
""",
            )
        else:
            # Case 2: No images in library - offer generation
            logger.info(f"No images found in library for kp_id={kp_id}")
            
            return ToolContext(
                tool_name="image_generation",
                description="图片生成工具",
                available_resources=[],
                usage_guide="""
【图片生成功能】
- 当前知识点暂无预置图片
- 可以动态生成教学图片
- 在消息中添加: "need_image": {"concept": "图片描述", "type": "图片类型"}

【支持的图片类型】
- infographic: 信息图表(适合概念讲解)
- proof_diagram: 证明图(适合几何证明)
- step_by_step: 步骤图(适合公式推导)
- comparison: 对比图(适合辨析)
- example: 示例图(适合具体例子)
- concept_map: 概念图(适合知识结构)

【示例】
{"type":"segment", "message":"让我们看一个例子...", "need_image": {"concept": "三角形内角和证明", "type": "proof_diagram"}}

【重要规则】
- 每个 segment 最多只能引用一个资源
- 生成图片会消耗较多时间,建议优先使用图片库资源
""",
            )
    
    async def execute(self, request: ToolRequest) -> ToolResult:
        """Execute image retrieval or generation.
        
        Actions:
        - get_image: Retrieve image from library
        - generate_image: Generate new image (template or AI)
        
        Strategy:
        1. Try template rendering first (fast, low cost)
        2. Fall back to AI generation (slower, higher cost)
        
        Args:
            request: ToolRequest with action and parameters
            
        Returns:
            ToolResult with image metadata or error
        """
        start_time = time.time()
        action = request.action
        params = request.params
        # Get kp_id and student_id from params
        kp_id = params.get("knowledge_point_id", "")
        student_id = params.get("student_id")
        
        logger.info(f"Executing image tool: action={action}, params={params}")
        
        try:
            if action == "get_image":
                # Retrieve existing image from library
                result = await self._get_image(params, kp_id)
            
            elif action == "generate_image":
                # Generate new image using template or AI
                result = await self._generate_image(params, kp_id)
            
            else:
                result = ToolResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
            
            # Log usage
            execution_time_ms = int((time.time() - start_time) * 1000)
            await self._log_usage(
                tool_name="image_generation",
                kp_id=kp_id,
                student_id=student_id,
                action=action,
                params=params,
                result=result.to_dict() if result.success else {"error": result.error},
                success=result.success,
                execution_time_ms=execution_time_ms
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Image tool execution failed: {e}", exc_info=True)
            
            # Log failure
            execution_time_ms = int((time.time() - start_time) * 1000)
            await self._log_usage(
                tool_name="image_generation",
                kp_id=kp_id,
                student_id=student_id,
                action=action,
                params=params,
                result={"error": str(e)},
                success=False,
                execution_time_ms=execution_time_ms
            )
            
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"action": action, "params": params}
            )
    
    async def _get_image(
        self,
        params: dict[str, Any],
        kp_id: str
    ) -> ToolResult:
        """Get image from library.
        
        Args:
            params: Parameters containing image_id
            kp_id: Knowledge point ID
            
        Returns:
            ToolResult with image data
        """
        image_id = params.get("image_id", "")
        
        # Query image from database
        image = self.image_repo.get_by_id(image_id)
        
        if not image:
            return ToolResult(
                success=False,
                error=f"Image not found: {image_id}"
            )
        
        # Increment usage count
        self.image_repo.increment_usage(image_id)
        
        logger.info(f"Retrieved image from library: {image_id}")
        
        return ToolResult(
            success=True,
            resource=image.to_dict()
        )
    
    async def _generate_image(
        self,
        params: dict[str, Any],
        kp_id: str
    ) -> ToolResult:
        """Generate new image using template or AI.
        
        Strategy:
        1. Try template rendering first
        2. Fall back to AI generation
        
        Args:
            params: Parameters containing concept and type
            kp_id: Knowledge point ID
            
        Returns:
            ToolResult with generated image data
        """
        concept = params.get("concept", "")
        image_type_str = params.get("type", "infographic")
        
        # Convert string to ImageType enum
        try:
            image_type = ImageType(image_type_str)
        except ValueError:
            image_type = ImageType.INFOGRAPHIC
        
        # Strategy 1: Try template rendering
        rendered = await self.template_engine.render_quick(
            concept=concept,
            template_type=image_type,
            params=params
        )
        
        if rendered:
            logger.info(f"Image generated from template: {rendered['id']}")
            return ToolResult(success=True, resource=rendered)
        
        # Strategy 2: AI generation
        logger.info(f"No template found, generating with AI: {concept}")
        
        try:
            generated = await self.ai_generator.generate_with_retry(
                concept=concept,
                image_type=image_type,
                params=params,
                max_retries=2
            )
            
            logger.info(f"Image generated by AI: {generated['id']}")
            
            # TODO: Optionally save generated image to library
            # self._save_to_library(generated, kp_id)
            
            return ToolResult(success=True, resource=generated)
        
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return ToolResult(
                success=False,
                error=f"Image generation failed: {str(e)}"
            )
    
    async def _log_usage(
        self,
        tool_name: str,
        kp_id: str,
        student_id: Optional[int],
        action: str,
        params: dict[str, Any],
        result: dict[str, Any],
        success: bool,
        execution_time_ms: int
    ) -> None:
        """Log tool usage.
        
        Args:
            tool_name: Name of the tool
            kp_id: Knowledge point ID
            student_id: Student ID if available
            action: Action performed
            params: Action parameters
            result: Action result
            success: Whether the action succeeded
            execution_time_ms: Execution time in milliseconds
        """
        from app.models.resource import ToolUsageLog
        
        log = ToolUsageLog(
            id="",  # Will be auto-generated
            tool_name=tool_name,
            knowledge_point_id=kp_id,
            student_id=student_id,
            action=action,
            params=params,
            result=result,
            success=success,
            execution_time_ms=execution_time_ms
        )
        
        self.usage_log_repo.create(log)
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata.
        
        Returns:
            ToolMetadata with tool capabilities
        """
        return ToolMetadata(
            name="image_generation",
            description="教学图片生成工具",
            capabilities=[
                "图片库检索(最快)",
                "模板渲染(较快)",
                "AI生成(较慢)",
                "使用记录跟踪"
            ],
            resource_types=[ResourceType.IMAGE],
        )
