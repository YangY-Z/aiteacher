"""Image tool implementation with real data sources.

This module provides image generation and retrieval functionality following
SOLID principles and clean architecture patterns.
"""

import logging
import time
from typing import Any, Optional

from app.models.resource import ImageType, ToolUsageLog
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
from app.services.tools.ai_image_generator import ai_image_generator
from app.services.tools.animation_generator import animation_generator
from app.services.tools.base import TeachingTool
from app.services.tools.protocols import (
    ImageRepositoryProtocol,
    AnimationGeneratorProtocol,
    AIImageGeneratorProtocol,
    UsageLogRepositoryProtocol,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Main ImageTool Class
# ============================================================================


class ImageTool(TeachingTool):
    """Image generation tool with real data sources.

    This tool supports three strategies:
    1. Image library retrieval (fastest, lowest cost)
    2. Manim animation generation (medium cost, high quality)
    3. AI generation (slowest, highest cost)

    Attributes:
        image_repo: Repository for image library operations.
        animation_generator: Generator for Manim animations.
        ai_generator: Generator for AI image generation.
        usage_log_repo: Repository for usage logging.

    Example:
        >>> tool = ImageTool(
        ...     image_repo=teaching_image_repository,
        ...     animation_generator=animation_generator,
        ...     ai_generator=ai_image_generator,
        ...     usage_log_repo=tool_usage_log_repository
        ... )
        >>> context = await tool.get_context("K3")
        >>> print(context.description)
        "可用图片资源"
    """

    def __init__(
        self,
        image_repo: ImageRepositoryProtocol,
        animation_generator: AnimationGeneratorProtocol,
        ai_generator: AIImageGeneratorProtocol,
        usage_log_repo: UsageLogRepositoryProtocol,
    ):
        """Initialize the image tool with dependencies.

        Args:
            image_repo: Repository for image library operations.
            animation_generator: Generator for Manim animations.
            ai_generator: Generator for AI image generation.
            usage_log_repo: Repository for usage logging.
        """
        self._image_repo = image_repo
        self._animation_generator = animation_generator
        self._ai_generator = ai_generator
        self._usage_log_repo = usage_log_repo
        logger.info(
            "ImageTool initialized",
            extra={
                "component": "ImageTool",
                "action": "initialize"
            }
        )

    # ========================================================================
    # Public Methods
    # ========================================================================

    async def get_context(self, kp_id: str) -> ToolContext:
        """Get image context for a knowledge point.

        This method queries the image library for available resources and returns
        context with usage instructions. If images are available, it lists them
        with metadata. Otherwise, it provides instructions for generating new images.

        Args:
            kp_id: Knowledge point ID.

        Returns:
            ToolContext with available images and usage guide.
        """
        logger.info(
            "Getting image context",
            extra={
                "component": "ImageTool",
                "action": "get_context",
                "kp_id": kp_id
            }
        )

        images = self._image_repo.get_by_knowledge_point(kp_id, limit=10)

        if images:
            return self._build_context_with_images(images)
        else:
            return self._build_context_without_images()

    async def execute(self, request: ToolRequest) -> ToolResult:
        """Execute image retrieval or generation.

        Supported actions:
        - get_image: Retrieve image from library
        - generate_image: Generate new image (Manim or AI)

        Strategy:
        1. Try Manim generation if animation_type is provided
        2. Fall back to AI generation otherwise

        Args:
            request: ToolRequest with action and parameters.

        Returns:
            ToolResult with image metadata or error.

        Raises:
            ValueError: If action is unknown.
        """
        start_time = time.time()
        action = request.action
        params = request.params
        kp_id = params.get("knowledge_point_id", "")
        student_id = params.get("student_id")

        logger.info(
            "Executing image tool",
            extra={
                "component": "ImageTool",
                "action": action,
                "kp_id": kp_id,
                "student_id": student_id
            }
        )

        try:
            result = await self._execute_action(action, params, kp_id)
            
            self._log_usage(
                kp_id=kp_id,
                student_id=student_id,
                action=action,
                params=params,
                result=result.resource if result.success and result.resource else {"error": result.error},
                success=result.success,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

            return result

        except Exception as e:
            logger.exception(
                "Image tool execution failed",
                extra={
                    "component": "ImageTool",
                    "action": action,
                    "kp_id": kp_id,
                    "error": str(e)
                }
            )

            self._log_usage(
                kp_id=kp_id,
                student_id=student_id,
                action=action,
                params=params,
                result={"error": str(e)},
                success=False,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

            return ToolResult(
                success=False,
                error=str(e),
                metadata={"action": action, "params": params}
            )

    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata.

        Returns:
            ToolMetadata with tool capabilities.
        """
        return ToolMetadata(
            name="image_generation",
            description="教学图片生成工具",
            capabilities=[
                "图片库检索(最快)",
                "Manim动画生成(中等)",
                "AI生成(较慢)",
                "使用记录跟踪"
            ],
            resource_types=[ResourceType.IMAGE, ResourceType.VIDEO],
        )

    # ========================================================================
    # Private Methods - Action Execution
    # ========================================================================

    async def _execute_action(
        self,
        action: str,
        params: dict[str, Any],
        kp_id: str
    ) -> ToolResult:
        """Execute the specified action.

        Args:
            action: Action to execute (get_image or generate_image).
            params: Action parameters.
            kp_id: Knowledge point ID.

        Returns:
            ToolResult with action result.

        Raises:
            ValueError: If action is unknown.
        """
        if action == "get_image":
            return await self._get_image(params, kp_id)
        elif action == "generate_image":
            return await self._generate_image(params, kp_id)
        else:
            raise ValueError(f"Unknown action: {action}")

    async def _get_image(
        self,
        params: dict[str, Any],
        kp_id: str
    ) -> ToolResult:
        """Get image from library.

        Args:
            params: Parameters containing image_id.
            kp_id: Knowledge point ID.

        Returns:
            ToolResult with image data.
        """
        image_id = params.get("image_id", "")
        image = self._image_repo.get_by_id(image_id)

        if not image:
            logger.warning(
                "Image not found",
                extra={
                    "component": "ImageTool",
                    "action": "get_image",
                    "image_id": image_id
                }
            )
            return ToolResult(
                success=False,
                error=f"Image not found: {image_id}"
            )

        self._image_repo.increment_usage(image_id)

        logger.info(
            "Retrieved image from library",
            extra={
                "component": "ImageTool",
                "action": "get_image",
                "image_id": image_id
            }
        )

        return ToolResult(success=True, resource=image.to_dict())

    async def _generate_image(
        self,
        params: dict[str, Any],
        kp_id: str
    ) -> ToolResult:
        """Generate new image using Manim animation or AI.

        Strategy:
        1. If animation_type is provided by agent, use Manim generation
        2. Otherwise, fall back to AI generation

        Args:
            params: Generation parameters including:
                - concept: Concept description
                - type: Image type (optional)
                - animation_type: Animation type (optional)
                - output_format: "video" or "image" (default: "video")
                - Other animation parameters (k, b, x, etc.)
            kp_id: Knowledge point ID.

        Returns:
            ToolResult with generated image/video data.
        """
        animation_type = params.get("animation_type")

        if animation_type:
            return await self._generate_with_manim(params, kp_id)
        else:
            return await self._generate_with_ai(params, kp_id)

    # ========================================================================
    # Private Methods - Generation Strategies
    # ========================================================================

    async def _generate_with_manim(
        self,
        params: dict[str, Any],
        kp_id: str
    ) -> ToolResult:
        """Generate image/video using Manim.

        Args:
            params: Generation parameters.
            kp_id: Knowledge point ID.

        Returns:
            ToolResult with generated resource.
        """
        concept = params.get("concept", "")
        animation_type = params.get("animation_type")
        output_format = params.get("output_format", "video")

        logger.info(
            "Generating with Manim",
            extra={
                "component": "ImageTool",
                "action": "generate_image",
                "animation_type": animation_type,
                "output_format": output_format,
                "kp_id": kp_id
            }
        )

        try:
            generated = await self._animation_generator.generate_animation(
                animation_type=animation_type,
                params=params,
                trace_id=f"img_{kp_id}",
                output_format=output_format
            )

            resource = self._build_manim_resource(
                generated=generated,
                concept=concept,
                animation_type=animation_type,
                output_format=output_format
            )

            logger.info(
                "Manim generation succeeded",
                extra={
                    "component": "ImageTool",
                    "action": "generate_image",
                    "output_format": output_format,
                    "cached": generated.get('cached', False)
                }
            )

            return ToolResult(success=True, resource=resource)

        except Exception as e:
            logger.warning(
                "Manim generation failed, falling back to AI",
                extra={
                    "component": "ImageTool",
                    "action": "generate_image",
                    "error": str(e)
                }
            )
            return await self._generate_with_ai(params, kp_id)

    async def _generate_with_ai(
        self,
        params: dict[str, Any],
        kp_id: str
    ) -> ToolResult:
        """Generate image using AI.

        Args:
            params: Generation parameters.
            kp_id: Knowledge point ID.

        Returns:
            ToolResult with generated image.
        """
        concept = params.get("concept", "")
        image_type_str = params.get("type", "infographic")

        try:
            image_type = ImageType(image_type_str)
        except ValueError:
            image_type = ImageType.INFOGRAPHIC

        logger.info(
            "Generating with AI",
            extra={
                "component": "ImageTool",
                "action": "generate_image",
                "image_type": image_type_str,
                "kp_id": kp_id
            }
        )

        try:
            generated = await self._ai_generator.generate_with_retry(
                concept=concept,
                image_type=image_type,
                params=params,
                max_retries=2
            )

            logger.info(
                "AI generation succeeded",
                extra={
                    "component": "ImageTool",
                    "action": "generate_image",
                    "image_id": generated.get('id')
                }
            )

            return ToolResult(success=True, resource=generated)

        except Exception as e:
            logger.error(
                "AI generation failed",
                extra={
                    "component": "ImageTool",
                    "action": "generate_image",
                    "error": str(e)
                }
            )
            return ToolResult(
                success=False,
                error=f"Image generation failed: {str(e)}"
            )

    # ========================================================================
    # Private Methods - Resource Building
    # ========================================================================

    def _build_manim_resource(
        self,
        generated: dict[str, Any],
        concept: str,
        animation_type: str,
        output_format: str
    ) -> dict[str, Any]:
        """Build resource dictionary for Manim generation result.

        Args:
            generated: Generated animation/image data.
            concept: Concept description.
            animation_type: Animation type.
            output_format: Output format (video or image).

        Returns:
            Resource dictionary.
        """
        if output_format == "video":
            return self._build_video_resource(generated, concept, animation_type)
        else:
            return self._build_image_resource(generated, concept, animation_type)

    def _build_video_resource(
        self,
        generated: dict[str, Any],
        concept: str,
        animation_type: str
    ) -> dict[str, Any]:
        """Build video resource dictionary.

        Args:
            generated: Generated video data.
            concept: Concept description.
            animation_type: Animation type.

        Returns:
            Video resource dictionary.
        """
        video_url = generated['video_url']
        return {
            "id": video_url.split('/')[-1].replace('.mp4', ''),
            "type": "video",
            "url": video_url,
            "thumbnail_url": video_url,
            "title": f"{concept}动画演示",
            "description": concept,
            "source": "manim_generated",
            "animation_type": animation_type,
            "duration": generated.get('duration', 15.0),
            "cached": generated.get('cached', False),
        }

    def _build_image_resource(
        self,
        generated: dict[str, Any],
        concept: str,
        animation_type: str
    ) -> dict[str, Any]:
        """Build image resource dictionary.

        Args:
            generated: Generated image data.
            concept: Concept description.
            animation_type: Animation type.

        Returns:
            Image resource dictionary.
        """
        image_url = generated['image_url']
        return {
            "id": image_url.split('/')[-1].replace('.png', ''),
            "type": "image",
            "url": image_url,
            "thumbnail_url": image_url,
            "title": f"{concept}图示",
            "description": concept,
            "source": "manim_generated",
            "animation_type": animation_type,
            "cached": generated.get('cached', False),
        }

    # ========================================================================
    # Private Methods - Context Building
    # ========================================================================

    def _build_context_with_images(self, images: list[Any]) -> ToolContext:
        """Build tool context with available images.

        Args:
            images: List of available images.

        Returns:
            ToolContext with image list and usage guide.
        """
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
            usage_guide=self._get_usage_guide_with_images(),
        )

    def _build_context_without_images(self) -> ToolContext:
        """Build tool context without available images.

        Returns:
            ToolContext with generation guide.
        """
        return ToolContext(
            tool_name="image_generation",
            description="图片生成工具",
            available_resources=[],
            usage_guide=self._get_usage_guide_without_images(),
        )

    def _get_usage_guide_with_images(self) -> str:
        """Get usage guide when images are available.

        Returns:
            Usage guide string.
        """
        return """
【图片使用方式】
- 在消息中添加: "image_id": "图片ID"
- 示例: {"type":"segment", "message":"让我们看一个例子...", "image_id":"IMG_001"}

【生成新资源】
- 在消息中添加: "need_image": {...}
- 系统支持 Manim 动画生成和 AI 图片生成两种方式

【Manim 动画生成】
- 示例1 (自动模式): {"need_image": {"concept": "展示一次函数 y=2x+1 的图像", "animation_type": "auto", "k": 2, "b": 1}}
- 示例2 (指定类型): {"need_image": {"concept": "坐标系演示", "animation_type": "coordinate_system"}}
- 示例3 (生成图片): {"need_image": {"concept": "二次函数图像", "animation_type": "auto", "output_format": "image"}}

参数说明:
- animation_type: 动画类型
  - "auto": LLM 自动决定生成什么内容（推荐）
  - "linear_function": 一次函数（需要 k, b）
  - "coordinate_system": 坐标系
  - "point_on_graph": 图上的点（需要 k, b, x）
- output_format: 输出格式
  - "video": 生成动画视频
  - "image": 生成静态图片（默认）

Manim 能力:
- 各类函数图像（一次、二次、三角函数等）
- 几何图形与变换
- 数学证明过程
- 公式推导
- 数据可视化

【AI 图片生成】
- 示例: {"need_image": {"concept": "三角形内角和证明", "type": "proof_diagram"}}
- 支持: infographic, proof_diagram, step_by_step, comparison, example, concept_map

【重要规则】
- 提供 animation_type → 使用 Manim 生成
- 不提供 animation_type → 使用 AI 生成图片
- 推荐: 使用 animation_type="auto" 和 output_format 根据需要选择
- 每个 segment 最多只能引用一个资源
"""

    def _get_usage_guide_without_images(self) -> str:
        """Get usage guide when no images are available.

        Returns:
            Usage guide string.
        """
        return """
【资源生成功能】
- 可以动态生成教学图片或动画
- 在消息中添加: "need_image": {...}

【Manim 动画生成（推荐）】
- 示例1: {"need_image": {"concept": "展示二次函数 y=x² 的图像", "animation_type": "auto"}}
- 示例2: {"need_image": {"concept": "三角形外角和证明", "animation_type": "auto", "output_format": "image"}}

参数说明:
- animation_type: "auto"（自动决定）或具体类型
- output_format: "video"（动画视频）或 "image"（静态图片）
- concept: 详细描述要生成的内容

Manim 能力范围:
✅ 各类函数图像（一次、二次、三角、指数、对数等）
✅ 几何图形与变换（旋转、平移、缩放）
✅ 数学证明过程动画
✅ 公式推导步骤
✅ 数据可视化图表
✅ 坐标系、向量、参数方程等

【AI 图片生成】
- 示例: {"need_image": {"concept": "三角形内角和证明", "type": "proof_diagram"}}
- 适用于非数学动画类内容

【使用建议】
- 数学相关内容 → 使用 Manim（animation_type="auto"）
- 静态展示 → 设置 output_format="image"
- 动态演示 → 设置 output_format="video"（默认）
- 每个 segment 最多只能引用一个资源
"""

    # ========================================================================
    # Private Methods - Logging
    # ========================================================================

    def _log_usage(
        self,
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
            kp_id: Knowledge point ID.
            student_id: Student ID if available.
            action: Action performed.
            params: Action parameters.
            result: Action result.
            success: Whether the action succeeded.
            execution_time_ms: Execution time in milliseconds.
        """
        log = ToolUsageLog(
            id="",  # Will be auto-generated
            tool_name="image_generation",
            knowledge_point_id=kp_id,
            student_id=student_id,
            action=action,
            params=params,
            result=result,
            success=success,
            execution_time_ms=execution_time_ms
        )

        self._usage_log_repo.create(log)


# ============================================================================
# Factory Function for Default Instance
# ============================================================================


def create_image_tool() -> ImageTool:
    """Create default ImageTool instance with real dependencies.

    Returns:
        ImageTool instance with real data sources.
    """
    return ImageTool(
        image_repo=teaching_image_repository,
        animation_generator=animation_generator,
        ai_generator=ai_image_generator,
        usage_log_repo=tool_usage_log_repository
    )


# Default instance for backward compatibility
image_tool = create_image_tool()
