"""Tool registry for managing all teaching tools."""

import logging
from typing import Any, Optional

from app.models.tool import ToolContext, ToolRequest, ToolResult
from app.services.tools.base import TeachingTool

logger = logging.getLogger(__name__)


class ToolNotFoundError(Exception):
    """Raised when a requested tool is not found in the registry."""
    pass


class ToolRegistry:
    """Registry for managing all teaching tools.
    
    This class provides:
    - Centralized tool management
    - Tool registration and discovery
    - Tool context preparation
    - Tool execution delegation
    
    Design Principles:
    - Single Responsibility: Only manages tool registration and delegation
    - Open/Closed: New tools can be registered without modifying this class
    - Dependency Injection: Tools are injected via register()
    
    Example:
        >>> registry = ToolRegistry()
        >>> registry.register("image_generation", ImageTool())
        >>> registry.register("video_generation", VideoTool())
        >>> 
        >>> # Get all registered tools
        >>> tools = registry.get_all_registered_tools()
        >>> print(tools)
        ["image_generation", "video_generation"]
        >>> 
        >>> # Execute a tool
        >>> result = await registry.execute_tool("image_generation", request)
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self.tools: dict[str, TeachingTool] = {}
        logger.info("ToolRegistry initialized")
    
    def register(self, tool_name: str, tool: TeachingTool) -> None:
        """Register a tool.
        
        Args:
            tool_name: Unique name for the tool (e.g., "image_generation")
            tool: Tool instance implementing TeachingTool
            
        Example:
            >>> registry.register("image_generation", ImageTool())
            >>> registry.register("video_generation", VideoTool())
        """
        if tool_name in self.tools:
            logger.warning(f"Tool '{tool_name}' already registered, overwriting")
        
        self.tools[tool_name] = tool
        logger.info(f"Tool registered: {tool_name}")
    
    def unregister(self, tool_name: str) -> bool:
        """Unregister a tool.
        
        Args:
            tool_name: Name of the tool to unregister
            
        Returns:
            True if tool was unregistered, False if not found
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Tool unregistered: {tool_name}")
            return True
        return False
    
    def get_tool(self, tool_name: str) -> Optional[TeachingTool]:
        """Get a tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool instance if found, None otherwise
        """
        return self.tools.get(tool_name)
    
    def get_all_registered_tools(self) -> list[str]:
        """Get names of all registered tools.
        
        Returns:
            List of registered tool names
        """
        return list(self.tools.keys())
    
    async def prepare_tool_contexts(
        self,
        tool_names: list[str],
        kp_id: str,
    ) -> dict[str, ToolContext]:
        """Prepare tool contexts for a knowledge point.
        
        This method:
        1. Loads contexts for all specified tools
        2. Filters to only registered tools
        3. Returns a dictionary mapping tool names to contexts
        
        Args:
            tool_names: List of tool names to prepare contexts for
            kp_id: Knowledge point ID
            
        Returns:
            Dictionary mapping tool names to their contexts
            
        Example:
            >>> contexts = await registry.prepare_tool_contexts(
            ...     ["image_generation", "video_generation"],
            ...     "K3"
            ... )
            >>> print(contexts["image_generation"].description)
            "可用图片资源"
        """
        contexts = {}
        
        for tool_name in tool_names:
            if tool_name not in self.tools:
                logger.warning(f"Tool '{tool_name}' not registered, skipping")
                continue
            
            try:
                tool = self.tools[tool_name]
                context = await tool.get_context(kp_id)
                contexts[tool_name] = context
                logger.info(f"Prepared context for tool '{tool_name}', kp_id={kp_id}")
            except Exception as e:
                logger.error(f"Failed to prepare context for tool '{tool_name}': {e}")
                # Continue with other tools instead of failing
        
        return contexts
    
    async def execute_tool(
        self,
        tool_name: str,
        tool_request: ToolRequest,
    ) -> ToolResult:
        """Execute a tool with the given request.
        
        Args:
            tool_name: Name of the tool to execute
            tool_request: Request with action and parameters
            
        Returns:
            ToolResult with success status and resource
            
        Raises:
            ToolNotFoundError: If tool is not registered
            
        Example:
            >>> request = ToolRequest(action="get_image", params={"image_id": "IMG_001"})
            >>> result = await registry.execute_tool("image_generation", request)
            >>> if result.success:
            ...     print(result.resource)
        """
        if tool_name not in self.tools:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found in registry")
        
        tool = self.tools[tool_name]
        
        try:
            result = await tool.execute(tool_request)
            logger.info(
                f"Executed tool '{tool_name}', action={tool_request.action}, "
                f"success={result.success}"
            )
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}, error={e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"tool_name": tool_name, "action": tool_request.action}
            )
    
    def get_tool_metadata(self, tool_name: str) -> Optional[dict[str, Any]]:
        """Get metadata for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool metadata as dictionary, or None if not found
        """
        if tool_name not in self.tools:
            return None
        
        tool = self.tools[tool_name]
        metadata = tool.get_metadata()
        
        return {
            "name": metadata.name,
            "description": metadata.description,
            "capabilities": metadata.capabilities,
            "resource_types": [rt.value for rt in metadata.resource_types],
        }
    
    def get_all_tools_metadata(self) -> list[dict[str, Any]]:
        """Get metadata for all registered tools.
        
        Returns:
            List of tool metadata dictionaries
        """
        return [
            self.get_tool_metadata(tool_name)
            for tool_name in self.tools.keys()
        ]


# Global tool registry instance
tool_registry = ToolRegistry()
