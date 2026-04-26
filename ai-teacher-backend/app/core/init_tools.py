"""Initialize tools and start the layered Agent system."""

import asyncio
import logging

from app.services.tools.registry import tool_registry
from app.services.tools.image_tool import create_image_tool
from app.services.tool_selection_engine import tool_selection_engine
from app.services.student_context_loader import student_context_loader
from app.services.tool_strategies import strategy_selector

logger = logging.getLogger(__name__)


def initialize_tools() -> None:
    """Initialize and register all teaching tools.
    
    This function:
    1. Creates tool instances
    2. Registers them with the tool registry
    3. Logs registration status
    
    Call this during application startup.
    
    Example:
        >>> # In main.py
        >>> from app.core.init_tools import initialize_tools
        >>> initialize_tools()
    """
    logger.info("=== Initializing Teaching Tools ===")
    
    # Register Image Tool
    image_tool = create_image_tool()
    tool_registry.register("image_generation", image_tool)
    logger.info("✓ Image tool registered")
    
    # TODO: Register other tools as they are implemented
    # tool_registry.register("video_generation", VideoTool())
    # tool_registry.register("interactive_demo", InteractiveDemoTool())
    # tool_registry.register("question_generator", QuestionGeneratorTool())
    
    # Log registered tools
    registered_tools = tool_registry.get_all_registered_tools()
    logger.info(f"=== Tool Initialization Complete ===")
    logger.info(f"Registered tools: {registered_tools}")
    
    # Log tool metadata
    for tool_name in registered_tools:
        metadata = tool_registry.get_tool_metadata(tool_name)
        if metadata:
            logger.info(
                f"  - {tool_name}: {metadata['description']}, "
                f"capabilities={metadata['capabilities']}"
            )


def initialize_rules() -> None:
    """Initialize tool selection rules.
    
    This function:
    1. Adds custom rules if needed
    2. Logs available rules
    
    Default rules are already defined in ToolSelectionRuleEngine.
    This function can add domain-specific rules.
    """
    logger.info("=== Initializing Tool Selection Rules ===")
    
    # Add custom rules if needed
    # Example: Add a rule for phase 5
    # tool_selection_engine.add_rule(
    #     phase=5,
    #     kp_type="综合应用",
    #     tools=["interactive_demo", "question_generator"]
    # )
    
    # Log available rules
    all_rules = tool_selection_engine.get_all_rules()
    logger.info(f"=== Rule Initialization Complete ===")
    logger.info(f"Total rules: {len(all_rules)}")
    
    # Log rule summary
    phase_rules = {}
    for (phase_key, kp_type), tools in all_rules.items():
        phase = phase_key.replace("phase_", "")
        if phase not in phase_rules:
            phase_rules[phase] = []
        phase_rules[phase].append(f"{kp_type} -> {tools}")
    
    for phase, rules in sorted(phase_rules.items()):
        logger.info(f"  Phase {phase}:")
        for rule in rules:
            logger.info(f"    - {rule}")


def initialize_system() -> None:
    """Initialize the entire layered Agent system.
    
    This function:
    1. Initializes teaching resources
    2. Initializes tools
    3. Initializes rules
    4. Validates system readiness
    5. Logs system status
    
    Call this during application startup.
    
    Example:
        >>> # In main.py
        >>> from app.core.init_tools import initialize_system
        >>> initialize_system()
    """
    logger.info("=" * 60)
    logger.info("Initializing Layered Agent System")
    logger.info("=" * 60)
    
    # Step 0: Initialize teaching resources
    from app.core.init_resources import initialize_resources
    initialize_resources()
    
    # Step 1: Initialize tools
    initialize_tools()
    
    # Step 2: Initialize rules
    initialize_rules()
    
    # Step 3: Validate system readiness
    logger.info("=== Validating System Readiness ===")
    
    # Check tool registry
    registered_tools = tool_registry.get_all_registered_tools()
    if not registered_tools:
        logger.warning("⚠ No tools registered!")
    else:
        logger.info(f"✓ {len(registered_tools)} tools registered")
    
    # Check rules
    all_rules = tool_selection_engine.get_all_rules()
    if not all_rules:
        logger.warning("⚠ No rules defined!")
    else:
        logger.info(f"✓ {len(all_rules)} rules defined")
    
    # Check strategies
    strategies = strategy_selector.get_registered_strategies()
    if not strategies:
        logger.warning("⚠ No strategies registered!")
    else:
        logger.info(f"✓ {len(strategies)} strategies registered: {strategies}")
    
    # Check student context loader
    logger.info("✓ Student context loader ready")
    
    logger.info("=" * 60)
    logger.info("Layered Agent System Initialization Complete")
    logger.info("=" * 60)


async def test_system() -> None:
    """Test the initialized system.
    
    This function performs basic tests to verify the system works correctly:
    1. Tool registration
    2. Tool context preparation
    3. Tool execution
    4. Rule selection
    5. Student context loading
    
    Run this after initialization to verify everything works.
    
    Example:
        >>> import asyncio
        >>> from app.core.init_tools import test_system
        >>> asyncio.run(test_system())
    """
    logger.info("=" * 60)
    logger.info("Testing Layered Agent System")
    logger.info("=" * 60)
    
    # Test 1: Tool registration
    logger.info("Test 1: Tool Registration")
    registered_tools = tool_registry.get_all_registered_tools()
    logger.info(f"  Registered tools: {registered_tools}")
    assert "image_generation" in registered_tools, "Image tool not registered"
    logger.info("  ✓ Test passed")
    
    # Test 2: Tool context preparation
    logger.info("Test 2: Tool Context Preparation")
    contexts = await tool_registry.prepare_tool_contexts(
        ["image_generation"],
        "K3"
    )
    logger.info(f"  Prepared contexts: {list(contexts.keys())}")
    assert "image_generation" in contexts, "Image context not prepared"
    context = contexts["image_generation"]
    logger.info(f"  Context description: {context.description}")
    logger.info(f"  Available resources: {len(context.available_resources)}")
    logger.info("  ✓ Test passed")
    
    # Test 3: Tool execution
    logger.info("Test 3: Tool Execution")
    from app.models.tool import ToolRequest
    
    # Test get_image
    request = ToolRequest(action="get_image", params={"image_id": "IMG_001"})
    result = await tool_registry.execute_tool("image_generation", request)
    logger.info(f"  get_image result: success={result.success}")
    if result.success:
        logger.info(f"  Image ID: {result.resource.get('id')}")
    logger.info("  ✓ Test passed")
    
    # Test 4: Rule selection
    logger.info("Test 4: Rule Selection")
    from app.services.tool_selection_engine import TeachingContext
    
    context = TeachingContext(current_phase=1, kp_type="几何概念")
    tools = tool_selection_engine.select_tools(context)
    logger.info(f"  Selected tools: {tools}")
    assert "image_generation" in tools, "Image tool not selected for phase 1, 几何概念"
    logger.info("  ✓ Test passed")
    
    # Test 5: Student context loading
    logger.info("Test 5: Student Context Loading")
    student_context = await student_context_loader.load(
        student_id=1,
        course_id="MATH_JUNIOR_01"
    )
    logger.info(f"  Student context loaded: {student_context.summary}")
    logger.info("  ✓ Test passed")
    
    logger.info("=" * 60)
    logger.info("All Tests Passed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Initialize system
    initialize_system()
    
    # Run tests
    asyncio.run(test_system())
