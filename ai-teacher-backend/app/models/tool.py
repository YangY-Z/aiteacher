"""Tool-related domain models for the layered Agent architecture."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ToolType(str, Enum):
    """Types of teaching tools."""

    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    INTERACTIVE_DEMO = "interactive_demo"
    QUESTION_GENERATOR = "question_generator"


class ResourceType(str, Enum):
    """Types of resources that tools can provide."""

    IMAGE = "image"
    VIDEO = "video"
    INTERACTIVE = "interactive"
    QUESTION = "question"


@dataclass
class ToolMetadata:
    """Metadata describing a tool's capabilities.
    
    Args:
        name: Tool name (e.g., "image_generation")
        description: Human-readable description
        capabilities: List of tool capabilities
        resource_types: Types of resources this tool provides
    """
    
    name: str
    description: str
    capabilities: list[str] = field(default_factory=list)
    resource_types: list[ResourceType] = field(default_factory=list)


@dataclass
class ToolContext:
    """Context information for a tool to be injected into prompts.
    
    Args:
        tool_name: Name of the tool
        description: Description of available resources
        available_resources: List of available resources
        usage_guide: Instructions on how to use the tool
    """
    
    tool_name: str
    description: str
    available_resources: list[dict[str, Any]] = field(default_factory=list)
    usage_guide: str = ""
    
    def to_prompt_str(self) -> str:
        """Convert to a string suitable for inclusion in prompts."""
        lines = [f"【{self.description}】"]
        
        if self.available_resources:
            lines.append("可用资源:")
            for resource in self.available_resources:
                resource_id = resource.get("id", "")
                resource_type = resource.get("type", "")
                resource_desc = resource.get("description", "")
                lines.append(f"- ID: {resource_id}, 类型: {resource_type}, 描述: {resource_desc}")
        
        if self.usage_guide:
            lines.append(f"\n{self.usage_guide}")
        
        return "\n".join(lines)


@dataclass
class ToolRequest:
    """Request to execute a tool.
    
    Args:
        action: Action to perform (e.g., "get_image", "generate_image")
        params: Parameters for the action
    """
    
    action: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """Result of a tool execution.
    
    Args:
        success: Whether the execution was successful
        resource: The resource produced by the tool (if any)
        error: Error message if execution failed
        metadata: Additional metadata about the result
    """
    
    success: bool
    resource: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TeachingEvent:
    """Event produced during teaching flow.
    
    Represents a single segment of teaching content, possibly with tool references.
    
    Args:
        event_type: Type of event (segment, complete, etc.)
        message: Text content of the event
        image: Image resource (if any)
        video: Video resource (if any)
        interactive: Interactive demo resource (if any)
        question: Question resource (if any)
        next_action: Next action for the flow (e.g., "wait_for_student")
    """
    
    event_type: str = "segment"
    message: str = ""
    image: Optional[dict[str, Any]] = None
    video: Optional[dict[str, Any]] = None
    interactive: Optional[dict[str, Any]] = None
    question: Optional[dict[str, Any]] = None
    next_action: str = ""
    
    def has_image_reference(self) -> bool:
        """Check if this event references an image."""
        # Check if message contains image_id reference
        return "image_id" in self.message.lower() or self.image is not None
    
    def needs_image_generation(self) -> bool:
        """Check if this event requests image generation."""
        return "need_image" in self.message.lower()
    
    def has_video_reference(self) -> bool:
        """Check if this event references a video."""
        return "video_id" in self.message.lower() or self.video is not None
    
    def needs_question(self) -> bool:
        """Check if this event needs a question."""
        return "need_question" in self.message.lower() or self.question is not None
    
    def has_interactive_reference(self) -> bool:
        """Check if this event references an interactive demo."""
        return "demo_id" in self.message.lower() or self.interactive is not None
    
    def get_image_request(self) -> ToolRequest:
        """Extract image request from the event."""
        # Parse message to extract image_id
        import json
        import re
        
        try:
            # Try to parse message as JSON
            data = json.loads(self.message)
            image_id = data.get("image_id", "")
            return ToolRequest(action="get_image", params={"image_id": image_id})
        except (json.JSONDecodeError, AttributeError):
            # Fallback: extract image_id using regex
            match = re.search(r'"image_id":\s*"([^"]+)"', self.message)
            if match:
                return ToolRequest(action="get_image", params={"image_id": match.group(1)})
        
        return ToolRequest(action="get_image", params={})
    
    def get_generation_request(self) -> ToolRequest:
        """Extract image generation request from the event."""
        import json
        import re

        try:
            data = json.loads(self.message)
            need_image = data.get("need_image", {})
            # Pass all need_image params through (k, b, output_format, etc.)
            params = dict(need_image)
            params.setdefault("concept", "")
            params.setdefault("animation_type", "auto")
            # If concept is empty but message field has content, use it as fallback
            if not params.get("concept"):
                params["concept"] = data.get("message", "")
            return ToolRequest(
                action="generate_image",
                params=params,
            )
        except (json.JSONDecodeError, AttributeError):
            # Fallback: extract using regex - handle nested braces properly
            match = re.search(r'"need_image":\s*(\{[^}]*\})', self.message)
            if not match:
                # Try greedy match for simple cases
                match = re.search(r'"need_image":\s*(\{.*?\})', self.message)
            if match:
                try:
                    need_image = json.loads(match.group(1))
                    params = dict(need_image)
                    params.setdefault("concept", "")
                    params.setdefault("animation_type", "auto")
                    # If concept is empty, try extracting from message field in the JSON
                    msg_match = re.search(r'"message":\s*"([^"]*)"', self.message)
                    if not params.get("concept") and msg_match:
                        params["concept"] = msg_match.group(1)
                    return ToolRequest(
                        action="generate_image",
                        params=params,
                    )
                except json.JSONDecodeError:
                    pass

        return ToolRequest(action="generate_image", params={})
    
    def get_video_request(self) -> ToolRequest:
        """Extract video request from the event."""
        import json
        import re
        
        try:
            data = json.loads(self.message)
            video_id = data.get("video_id", "")
            return ToolRequest(action="get_video", params={"video_id": video_id})
        except (json.JSONDecodeError, AttributeError):
            match = re.search(r'"video_id":\s*"([^"]+)"', self.message)
            if match:
                return ToolRequest(action="get_video", params={"video_id": match.group(1)})
        
        return ToolRequest(action="get_video", params={})
    
    def get_question_request(self) -> ToolRequest:
        """Extract question generation request from the event."""
        import json
        
        try:
            data = json.loads(self.message)
            need_question = data.get("need_question", {})
            return ToolRequest(
                action="generate_question",
                params={
                    "difficulty": need_question.get("difficulty", "medium"),
                    "type": need_question.get("type", "choice"),
                }
            )
        except (json.JSONDecodeError, AttributeError):
            pass
        
        return ToolRequest(action="generate_question", params={})
    
    def get_interactive_request(self) -> ToolRequest:
        """Extract interactive demo request from the event."""
        import json
        import re
        
        try:
            data = json.loads(self.message)
            demo_id = data.get("demo_id", "")
            return ToolRequest(action="get_demo", params={"demo_id": demo_id})
        except (json.JSONDecodeError, AttributeError):
            match = re.search(r'"demo_id":\s*"([^"]+)"', self.message)
            if match:
                return ToolRequest(action="get_demo", params={"demo_id": match.group(1)})
        
        return ToolRequest(action="get_demo", params={})


@dataclass
class StudentContext:
    """Complete student context for personalized teaching.
    
    Args:
        profile: Student profile for the current course
        history: Recent learning records
        recent_dialogues: Recent dialogue history
        summary: Aggregated summary of student performance
    """
    
    profile: Optional[Any] = None  # StudentProfile
    history: list[Any] = field(default_factory=list)  # List[LearningRecord]
    recent_dialogues: list[dict[str, str]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default summary if not provided."""
        if not self.summary:
            self.summary = {
                "total_learned": 0,
                "average_score": 0.0,
                "struggle_areas": [],
                "learning_velocity": 0.5,
            }
