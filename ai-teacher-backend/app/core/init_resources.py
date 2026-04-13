"""Initialize teaching resources with sample data."""

import logging
from datetime import datetime

from app.models.resource import (
    TeachingImage,
    ImageTemplate,
    ImageType,
    ImageStatus,
)
from app.repositories.resource_repository import (
    teaching_image_repository,
    image_template_repository,
)

logger = logging.getLogger(__name__)


def init_sample_images() -> None:
    """Initialize sample teaching images.
    
    This creates a set of sample images for the "一次函数" (Linear Function) topic.
    In production, this would be populated with real educational images.
    """
    logger.info("Initializing sample teaching images...")
    
    # Define sample images for linear function topic
    sample_images = [
        # Knowledge Point K1: 正比例函数
        {
            "id": "IMG_K1_001",
            "knowledge_point_id": "K1",
            "title": "正比例函数y=2x的图像",
            "description": "展示正比例函数y=2x的图像,经过原点的直线",
            "image_type": ImageType.EXAMPLE,
            "file_path": "/static/images/linear_func/proportional_example.png",
            "thumbnail_path": "/static/images/linear_func/proportional_example_thumb.png",
            "tags": ["正比例函数", "图像", "示例"],
            "metadata": {
                "function": "y=2x",
                "slope": 2,
                "intercept": 0,
            },
            "usage_count": 15,
            "rating": 4.5,
        },
        {
            "id": "IMG_K1_002",
            "title": "正比例函数性质总结",
            "knowledge_point_id": "K1",
            "description": "信息图表总结正比例函数的性质:过原点、单调性、图像位置",
            "image_type": ImageType.INFOGRAPHIC,
            "file_path": "/static/images/linear_func/proportional_properties.png",
            "thumbnail_path": "/static/images/linear_func/proportional_properties_thumb.png",
            "tags": ["正比例函数", "性质", "信息图表"],
            "metadata": {
                "content": "性质总结",
            },
            "usage_count": 23,
            "rating": 4.8,
        },
        
        # Knowledge Point K2: 一次函数定义
        {
            "id": "IMG_K2_001",
            "knowledge_point_id": "K2",
            "title": "一次函数的一般形式",
            "description": "展示一次函数y=kx+b的一般形式,说明k和b的含义",
            "image_type": ImageType.CONCEPT_MAP,
            "file_path": "/static/images/linear_func/general_form.png",
            "thumbnail_path": "/static/images/linear_func/general_form_thumb.png",
            "tags": ["一次函数", "定义", "概念图"],
            "metadata": {
                "formula": "y=kx+b",
            },
            "usage_count": 18,
            "rating": 4.6,
        },
        {
            "id": "IMG_K2_002",
            "knowledge_point_id": "K2",
            "title": "k和b对图像的影响",
            "description": "对比图展示不同k和b值对一次函数图像的影响",
            "image_type": ImageType.COMPARISON,
            "file_path": "/static/images/linear_func/kb_effect.png",
            "thumbnail_path": "/static/images/linear_func/kb_effect_thumb.png",
            "tags": ["一次函数", "k值", "b值", "对比"],
            "metadata": {
                "comparison_items": ["k>0", "k<0", "b>0", "b<0"],
            },
            "usage_count": 25,
            "rating": 4.9,
        },
        
        # Knowledge Point K3: 一次函数图像
        {
            "id": "IMG_K3_001",
            "knowledge_point_id": "K3",
            "title": "一次函数图像绘制步骤",
            "description": "步骤图展示绘制一次函数图像的详细步骤",
            "image_type": ImageType.STEP_BY_STEP,
            "file_path": "/static/images/linear_func/draw_steps.png",
            "thumbnail_path": "/static/images/linear_func/draw_steps_thumb.png",
            "tags": ["一次函数", "图像绘制", "步骤"],
            "metadata": {
                "steps": ["列表", "描点", "连线"],
            },
            "usage_count": 30,
            "rating": 4.7,
        },
        {
            "id": "IMG_K3_002",
            "knowledge_point_id": "K3",
            "title": "两点法画一次函数图像",
            "description": "示例展示如何用两点法快速画出一次函数图像",
            "image_type": ImageType.EXAMPLE,
            "file_path": "/static/images/linear_func/two_point_method.png",
            "thumbnail_path": "/static/images/linear_func/two_point_method_thumb.png",
            "tags": ["一次函数", "两点法", "示例"],
            "metadata": {
                "method": "两点法",
            },
            "usage_count": 28,
            "rating": 4.8,
        },
        
        # Knowledge Point K4: 一次函数性质
        {
            "id": "IMG_K4_001",
            "knowledge_point_id": "K4",
            "title": "一次函数性质全解析",
            "description": "信息图表全面展示一次函数的性质:单调性、象限、截距",
            "image_type": ImageType.INFOGRAPHIC,
            "file_path": "/static/images/linear_func/properties_overview.png",
            "thumbnail_path": "/static/images/linear_func/properties_overview_thumb.png",
            "tags": ["一次函数", "性质", "信息图表"],
            "metadata": {
                "properties": ["单调性", "象限分布", "截距"],
            },
            "usage_count": 35,
            "rating": 4.9,
        },
        {
            "id": "IMG_K4_002",
            "knowledge_point_id": "K4",
            "title": "k的正负对单调性的影响",
            "description": "对比图展示k>0和k<0时函数的单调性差异",
            "image_type": ImageType.COMPARISON,
            "file_path": "/static/images/linear_func/monotonicity.png",
            "thumbnail_path": "/static/images/linear_func/monotonicity_thumb.png",
            "tags": ["一次函数", "单调性", "k值", "对比"],
            "metadata": {
                "cases": ["k>0递增", "k<0递减"],
            },
            "usage_count": 22,
            "rating": 4.6,
        },
        
        # Knowledge Point K5: 待定系数法
        {
            "id": "IMG_K5_001",
            "knowledge_point_id": "K5",
            "title": "待定系数法求解析式",
            "description": "步骤图详细展示待定系数法的完整流程",
            "image_type": ImageType.STEP_BY_STEP,
            "file_path": "/static/images/linear_func/undetermined_coefficients.png",
            "thumbnail_path": "/static/images/linear_func/undetermined_coefficients_thumb.png",
            "tags": ["一次函数", "待定系数法", "步骤"],
            "metadata": {
                "steps": ["设解析式", "代入点坐标", "解方程组", "写出解析式"],
            },
            "usage_count": 40,
            "rating": 4.9,
        },
        {
            "id": "IMG_K5_002",
            "knowledge_point_id": "K5",
            "title": "待定系数法应用示例",
            "description": "具体示例展示如何用待定系数法求解一次函数解析式",
            "image_type": ImageType.EXAMPLE,
            "file_path": "/static/images/linear_func/undetermined_example.png",
            "thumbnail_path": "/static/images/linear_func/undetermined_example_thumb.png",
            "tags": ["一次函数", "待定系数法", "示例"],
            "metadata": {
                "example_type": "两点求解析式",
            },
            "usage_count": 32,
            "rating": 4.7,
        },
    ]
    
    # Create images in repository
    created_count = 0
    for img_data in sample_images:
        img = TeachingImage(
            id=img_data.get("id", ""),
            knowledge_point_id=img_data["knowledge_point_id"],
            title=img_data["title"],
            description=img_data["description"],
            image_type=img_data["image_type"],
            file_path=img_data["file_path"],
            thumbnail_path=img_data.get("thumbnail_path"),
            tags=img_data.get("tags", []),
            metadata=img_data.get("metadata", {}),
            usage_count=img_data.get("usage_count", 0),
            rating=img_data.get("rating", 0.0),
            status=ImageStatus.READY,
        )
        
        teaching_image_repository.create(img)
        created_count += 1
    
    logger.info(f"Created {created_count} sample images")


def init_sample_templates() -> None:
    """Initialize sample image templates.
    
    Templates allow quick rendering of common image types.
    """
    logger.info("Initializing sample image templates...")
    
    sample_templates = [
        {
            "id": "TPL_001",
            "name": "函数图像模板",
            "description": "通用函数图像绘制模板,支持自定义函数表达式",
            "template_type": ImageType.EXAMPLE,
            "template_path": "/templates/function_graph.svg",
            "variables": ["function", "x_range", "y_range", "title"],
            "preview_url": "/static/templates/function_graph_preview.png",
        },
        {
            "id": "TPL_002",
            "name": "步骤流程图模板",
            "description": "步骤分解图模板,适合展示解题步骤",
            "template_type": ImageType.STEP_BY_STEP,
            "template_path": "/templates/steps.svg",
            "variables": ["title", "steps", "colors"],
            "preview_url": "/static/templates/steps_preview.png",
        },
        {
            "id": "TPL_003",
            "name": "对比分析模板",
            "description": "双栏对比图模板,适合展示异同点",
            "template_type": ImageType.COMPARISON,
            "template_path": "/templates/comparison.svg",
            "variables": ["title", "left_title", "right_title", "left_items", "right_items"],
            "preview_url": "/static/templates/comparison_preview.png",
        },
        {
            "id": "TPL_004",
            "name": "概念关系图模板",
            "description": "概念图模板,适合展示知识点之间的关系",
            "template_type": ImageType.CONCEPT_MAP,
            "template_path": "/templates/concept_map.svg",
            "variables": ["title", "concepts", "connections"],
            "preview_url": "/static/templates/concept_map_preview.png",
        },
        {
            "id": "TPL_005",
            "name": "信息图表模板",
            "description": "通用信息图表模板,支持多区块布局",
            "template_type": ImageType.INFOGRAPHIC,
            "template_path": "/templates/infographic.svg",
            "variables": ["title", "sections", "colors"],
            "preview_url": "/static/templates/infographic_preview.png",
        },
    ]
    
    # Create templates in repository
    created_count = 0
    for tpl_data in sample_templates:
        tpl = ImageTemplate(
            id=tpl_data.get("id", ""),
            name=tpl_data["name"],
            description=tpl_data["description"],
            template_type=tpl_data["template_type"],
            template_path=tpl_data["template_path"],
            variables=tpl_data["variables"],
            preview_url=tpl_data.get("preview_url"),
        )
        
        image_template_repository.create(tpl)
        created_count += 1
    
    logger.info(f"Created {created_count} sample templates")


def initialize_resources() -> None:
    """Initialize all teaching resources.
    
    This function should be called during application startup.
    """
    logger.info("=" * 60)
    logger.info("Initializing teaching resources...")
    logger.info("=" * 60)
    
    # Initialize images
    init_sample_images()
    
    # Initialize templates
    init_sample_templates()
    
    # Summary
    total_images = len(teaching_image_repository.get_all())
    total_templates = len(image_template_repository.get_all())
    
    logger.info("=" * 60)
    logger.info("Resource initialization completed!")
    logger.info(f"Total images: {total_images}")
    logger.info(f"Total templates: {total_templates}")
    logger.info("=" * 60)


if __name__ == "__main__":
    # Run initialization
    initialize_resources()
