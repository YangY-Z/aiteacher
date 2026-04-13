"""Resource models for teaching materials."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ResourceType(Enum):
    """Types of teaching resources."""
    IMAGE = "image"
    VIDEO = "video"
    INTERACTIVE = "interactive"
    TEMPLATE = "template"


class ImageType(Enum):
    """Types of images."""
    INFOGRAPHIC = "infographic"  # 信息图表
    PROOF_DIAGRAM = "proof_diagram"  # 证明图
    STEP_BY_STEP = "step_by_step"  # 步骤图
    COMPARISON = "comparison"  # 对比图
    EXAMPLE = "example"  # 示例图
    CONCEPT_MAP = "concept_map"  # 概念图


class ImageStatus(Enum):
    """Status of images."""
    READY = "ready"  # 可用
    GENERATING = "generating"  # 生成中
    FAILED = "failed"  # 失败


@dataclass
class TeachingImage:
    """Teaching image resource."""
    id: str
    knowledge_point_id: str
    title: str
    description: str
    image_type: ImageType
    file_path: str  # 图片文件路径或URL
    thumbnail_path: Optional[str] = None  # 缩略图路径
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    usage_count: int = 0  # 使用次数
    rating: float = 0.0  # 评分(0-5)
    status: ImageStatus = ImageStatus.READY
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "knowledge_point_id": self.knowledge_point_id,
            "title": self.title,
            "description": self.description,
            "image_type": self.image_type.value,
            "file_path": self.file_path,
            "thumbnail_path": self.thumbnail_path,
            "tags": self.tags,
            "metadata": self.metadata,
            "usage_count": self.usage_count,
            "rating": self.rating,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class ImageTemplate:
    """Image template for rendering."""
    id: str
    name: str
    description: str
    template_type: ImageType
    template_path: str  # 模板文件路径
    variables: list[str]  # 模板变量列表
    preview_url: Optional[str] = None
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type.value,
            "template_path": self.template_path,
            "variables": self.variables,
            "preview_url": self.preview_url,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class TeachingVideo:
    """Teaching video resource."""
    id: str
    knowledge_point_id: str
    title: str
    description: str
    video_url: str
    duration: int  # 时长(秒)
    thumbnail_url: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    usage_count: int = 0
    rating: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "knowledge_point_id": self.knowledge_point_id,
            "title": self.title,
            "description": self.description,
            "video_url": self.video_url,
            "duration": self.duration,
            "thumbnail_url": self.thumbnail_url,
            "tags": self.tags,
            "metadata": self.metadata,
            "usage_count": self.usage_count,
            "rating": self.rating,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class InteractiveDemo:
    """Interactive demonstration resource."""
    id: str
    knowledge_point_id: str
    title: str
    description: str
    demo_url: str  # 交互演示URL
    demo_type: str  # 类型: geogebra, desmos, custom
    config: dict[str, Any] = field(default_factory=dict)
    thumbnail_url: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    usage_count: int = 0
    rating: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "knowledge_point_id": self.knowledge_point_id,
            "title": self.title,
            "description": self.description,
            "demo_url": self.demo_url,
            "demo_type": self.demo_type,
            "config": self.config,
            "thumbnail_url": self.thumbnail_url,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "rating": self.rating,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ToolUsageLog:
    """Log entry for tool usage."""
    id: str
    tool_name: str
    knowledge_point_id: str
    student_id: Optional[int]
    action: str
    params: dict[str, Any]
    result: dict[str, Any]
    success: bool
    execution_time_ms: int
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "knowledge_point_id": self.knowledge_point_id,
            "student_id": self.student_id,
            "action": self.action,
            "params": self.params,
            "result": self.result,
            "success": self.success,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat(),
        }
