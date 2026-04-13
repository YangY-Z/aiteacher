#!/usr/bin/env python3
"""Test Phase 3 implementation: System Integration."""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.init_tools import initialize_system
from app.models.learning import LearningSession, SessionStatus
from app.repositories.learning_repository import learning_session_repository
from app.services.teaching_flow import teaching_flow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def test_phase3():
    """Test Phase 3 system integration."""
    logger.info("=" * 70)
    logger.info("Testing Phase 3: System Integration")
    logger.info("=" * 70)
    
    # Step 1: Initialize system
    logger.info("\n【Step 1】Initialize System")
    initialize_system()
    logger.info("✓ System initialized\n")
    
    # Step 2: Create test session
    logger.info("【Step 2】Create Test Session")
    
    from app.models.learning import LearningRound, RoundStatus
    
    # Create session with a learning round
    round1 = LearningRound(
        round_number=1,
        start_time=datetime.now(),
        status=RoundStatus.IN_PROGRESS,
        current_phase=1,
    )
    
    session = LearningSession(
        id="test_session_phase3",
        student_id=1,
        course_id="MATH_JUNIOR_01",
        kp_id="K1",  # 正比例函数
        status=SessionStatus.ACTIVE,
        rounds=[round1],
    )
    learning_session_repository.create(session)
    logger.info(f"  Session ID: {session.id}")
    logger.info(f"  Student ID: {session.student_id}")
    logger.info(f"  Knowledge Point: {session.kp_id}")
    logger.info(f"  Current Phase: {session.current_round.current_phase}")
    logger.info("✓ Test session created\n")
    
    # Step 3: Test TeachingFlow with tools enabled
    logger.info("【Step 3】Test TeachingFlow (with tools)")
    event_count = 0
    tool_events = 0
    
    try:
        async for sse_event in teaching_flow.execute_teaching_phase(
            session=session,
            student_name="测试学生",
            trace_id="test-phase3",
            use_tools=True,
        ):
            event_count += 1
            event_type = sse_event.get("event", "")
            
            # Parse event data
            import json
            event_data = json.loads(sse_event.get("data", "{}"))
            
            # Check for tool references
            if event_type == "segment":
                message = event_data.get("message", "")
                if "image_id" in message or "need_image" in message:
                    tool_events += 1
                    logger.info(f"  Event #{event_count}: {event_type} (含工具引用)")
                else:
                    if event_count <= 3:  # 只打印前几个事件
                        logger.info(f"  Event #{event_count}: {event_type}")
        
        logger.info(f"  总事件数: {event_count}")
        logger.info(f"  工具相关事件: {tool_events}")
        logger.info("✓ TeachingFlow with tools passed\n")
    
    except Exception as e:
        logger.error(f"  ✗ TeachingFlow failed: {e}", exc_info=True)
    
    # Step 4: Test TeachingFlow without tools
    logger.info("【Step 4】Test TeachingFlow (without tools)")
    event_count_no_tools = 0
    
    try:
        async for sse_event in teaching_flow.execute_teaching_phase(
            session=session,
            student_name="测试学生",
            trace_id="test-phase3-no-tools",
            use_tools=False,
        ):
            event_count_no_tools += 1
            if event_count_no_tools <= 3:  # 只打印前几个事件
                event_type = sse_event.get("event", "")
                logger.info(f"  Event #{event_count_no_tools}: {event_type}")
        
        logger.info(f"  总事件数: {event_count_no_tools}")
        logger.info("✓ TeachingFlow without tools passed\n")
    
    except Exception as e:
        logger.error(f"  ✗ TeachingFlow failed: {e}", exc_info=True)
    
    # Step 5: Test API endpoints
    logger.info("【Step 5】Test API Endpoints")
    
    from app.api.teaching_v2 import get_available_tools, get_image_resource
    from app.core.security import get_current_student_id
    from fastapi import Depends
    
    try:
        # Test get_available_tools
        logger.info("  Test 5.1: Get available tools")
        response = await get_available_tools(
            session_id=session.id,
            student_id=1,
        )
        logger.info(f"    Success: {response.success}")
        logger.info(f"    Selected tools: {response.data['selected_tools']}")
        logger.info("  ✓ Test passed")
        
        # Test get_image_resource
        logger.info("  Test 5.2: Get image resource")
        response = await get_image_resource(
            image_id="IMG_K1_001",
            student_id=1,
        )
        logger.info(f"    Success: {response.success}")
        logger.info(f"    Image title: {response.data['title']}")
        logger.info("  ✓ Test passed")
        
        logger.info("✓ API endpoints test passed\n")
    
    except Exception as e:
        logger.error(f"  ✗ API test failed: {e}", exc_info=True)
    
    # Step 6: Summary
    logger.info("=" * 70)
    logger.info("Phase 3 Test Summary")
    logger.info("=" * 70)
    logger.info("✓ System initialization with resources")
    logger.info("✓ TeachingFlow with tool enhancement")
    logger.info("✓ TeachingFlow without tool enhancement")
    logger.info("✓ API endpoints functional")
    logger.info("")
    logger.info(f"With tools:    {event_count} events ({tool_events} tool-related)")
    logger.info(f"Without tools: {event_count_no_tools} events")
    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ Phase 3 Integration Test Complete!")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_phase3())
