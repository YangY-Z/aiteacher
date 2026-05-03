"""Resource repositories for teaching materials."""

import logging
import re
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

# Keywords commonly used in math/teaching contexts for tagging
MATH_KEYWORDS = [
    "函数", "图像", "坐标系", "一次函数", "二次函数", "反比例函数",
    "直线", "斜率", "截距", "平移", "对称", "交点", "方程",
    "不等式", "概率", "统计", "几何", "三角形", "圆", "平行",
    "垂直", "角度", "面积", "体积", "相似", "全等", "变量",
    "常数", "正比例", "定义域", "值域", "单调性", "奇偶性",
    "抛物线", "顶点", "开口方向", "对称轴",
    "增减性", "图象", "图表", "变换", "旋转", "翻折",
    "y=kx", "y=kx+b", "y=ax+b", "y=ax^2+bx+c",
    "k", "b", "a", "c",
]


def extract_keywords(text: str) -> list[str]:
    """从描述文本中提取关键词，用于标签和检索。

    Args:
        text: 描述文本。

    Returns:
        提取的关键词列表。
    """
    if not text:
        return []

    keywords = set()

    # 1. 匹配预定义的数学关键词
    for kw in MATH_KEYWORDS:
        if kw in text:
            keywords.add(kw)

    # 2. 提取数字和字母组合（如 y=2x+1, k=3）
    math_patterns = re.findall(r'[a-zA-Z]\s*=\s*[0-9a-zA-Z+\-*/^]+', text)
    for p in math_patterns:
        keywords.add(p.replace(" ", ""))

    # 3. 提取中文词组（2-4字连续中文字符）
    chinese_words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
    for w in chinese_words:
        # 过滤掉太泛的词
        if w not in ("的", "和", "与", "在", "中", "上", "下", "不", "是",
                      "了", "有", "我们", "可以", "这个", "那个", "一个"):
            keywords.add(w)

    return sorted(keywords)[:20]  # 最多20个标签


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
        return self._images.get(id)
    
    def get_by_knowledge_point(
        self, 
        knowledge_point_id: str,
        image_type: Optional[ImageType] = None,
        limit: int = 10
    ) -> list[TeachingImage]:
        images = []
        for img in self._images.values():
            if img.knowledge_point_id == knowledge_point_id:
                if image_type is None or img.image_type == image_type:
                    if img.status == ImageStatus.READY:
                        images.append(img)
        images.sort(key=lambda x: (x.usage_count, x.rating), reverse=True)
        return images[:limit]
    
    def search_by_tags(
        self,
        tags: list[str],
        knowledge_point_id: Optional[str] = None,
        limit: int = 10
    ) -> list[TeachingImage]:
        images = []
        for img in self._images.values():
            if any(tag in img.tags for tag in tags):
                if knowledge_point_id is None or img.knowledge_point_id == knowledge_point_id:
                    if img.status == ImageStatus.READY:
                        images.append(img)
        images.sort(key=lambda x: (x.usage_count, x.rating), reverse=True)
        return images[:limit]

    def search_by_keyword(self, keyword: str, limit: int = 10) -> list[TeachingImage]:
        """按关键词搜索图片（匹配标签、标题、描述）。

        Args:
            keyword: 搜索关键词。
            limit: 最大返回数量。

        Returns:
            匹配的图片列表。
        """
        results = []
        keyword_lower = keyword.lower()
        for img in self._images.values():
            if img.status != ImageStatus.READY:
                continue
            # 在标签、标题、描述中搜索
            if (keyword_lower in img.title.lower()
                or keyword_lower in img.description.lower()
                or any(keyword_lower in tag.lower() for tag in img.tags)):
                results.append(img)
        results.sort(key=lambda x: (x.usage_count, x.rating), reverse=True)
        return results[:limit]

    def find_by_cache_key(self, cache_key: str) -> Optional[TeachingImage]:
        """根据缓存键查找图片（用于去重）。

        Args:
            cache_key: 动画生成器的缓存键。

        Returns:
            匹配的图片或None。
        """
        for img in self._images.values():
            if img.metadata.get("cache_key") == cache_key:
                return img
        return None
    
    def create(self, entity: TeachingImage) -> TeachingImage:
        if not entity.id:
            entity.id = str(uuid.uuid4())
        entity.created_at = datetime.now()
        entity.updated_at = datetime.now()
        self._images[entity.id] = entity
        db.save_media_resources_to_file()
        logger.info(f"Created image: {entity.id} - {entity.title}")
        return entity
    
    def update(self, entity: TeachingImage) -> TeachingImage:
        entity.updated_at = datetime.now()
        self._images[entity.id] = entity
        db.save_media_resources_to_file()
        logger.info(f"Updated image: {entity.id}")
        return entity
    
    def increment_usage(self, id: str) -> None:
        if id in self._images:
            self._images[id].usage_count += 1
            self._images[id].updated_at = datetime.now()
    
    def get_all(self) -> list[TeachingImage]:
        return list(self._images.values())
    
    def delete(self, id: str) -> bool:
        if id in self._images:
            del self._images[id]
            db.save_media_resources_to_file()
            logger.info(f"Deleted image: {id}")
            return True
        return False


class TeachingVideoRepository(BaseRepository[TeachingVideo, str]):
    """Repository for teaching videos using in-memory storage."""

    def __init__(self):
        if not hasattr(db, "_teaching_videos"):
            db._teaching_videos = {}
        self._videos = db._teaching_videos

    def get_by_id(self, id: str) -> Optional[TeachingVideo]:
        return self._videos.get(id)

    def get_by_knowledge_point(
        self,
        knowledge_point_id: str,
        limit: int = 10,
    ) -> list[TeachingVideo]:
        videos = []
        for vid in self._videos.values():
            if vid.knowledge_point_id == knowledge_point_id:
                videos.append(vid)
        videos.sort(key=lambda x: (x.usage_count, x.rating), reverse=True)
        return videos[:limit]

    def search_by_keyword(self, keyword: str, limit: int = 10) -> list[TeachingVideo]:
        """按关键词搜索视频（匹配标签、标题、描述）。

        Args:
            keyword: 搜索关键词。
            limit: 最大返回数量。

        Returns:
            匹配的视频列表。
        """
        results = []
        keyword_lower = keyword.lower()
        for vid in self._videos.values():
            if (keyword_lower in vid.title.lower()
                or keyword_lower in vid.description.lower()
                or any(keyword_lower in tag.lower() for tag in vid.tags)):
                results.append(vid)
        results.sort(key=lambda x: (x.usage_count, x.rating), reverse=True)
        return results[:limit]

    def find_by_cache_key(self, cache_key: str) -> Optional[TeachingVideo]:
        """根据缓存键查找视频（用于去重）。

        Args:
            cache_key: 动画生成器的缓存键。

        Returns:
            匹配的视频或None。
        """
        for vid in self._videos.values():
            if vid.metadata.get("cache_key") == cache_key:
                return vid
        return None

    def create(self, entity: TeachingVideo) -> TeachingVideo:
        if not entity.id:
            entity.id = str(uuid.uuid4())
        entity.created_at = datetime.now()
        self._videos[entity.id] = entity
        db.save_media_resources_to_file()
        logger.info(f"Created video: {entity.id} - {entity.title}")
        return entity

    def update(self, entity: TeachingVideo) -> TeachingVideo:
        self._videos[entity.id] = entity
        db.save_media_resources_to_file()
        logger.info(f"Updated video: {entity.id}")
        return entity

    def increment_usage(self, id: str) -> None:
        if id in self._videos:
            self._videos[id].usage_count += 1

    def get_all(self) -> list[TeachingVideo]:
        return list(self._videos.values())

    def delete(self, id: str) -> bool:
        if id in self._videos:
            del self._videos[id]
            db.save_media_resources_to_file()
            logger.info(f"Deleted video: {id}")
            return True
        return False


class ImageTemplateRepository(BaseRepository[ImageTemplate, str]):
    """Repository for image templates."""
    
    def __init__(self):
        if not hasattr(db, "_image_templates"):
            db._image_templates = {}
        self._templates = db._image_templates
    
    def get_by_id(self, id: str) -> Optional[ImageTemplate]:
        return self._templates.get(id)
    
    def find_template(
        self,
        concept: str,
        template_type: Optional[ImageType] = None
    ) -> Optional[ImageTemplate]:
        for template in self._templates.values():
            if template_type and template.template_type != template_type:
                continue
            if any(keyword in concept for keyword in template.name.lower().split()):
                return template
        return None
    
    def create(self, entity: ImageTemplate) -> ImageTemplate:
        if not entity.id:
            entity.id = str(uuid.uuid4())
        entity.created_at = datetime.now()
        self._templates[entity.id] = entity
        logger.info(f"Created template: {entity.id} - {entity.name}")
        return entity
    
    def get_all(self) -> list[ImageTemplate]:
        return list(self._templates.values())
    
    def update(self, entity: ImageTemplate) -> ImageTemplate:
        self._templates[entity.id] = entity
        logger.info(f"Updated template: {entity.id}")
        return entity
    
    def delete(self, id: str) -> bool:
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
        if not hasattr(db, "_tool_usage_logs"):
            db._tool_usage_logs = []
        self._logs = db._tool_usage_logs
    
    def get_by_id(self, id: str) -> Optional[ToolUsageLog]:
        for log in self._logs:
            if log.id == id:
                return log
        return None
    
    def create(self, entity: ToolUsageLog) -> ToolUsageLog:
        if not entity.id:
            entity.id = str(uuid.uuid4())
        entity.created_at = datetime.now()
        self._logs.append(entity)
        return entity
    
    def get_all(self) -> list[ToolUsageLog]:
        return list(self._logs)
    
    def get_by_knowledge_point(self, knowledge_point_id: str, limit: int = 100) -> list[ToolUsageLog]:
        logs = [log for log in self._logs if log.knowledge_point_id == knowledge_point_id]
        logs.sort(key=lambda x: x.created_at, reverse=True)
        return logs[:limit]
    
    def update(self, entity: ToolUsageLog) -> ToolUsageLog:
        for i, log in enumerate(self._logs):
            if log.id == entity.id:
                self._logs[i] = entity
                logger.info(f"Updated log: {entity.id}")
                return entity
        raise ValueError(f"Log not found: {entity.id}")
    
    def delete(self, id: str) -> bool:
        for i, log in enumerate(self._logs):
            if log.id == id:
                del self._logs[i]
                logger.info(f"Deleted log: {id}")
                return True
        return False


# Global instances
teaching_image_repository = TeachingImageRepository()
teaching_video_repository = TeachingVideoRepository()
image_template_repository = ImageTemplateRepository()
tool_usage_log_repository = ToolUsageLogRepository()
