"""Base class for all teaching tools."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.models.tool import ToolContext, ToolRequest, ToolResult, ToolMetadata


class TeachingTool(ABC):
    """Abstract base class for all teaching tools.
    
    All tools must implement this interface to ensure consistency and extensibility.
    
    Design Principles:
    - Single Responsibility: Each tool handles one type of resource
    - Open/Closed: New tools can be added without modifying existing code
    - Dependency Inversion: High-level modules depend on this abstraction
    """
    
    @abstractmethod
    async def get_context(self, kp_id: str) -> ToolContext:
        """Get tool context for injection into prompts.
        
        This method should:
        1. Query available resources for the given knowledge point
        2. Return context with available resources and usage instructions
        3. Be efficient - only load what's needed
        
        Args:
            kp_id: Knowledge point ID to get context for
            
        Returns:
            ToolContext with available resources and usage guide
            
        Example:
            >>> tool = ImageTool()
            >>> context = await tool.get_context("K3")
            >>> print(context.description)
            "可用图片资源"
            >>> print(context.available_resources)
            [{"id": "IMG_001", "description": "...", "type": "infographic"}]
        """
        pass
    
    @abstractmethod
    async def execute(self, request: ToolRequest) -> ToolResult:
        """Execute a tool action.
        
        This method should:
        1. Validate the request parameters
        2. Execute the requested action
        3. Return the result (resource or error)
        4. Handle errors gracefully
        
        Args:
            request: ToolRequest with action and parameters
            
        Returns:
            ToolResult with success status and resource (if successful)
            
        Example:
            >>> tool = ImageTool()
            >>> request = ToolRequest(action="get_image", params={"image_id": "IMG_001"})
            >>> result = await tool.execute(request)
            >>> if result.success:
            ...     print(result.resource)
            {"id": "IMG_001", "url": "https://...", "description": "..."}
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata describing its capabilities.
        
        This method should:
        1. Return metadata with tool name, description, and capabilities
        2. Be idempotent - return the same metadata each time
        3. Be fast - no heavy computation
        
        Returns:
            ToolMetadata with tool capabilities
            
        Example:
            >>> tool = ImageTool()
            >>> metadata = tool.get_metadata()
            >>> print(metadata.name)
            "image_generation"
            >>> print(metadata.capabilities)
            ["图片库检索", "模板渲染", "AI生成"]
        """
        pass
    
    def __repr__(self) -> str:
        """String representation of the tool."""
        metadata = self.get_metadata()
        return f"{self.__class__.__name__}(name={metadata.name})"
