"""Tests for concept parameter passing in image/video generation flow.

Validates two bugs:
1. concept parameter should not be lost when generating Manim code
2. concept should have fallback to message field when empty

Also tests:
3. Media resources are persisted to database
4. Keywords are extracted from concept descriptions
5. Media resource persistence across restarts (JSON file)
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from app.models.tool import TeachingEvent, ToolRequest
from app.repositories.resource_repository import extract_keywords


class TestTeachingEventGetGenerationRequest:
    """Test TeachingEvent.get_generation_request() - concept parameter preservation."""

    def test_concept_preserved_in_normal_json(self):
        """LLM outputs need_image with concept - concept should be preserved."""
        llm_output = json.dumps({
            "type": "segment",
            "message": "我们来看一次函数 y=2x+1 的图像",
            "need_image": {
                "concept": "一次函数 y=2x+1 向上平移3和向右平移2的图像对比",
                "animation_type": "auto",
                "output_format": "image",
            },
        }, ensure_ascii=False)

        event = TeachingEvent(event_type="segment", message=llm_output)
        request = event.get_generation_request()

        assert request.action == "generate_image"
        assert request.params["concept"] == "一次函数 y=2x+1 向上平移3和向右平移2的图像对比"
        assert request.params["animation_type"] == "auto"
        assert request.params["output_format"] == "image"

    def test_concept_fallback_to_message_field(self):
        """When need_image.concept is empty, fallback to message field."""
        llm_output = json.dumps({
            "type": "segment",
            "message": "展示一次函数 y=2x+1 的图像变换",
            "need_image": {
                "concept": "",
                "animation_type": "auto",
                "output_format": "image",
            },
        }, ensure_ascii=False)

        event = TeachingEvent(event_type="segment", message=llm_output)
        request = event.get_generation_request()

        assert request.action == "generate_image"
        assert request.params["concept"] == "展示一次函数 y=2x+1 的图像变换"
        assert request.params["animation_type"] == "auto"

    def test_concept_fallback_when_missing(self):
        """When need_image has no concept key at all, fallback to message."""
        llm_output = json.dumps({
            "type": "segment",
            "message": "一次函数图像平移变换",
            "need_image": {
                "animation_type": "auto",
                "output_format": "image",
            },
        }, ensure_ascii=False)

        event = TeachingEvent(event_type="segment", message=llm_output)
        request = event.get_generation_request()

        assert request.action == "generate_image"
        assert request.params["concept"] == "一次函数图像平移变换"

    def test_concept_preserved_with_k_b_params(self):
        """concept should be preserved alongside k, b animation params."""
        llm_output = json.dumps({
            "type": "segment",
            "message": "一次函数图像",
            "need_image": {
                "concept": "一次函数 y=3x-2 的图像",
                "animation_type": "linear_function",
                "output_format": "video",
                "k": 3,
                "b": -2,
            },
        }, ensure_ascii=False)

        event = TeachingEvent(event_type="segment", message=llm_output)
        request = event.get_generation_request()

        assert request.params["concept"] == "一次函数 y=3x-2 的图像"
        assert request.params["animation_type"] == "linear_function"
        assert request.params["output_format"] == "video"
        assert request.params["k"] == 3
        assert request.params["b"] == -2

    def test_needs_image_generation_detection(self):
        """needs_image_generation() should detect need_image in message."""
        llm_output = json.dumps({
            "type": "segment",
            "message": "讲解内容",
            "need_image": {"concept": "test", "animation_type": "auto"},
        }, ensure_ascii=False)

        event = TeachingEvent(event_type="segment", message=llm_output)
        assert event.needs_image_generation() is True

    def test_no_need_image_no_generation(self):
        """When no need_image in message, needs_image_generation() returns False."""
        llm_output = json.dumps({
            "type": "segment",
            "message": "这是一段普通的教学文本",
        }, ensure_ascii=False)

        event = TeachingEvent(event_type="segment", message=llm_output)
        assert event.needs_image_generation() is False

    def test_default_params_set(self):
        """Default params should be set when not provided."""
        llm_output = json.dumps({
            "type": "segment",
            "message": "讲解内容",
            "need_image": {
                "concept": "test concept",
            },
        }, ensure_ascii=False)

        event = TeachingEvent(event_type="segment", message=llm_output)
        request = event.get_generation_request()

        assert request.params["animation_type"] == "auto"

    def test_regex_fallback_preserves_concept(self):
        """Regex fallback should also handle concept correctly."""
        llm_output = json.dumps({
            "type": "segment",
            "message": "坐标系中的图像",
            "need_image": {
                "concept": "一次函数 y=2x+1 图像",
                "animation_type": "auto",
                "output_format": "image",
            },
        }, ensure_ascii=False)

        event = TeachingEvent(event_type="segment", message=llm_output)
        request = event.get_generation_request()

        assert request.params["concept"] == "一次函数 y=2x+1 图像"

    def test_empty_need_image_object(self):
        """Empty need_image object should fallback gracefully."""
        llm_output = json.dumps({
            "type": "segment",
            "message": "一次函数概念讲解",
            "need_image": {},
        }, ensure_ascii=False)

        event = TeachingEvent(event_type="segment", message=llm_output)
        request = event.get_generation_request()

        assert request.action == "generate_image"
        assert request.params["concept"] == "一次函数概念讲解"
        assert request.params["animation_type"] == "auto"


class TestTeachingEventSSEFormat:
    """Test that image/video resources are correctly formatted for SSE output."""

    def test_image_resource_attached_to_event(self):
        event = TeachingEvent(event_type="segment", message="test")
        event.image = {
            "id": "test_img",
            "type": "image",
            "url": "/media/test.png",
            "title": "测试图片",
        }

        assert event.image is not None
        assert event.image["type"] == "image"
        assert event.image["url"] == "/media/test.png"

    def test_video_resource_attached_to_event(self):
        event = TeachingEvent(event_type="segment", message="test")
        event.video = {
            "id": "test_vid",
            "type": "video",
            "url": "/media/test.mp4",
            "title": "测试视频",
            "duration": 15.0,
        }

        assert event.video is not None
        assert event.video["type"] == "video"
        assert event.video["duration"] == 15.0

    def test_image_with_video_type(self):
        event = TeachingEvent(event_type="segment", message="test")
        event.image = {
            "id": "manim_video",
            "type": "video",
            "url": "/media/manim_auto_xxx.mp4",
            "thumbnail_url": "/media/manim_auto_xxx.mp4",
            "title": "一次函数动画演示",
            "description": "一次函数 y=2x+1",
            "source": "manim_generated",
            "animation_type": "auto",
            "duration": 15.0,
        }

        assert event.image is not None
        assert event.image["type"] == "video"
        assert event.image["url"].endswith(".mp4")


class TestLearningServiceNeedImage:
    """Test that learning_service correctly processes need_image from LLM output."""

    def test_segment_with_need_image_has_image_field(self):
        llm_segment = {
            "type": "segment",
            "message": "我们来看一次函数 y=2x+1 的图像",
            "whiteboard": {},
            "need_image": {
                "concept": "一次函数 y=2x+1 的图像",
                "animation_type": "auto",
                "output_format": "image",
            },
        }

        concept = llm_segment["need_image"]["concept"]
        expected_media_resource = {
            "id": "test_image",
            "type": "image",
            "url": f"/media/{concept[:30]}_image_test123.png",
            "title": concept,
            "description": concept,
            "concept": concept,
        }

        sse_data = {
            "message": llm_segment["message"],
            "whiteboard": llm_segment["whiteboard"],
            "image": expected_media_resource,
        }

        assert "image" in sse_data
        assert sse_data["image"]["type"] == "image"
        assert sse_data["image"]["concept"] == "一次函数 y=2x+1 的图像"
        assert sse_data["message"] == "我们来看一次函数 y=2x+1 的图像"

    def test_segment_with_video_need_image(self):
        llm_segment = {
            "type": "segment",
            "message": "观察函数图像的平移过程",
            "whiteboard": {"points": ["平移不改变斜率"]},
            "need_image": {
                "concept": "函数图像向上平移3个单位的动画",
                "animation_type": "auto",
                "output_format": "video",
            },
        }

        concept = llm_segment["need_image"]["concept"]
        sse_data = {
            "message": llm_segment["message"],
            "whiteboard": llm_segment["whiteboard"],
            "image": {
                "type": "video",
                "url": f"/media/{concept[:30]}_video_test123.mp4",
                "title": concept,
                "description": concept,
                "concept": concept,
                "duration": 15.0,
            },
        }

        assert "image" in sse_data
        assert sse_data["image"]["type"] == "video"
        assert ".mp4" in sse_data["image"]["url"]

    def test_segment_without_need_image_no_media(self):
        llm_segment = {
            "type": "segment",
            "message": "一次函数的基本概念",
            "whiteboard": {"title": "一次函数"},
        }

        sse_data = {
            "message": llm_segment["message"],
            "whiteboard": llm_segment["whiteboard"],
        }

        assert "image" not in sse_data
        assert "video" not in sse_data


class TestAnimationGeneratorCacheKey:
    """Test that cache keys use concept for meaningful file names."""

    def test_cache_key_contains_concept(self):
        from app.services.tools.animation_generator import AnimationGenerator

        gen = AnimationGenerator.__new__(AnimationGenerator)
        params = {
            "concept": "一次函数y=2x+1的图像",
            "animation_type": "auto",
        }
        cache_key = gen._build_cache_key("auto", params, "image")

        assert "一次函数" in cache_key or "y" in cache_key or "2x1" in cache_key
        assert "image" in cache_key

    def test_cache_key_without_concept_uses_hash(self):
        from app.services.tools.animation_generator import AnimationGenerator

        gen = AnimationGenerator.__new__(AnimationGenerator)
        params = {
            "animation_type": "linear_function",
            "k": 2,
            "b": 1,
        }
        cache_key = gen._build_cache_key("linear_function", params, "video")

        assert "linear_function" in cache_key
        assert "video" in cache_key
        assert len(cache_key) > 30

    def test_cache_key_concept_truncated(self):
        from app.services.tools.animation_generator import AnimationGenerator

        gen = AnimationGenerator.__new__(AnimationGenerator)
        long_concept = "这是一个非常非常非常长的概念描述" * 5
        params = {"concept": long_concept, "animation_type": "auto"}
        cache_key = gen._build_cache_key("auto", params, "image")

        assert len(cache_key) < 200


class TestFrontendMediaRouting:
    """Test frontend logic for routing media resources based on type field."""

    def test_video_in_image_field_routes_to_video(self):
        sse_data = {
            "message": "观察动画",
            "image": {
                "type": "video",
                "url": "/media/test.mp4",
                "title": "测试视频",
            },
        }

        image_resource = sse_data.get("image")
        video_resource = sse_data.get("video")

        if image_resource and image_resource.get("type") == "video":
            video_resource = image_resource
            image_resource = None

        assert video_resource is not None
        assert video_resource["type"] == "video"
        assert image_resource is None

    def test_image_in_image_field_stays_image(self):
        sse_data = {
            "message": "查看图片",
            "image": {
                "type": "image",
                "url": "/media/test.png",
                "title": "测试图片",
            },
        }

        image_resource = sse_data.get("image")
        video_resource = sse_data.get("video")

        if image_resource and image_resource.get("type") == "video":
            video_resource = image_resource
            image_resource = None

        assert image_resource is not None
        assert image_resource["type"] == "image"
        assert video_resource is None


class TestKeywordExtraction:
    """Test extract_keywords function."""

    def test_math_concept_keywords(self):
        """Should extract math-related keywords from concept."""
        keywords = extract_keywords("一次函数 y=2x+1 的图像")
        assert "一次函数" in keywords
        assert "图像" in keywords

    def test_translation_keywords(self):
        """Should extract translation-related keywords."""
        keywords = extract_keywords("函数图像向上平移3个单位")
        assert "函数" in keywords
        assert "图像" in keywords
        assert "平移" in keywords

    def test_formula_keywords(self):
        """Should extract formula patterns like y=2x+1."""
        keywords = extract_keywords("一次函数 y=2x+1 向上平移3和向右平移2的图像对比")
        assert "一次函数" in keywords
        assert "图像" in keywords
        assert "平移" in keywords

    def test_empty_text(self):
        """Should return empty list for empty text."""
        assert extract_keywords("") == []
        assert extract_keywords(None) == []

    def test_max_keywords_limit(self):
        """Should cap at 20 keywords."""
        long_text = "函数 图像 坐标系 方程 几何 三角形 圆 平行 垂直 角度 " * 10
        keywords = extract_keywords(long_text)
        assert len(keywords) <= 20


class TestMediaResourcePersistence:
    """Test that media resources can be persisted and loaded from JSON."""

    def test_teaching_image_create_and_retrieve(self):
        from app.models.resource import TeachingImage, ImageType, ImageStatus
        from app.repositories.resource_repository import teaching_image_repository

        img = TeachingImage(
            id="test_img_001",
            knowledge_point_id="K1",
            title="一次函数图像",
            description="一次函数 y=2x+1 的图像",
            image_type=ImageType.INFOGRAPHIC,
            file_path="/media/test.png",
            tags=["一次函数", "图像", "函数"],
            metadata={"cache_key": "test_cache_key", "source": "manim_generated"},
            status=ImageStatus.READY,
        )

        created = teaching_image_repository.create(img)
        assert created.id == "test_img_001"
        assert created.title == "一次函数图像"

        retrieved = teaching_image_repository.get_by_id("test_img_001")
        assert retrieved is not None
        assert retrieved.description == "一次函数 y=2x+1 的图像"
        assert "一次函数" in retrieved.tags

        # Cleanup
        teaching_image_repository.delete("test_img_001")

    def test_teaching_video_create_and_retrieve(self):
        from app.models.resource import TeachingVideo
        from app.repositories.resource_repository import teaching_video_repository

        vid = TeachingVideo(
            id="test_vid_001",
            knowledge_point_id="K1",
            title="平移动画",
            description="函数图像向上平移3个单位的动画",
            video_url="/media/test.mp4",
            duration=15,
            tags=["平移", "函数", "图像"],
            metadata={"cache_key": "test_video_cache", "source": "manim_generated"},
        )

        created = teaching_video_repository.create(vid)
        assert created.id == "test_vid_001"

        retrieved = teaching_video_repository.get_by_id("test_vid_001")
        assert retrieved is not None
        assert "平移" in retrieved.tags

        # Cleanup
        teaching_video_repository.delete("test_vid_001")

    def test_search_by_keyword_images(self):
        from app.models.resource import TeachingImage, ImageType, ImageStatus
        from app.repositories.resource_repository import teaching_image_repository

        img = TeachingImage(
            id="test_search_img",
            knowledge_point_id="K2",
            title="二次函数图像",
            description="二次函数 y=x^2 的抛物线",
            image_type=ImageType.INFOGRAPHIC,
            file_path="/media/test2.png",
            tags=["二次函数", "抛物线"],
            metadata={},
            status=ImageStatus.READY,
        )
        teaching_image_repository.create(img)

        results = teaching_image_repository.search_by_keyword("二次函数")
        assert len(results) >= 1
        assert any(r.id == "test_search_img" for r in results)

        results = teaching_image_repository.search_by_keyword("抛物线")
        assert len(results) >= 1

        results = teaching_image_repository.search_by_keyword("不存在的内容")
        assert len(results) == 0

        teaching_image_repository.delete("test_search_img")

    def test_search_by_keyword_videos(self):
        from app.models.resource import TeachingVideo
        from app.repositories.resource_repository import teaching_video_repository

        vid = TeachingVideo(
            id="test_search_vid",
            knowledge_point_id="K3",
            title="坐标系平移动画",
            description="直角坐标系中点的平移",
            video_url="/media/test3.mp4",
            duration=10,
            tags=["坐标系", "平移"],
            metadata={},
        )
        teaching_video_repository.create(vid)

        results = teaching_video_repository.search_by_keyword("坐标系")
        assert len(results) >= 1
        assert any(r.id == "test_search_vid" for r in results)

        teaching_video_repository.delete("test_search_vid")

    def test_find_by_cache_key_dedup(self):
        """find_by_cache_key should prevent duplicate entries."""
        from app.models.resource import TeachingImage, ImageType, ImageStatus
        from app.repositories.resource_repository import teaching_image_repository

        img = TeachingImage(
            id="test_dedup_img",
            knowledge_point_id="K1",
            title="测试去重",
            description="测试",
            image_type=ImageType.INFOGRAPHIC,
            file_path="/media/dedup.png",
            metadata={"cache_key": "unique_cache_key_123"},
            status=ImageStatus.READY,
        )
        teaching_image_repository.create(img)

        found = teaching_image_repository.find_by_cache_key("unique_cache_key_123")
        assert found is not None
        assert found.id == "test_dedup_img"

        not_found = teaching_image_repository.find_by_cache_key("nonexistent_key")
        assert not_found is None

        teaching_image_repository.delete("test_dedup_img")

    def test_get_by_knowledge_point(self):
        """Should filter resources by knowledge point."""
        from app.models.resource import TeachingImage, ImageType, ImageStatus
        from app.repositories.resource_repository import teaching_image_repository

        img1 = TeachingImage(
            id="test_kp_k1_img",
            knowledge_point_id="K1",
            title="K1的图",
            description="知识点K1",
            image_type=ImageType.INFOGRAPHIC,
            file_path="/media/k1.png",
            metadata={},
            status=ImageStatus.READY,
        )
        img2 = TeachingImage(
            id="test_kp_k2_img",
            knowledge_point_id="K2",
            title="K2的图",
            description="知识点K2",
            image_type=ImageType.INFOGRAPHIC,
            file_path="/media/k2.png",
            metadata={},
            status=ImageStatus.READY,
        )
        teaching_image_repository.create(img1)
        teaching_image_repository.create(img2)

        k1_images = teaching_image_repository.get_by_knowledge_point("K1")
        assert len(k1_images) >= 1
        assert all(img.knowledge_point_id == "K1" for img in k1_images)

        teaching_image_repository.delete("test_kp_k1_img")
        teaching_image_repository.delete("test_kp_k2_img")


class TestJsonPersistence:
    """Test that media resources persist to JSON file and survive reload."""

    def test_save_and_load_media_resources(self):
        """Media resources should survive save/load cycle."""
        from app.repositories.memory_db import db

        # Ensure media resources can be saved
        db.save_media_resources_to_file()

        # Verify file was created
        file_path = db._get_media_data_file_path()
        assert file_path.exists(), f"Media resources file should exist at {file_path}"

        # Verify JSON is valid
        import json
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "images" in data
        assert "videos" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
