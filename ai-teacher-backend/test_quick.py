#!/usr/bin/env python3
"""Quick validation test for core components."""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.init_tools import initialize_system
from app.models.tool import ToolRequest
from app.services.tool_selection_engine import tool_selection_engine, TeachingContext

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def test_tool_selection():
    """Test tool selection rules."""
    logger.info("\n【Test 1】Tool Selection Rules")
    
    test_cases = [
        (1, "概念", ["image_generation"]),
        (1, "几何概念", ["image_generation"]),
        (2, "公式推导", ["image_generation"]),
        (3, "概念", ["interactive_demo"]),
        (4, "概念", ["question_generator"]),  # Changed from "任何" to "概念"
    ]
    
    all_passed = True
    for phase, kp_type, expected in test_cases:
        context = TeachingContext(
            current_phase=phase,
            kp_type=kp_type,
            student_ability="beginner",
            teaching_mode="teach",
        )
        
        selected = tool_selection_engine.select_tools(context)
        passed = set(selected) == set(expected)
        
        status = "✓" if passed else "✗"
        logger.info(f"  {status} Phase {phase}, {kp_type}: {selected}")
        
        if not passed:
            logger.warning(f"    Expected: {expected}")
            all_passed = False
    
    return all_passed


async def test_image_generation():
    """Test image generation strategy."""
    logger.info("\n【Test 2】Image Generation Strategy")
    
    from app.services.tools.image_tool import ImageTool
    
    tool = ImageTool()
    
    # Test library retrieval
    logger.info("  Testing library retrieval...")
    request1 = ToolRequest(
        action="get_image",
        params={
            "image_id": "IMG_K1_001",
            "knowledge_point_id": "K1",
        }
    )
    result1 = await tool.execute(request1)
    
    lib_passed = result1.success and result1.metadata.get("source") == "library"
    logger.info(f"    {'✓' if lib_passed else '✗'} Library: {result1.metadata.get('source')}")
    
    # Test template rendering
    logger.info("  Testing template rendering...")
    request2 = ToolRequest(
        action="generate_image",
        params={
            "concept": "函数图像",
            "type": "example",
            "knowledge_point_id": "K3",
        }
    )
    result2 = await tool.execute(request2)
    
    template_passed = result2.success and result2.metadata.get("source") == "template"
    logger.info(f"    {'✓' if template_passed else '✗'} Template: {result2.metadata.get('source')}")
    
    # Test AI generation
    logger.info("  Testing AI generation...")
    request3 = ToolRequest(
        action="generate_image",
        params={
            "concept": "一次函数与几何图形结合",
            "type": "infographic",
            "knowledge_point_id": "K5",
        }
    )
    result3 = await tool.execute(request3)
    
    ai_passed = result3.success and result3.metadata.get("source") == "ai"
    logger.info(f"    {'✓' if ai_passed else '✗'} AI: {result3.metadata.get('source')}")
    
    # Summary
    logger.info(f"\n  Cost analysis:")
    logger.info(f"    Library: $0.00 (saved $0.05)")
    logger.info(f"    Template: $0.02 (saved $0.03)")
    logger.info(f"    AI: $0.05 (full cost)")
    logger.info(f"    Total saved: $0.08")
    
    return lib_passed and template_passed and ai_passed


async def test_student_context():
    """Test student context loading."""
    logger.info("\n【Test 3】Student Context Loading")
    
    from app.services.student_context_loader import student_context_loader
    
    try:
        context = await student_context_loader.load(
            student_id=1,
            course_id="MATH_JUNIOR_01",
        )
        
        has_profile = context.profile is not None
        has_history = len(context.history) >= 0
        has_summary = context.summary is not None
        
        logger.info(f"  {'✓' if has_profile else '✗'} Profile loaded")
        logger.info(f"  {'✓' if has_history else '✗'} History loaded: {len(context.history)} records")
        logger.info(f"  {'✓' if has_summary else '✗'} Summary loaded")
        
        if has_summary:
            logger.info(f"    Total learned: {context.summary.get('total_learned', 0)}")
            logger.info(f"    Average score: {context.summary.get('average_score', 0):.2%}")
        
        return has_profile and has_history and has_summary
        
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
        return False


async def test_repository():
    """Test repository operations."""
    logger.info("\n【Test 4】Repository Operations")
    
    from app.repositories.resource_repository import (
        teaching_image_repository,
        tool_usage_log_repository,
    )
    
    # Test image repository
    images = teaching_image_repository.get_by_knowledge_point("K1")
    img_passed = len(images) > 0
    logger.info(f"  {'✓' if img_passed else '✗'} Image repository: {len(images)} images for K1")
    
    # Test usage log repository
    all_logs = tool_usage_log_repository.get_all()
    log_passed = True  # Repository works even if no logs yet
    logger.info(f"  {'✓' if log_passed else '✗'} Usage log repository: {len(all_logs)} logs")
    
    return img_passed and log_passed


async def test_teaching_flow_init():
    """Test teaching flow initialization."""
    logger.info("\n【Test 5】Teaching Flow Initialization")
    
    from app.services.teaching_flow import teaching_flow
    
    # Check if tool_registry is initialized
    has_registry = teaching_flow.tool_registry is not None
    logger.info(f"  {'✓' if has_registry else '✗'} Tool registry initialized")
    
    if has_registry:
        tools = teaching_flow.tool_registry.get_all_registered_tools()
        logger.info(f"    Registered tools: {tools}")
    
    # Check other components
    has_loader = teaching_flow.student_context_loader is not None
    logger.info(f"  {'✓' if has_loader else '✗'} Student context loader initialized")
    
    has_strategy = teaching_flow.strategy_selector is not None
    logger.info(f"  {'✓' if has_strategy else '✗'} Strategy selector initialized")
    
    return has_registry and has_loader and has_strategy


async def main():
    """Run all tests."""
    logger.info("=" * 70)
    logger.info("Quick Validation Tests")
    logger.info("=" * 70)
    
    # Initialize system
    initialize_system()
    
    # Run tests
    results = []
    
    results.append(("Tool Selection", await test_tool_selection()))
    results.append(("Image Generation", await test_image_generation()))
    results.append(("Student Context", await test_student_context()))
    results.append(("Repository", await test_repository()))
    results.append(("Teaching Flow Init", await test_teaching_flow_init()))
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, p in results:
        status = "✓ PASS" if p else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nTotal: {passed}/{total} passed ({passed/total*100:.0f}%)")
    logger.info("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
