"""Tool processing strategies using Strategy Pattern."""

from abc import ABC, abstractmethod
import logging
from typing import Any, Optional

from app.models.tool import TeachingEvent, ToolRequest
from app.services.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolProcessStrategy(ABC):
    """Abstract base class for tool processing strategies.
    
    Each strategy handles a specific type of tool result.
    
    Design Principles:
    - Single Responsibility: Each strategy handles one tool type
    - Open/Closed: New strategies can be added without modifying existing code
    - Strategy Pattern: Interchangeable algorithms for processing
    
    Example:
        >>> strategy = ImageProcessStrategy()
        >>> if strategy.can_handle(event):
        ...     processed_event = await strategy.process(event, tool_registry, llm_service)
    """
    
    @abstractmethod
    def can_handle(self, event: TeachingEvent) -> bool:
        """Check if this strategy can handle the event.
        
        Args:
            event: Teaching event to check
            
        Returns:
            True if this strategy can handle the event
        """
        pass
    
    @abstractmethod
    async def process(
        self,
        event: TeachingEvent,
        tool_registry: ToolRegistry,
        llm_service: Any,
    ) -> TeachingEvent:
        """Process the event.
        
        Args:
            event: Teaching event to process
            tool_registry: Tool registry for executing tools
            llm_service: LLM service for processing dynamic content
            
        Returns:
            Processed teaching event
        """
        pass


class ImageProcessStrategy(ToolProcessStrategy):
    """Strategy for processing image references and generation requests.
    
    Handles two scenarios:
    1. Reference to existing image (image_id) - static resource, direct attachment
    2. Request for new image (need_image) - generate and attach
    
    Static resources are attached directly without LLM processing to save cost.
    """
    
    def can_handle(self, event: TeachingEvent) -> bool:
        """Check if event contains image reference or generation request."""
        return event.has_image_reference() or event.needs_image_generation()
    
    async def process(
        self,
        event: TeachingEvent,
        tool_registry: ToolRegistry,
        llm_service: Any,
    ) -> TeachingEvent:
        """Process image reference or generation request."""
        
        # Case 1: Reference to existing image
        if event.has_image_reference():
            logger.info(f"Processing image reference")
            tool_request = event.get_image_request()
            result = await tool_registry.execute_tool(
                "image_generation",
                tool_request
            )
            
            if result.success:
                # Static resource: directly attach to event
                event.image = result.resource
                logger.info(f"Image attached: {result.resource.get('id')}")
            else:
                logger.error(f"Failed to get image: {result.error}")
            
            return event
        
        # Case 2: Request for new image
        if event.needs_image_generation():
            logger.info(f"Processing image generation request: {event.get_generation_request()}")
            tool_request = event.get_generation_request()
            result = await tool_registry.execute_tool(
                "image_generation",
                tool_request
            )
            
            if result.success:
                # Generated image: directly attach to event
                event.image = result.resource
                logger.info(f"Image generated and attached: {result.resource.get('id')}")
            else:
                logger.error(f"Failed to generate image: {result.error}")
            
            return event
        
        return event


class VideoProcessStrategy(ToolProcessStrategy):
    """Strategy for processing video references.
    
    Videos are static resources and are attached directly without LLM processing.
    """
    
    def can_handle(self, event: TeachingEvent) -> bool:
        """Check if event contains video reference."""
        return event.has_video_reference()
    
    async def process(
        self,
        event: TeachingEvent,
        tool_registry: ToolRegistry,
        llm_service: Any,
    ) -> TeachingEvent:
        """Process video reference."""
        logger.info(f"Processing video reference")
        
        tool_request = event.get_video_request()
        result = await tool_registry.execute_tool(
            "video_generation",
            tool_request
        )
        
        if result.success:
            # Static resource: directly attach
            event.video = result.resource
            logger.info(f"Video attached: {result.resource.get('id')}")
        else:
            logger.error(f"Failed to get video: {result.error}")
        
        return event


class QuestionProcessStrategy(ToolProcessStrategy):
    """Strategy for processing question generation requests.
    
    Questions are dynamic content and require LLM processing to:
    - Organize the question in a natural way
    - Add contextual explanations
    - Ensure appropriate difficulty level
    """
    
    def can_handle(self, event: TeachingEvent) -> bool:
        """Check if event needs question."""
        return event.needs_question()
    
    async def process(
        self,
        event: TeachingEvent,
        tool_registry: ToolRegistry,
        llm_service: Any,
    ) -> TeachingEvent:
        """Process question generation request."""
        logger.info(f"Processing question generation request")
        
        # Generate question
        tool_request = event.get_question_request()
        result = await tool_registry.execute_tool(
            "question_generator",
            tool_request
        )
        
        if result.success:
            # Dynamic content: needs LLM processing
            # TODO: Call LLM to process the generated question
            event.question = result.resource
            logger.info(f"Question generated and processed: {result.resource.get('id')}")
        else:
            logger.error(f"Failed to generate question: {result.error}")
        
        return event


class InteractiveProcessStrategy(ToolProcessStrategy):
    """Strategy for processing interactive demo references.
    
    Interactive demos are typically static resources (pre-built demos)
    and are attached directly. However, they may require additional
    handling for student interaction results.
    """
    
    def can_handle(self, event: TeachingEvent) -> bool:
        """Check if event contains interactive demo reference."""
        return event.has_interactive_reference()
    
    async def process(
        self,
        event: TeachingEvent,
        tool_registry: ToolRegistry,
        llm_service: Any,
    ) -> TeachingEvent:
        """Process interactive demo reference."""
        logger.info(f"Processing interactive demo reference")
        
        tool_request = event.get_interactive_request()
        result = await tool_registry.execute_tool(
            "interactive_demo",
            tool_request
        )
        
        if result.success:
            # Attach demo to event
            event.interactive = result.resource
            logger.info(f"Interactive demo attached: {result.resource.get('id')}")
        else:
            logger.error(f"Failed to get interactive demo: {result.error}")
        
        return event


class ToolProcessStrategySelector:
    """Strategy selector for tool processing.
    
    This class:
    - Manages all registered strategies
    - Selects the appropriate strategy for each event
    - Provides a unified interface for tool processing
    
    Design Principles:
    - Strategy Pattern: Encapsulates strategy selection logic
    - Open/Closed: New strategies can be added without modification
    - Single Responsibility: Only handles strategy selection and delegation
    
    Example:
        >>> selector = ToolProcessStrategySelector()
        >>> selector.register_strategy(ImageProcessStrategy())
        >>> selector.register_strategy(VideoProcessStrategy())
        >>> 
        >>> processed_event = await selector.select_and_process(
        ...     event, tool_registry, llm_service
        ... )
    """
    
    def __init__(self):
        """Initialize the strategy selector."""
        self.strategies: list[ToolProcessStrategy] = []
        logger.info("ToolProcessStrategySelector initialized")
    
    def register_strategy(self, strategy: ToolProcessStrategy) -> None:
        """Register a strategy.
        
        Args:
            strategy: Strategy to register
            
        Example:
            >>> selector.register_strategy(ImageProcessStrategy())
        """
        self.strategies.append(strategy)
        logger.info(f"Strategy registered: {strategy.__class__.__name__}")
    
    async def select_and_process(
        self,
        event: TeachingEvent,
        tool_registry: ToolRegistry,
        llm_service: Any,
    ) -> TeachingEvent:
        """Select appropriate strategy and process the event.
        
        This method:
        1. Iterates through all registered strategies
        2. Finds the first strategy that can handle the event
        3. Executes the strategy's process method
        
        Args:
            event: Teaching event to process
            tool_registry: Tool registry for executing tools
            llm_service: LLM service for processing dynamic content
            
        Returns:
            Processed teaching event (or original event if no strategy matches)
            
        Example:
            >>> processed_event = await selector.select_and_process(
            ...     event, tool_registry, llm_service
            ... )
        """
        # Find the first strategy that can handle the event
        for strategy in self.strategies:
            if strategy.can_handle(event):
                logger.info(f"Using strategy: {strategy.__class__.__name__}")
                return await strategy.process(event, tool_registry, llm_service)
        
        # No strategy can handle the event, return as-is
        logger.info(f"No strategy found for event type: {event.event_type}")
        return event
    
    def get_registered_strategies(self) -> list[str]:
        """Get names of all registered strategies.
        
        Returns:
            List of strategy class names
        """
        return [strategy.__class__.__name__ for strategy in self.strategies]


# Global instance with pre-registered strategies
def build_default_strategy_selector() -> ToolProcessStrategySelector:
    """Build and return a strategy selector with default strategies.
    
    Returns:
        Strategy selector with all default strategies registered
    """
    selector = ToolProcessStrategySelector()
    
    # Register default strategies
    selector.register_strategy(ImageProcessStrategy())
    selector.register_strategy(VideoProcessStrategy())
    selector.register_strategy(QuestionProcessStrategy())
    selector.register_strategy(InteractiveProcessStrategy())
    
    return selector


# Global instance
strategy_selector = build_default_strategy_selector()
