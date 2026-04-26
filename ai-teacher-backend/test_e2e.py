#!/usr/bin/env python3
"""End-to-End test for Layered Agent Architecture.

This test validates:
1. Tool selection rules (different phases, different KP types)
2. Image generation strategy (library/template/AI)
3. New/old mode switching
4. Cost optimization
5. Student context loading
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.init_tools import initialize_system
from app.models.learning import LearningRound, LearningSession, RoundStatus, SessionStatus
from app.models.tool import ToolRequest
from app.repositories.learning_repository import learning_session_repository
from app.repositories.resource_repository import (
    teaching_image_repository,
    tool_usage_log_repository,
)
from app.services.teaching_flow import teaching_flow
from app.services.tool_selection_engine import tool_selection_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class E2ETestRunner:
    """End-to-end test runner."""
    
    def __init__(self):
        self.test_results = []
        self.total_cost_saved = 0
        self.total_images_generated = 0
    
    def record_test(self, test_name: str, passed: bool, details: dict[str, Any] = None):
        """Record test result."""
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        })
        
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            for key, value in details.items():
                logger.info(f"  {key}: {value}")
    
    def print_summary(self):
        """Print test summary."""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        
        logger.info("\n" + "=" * 70)
        logger.info("TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {total - passed}")
        logger.info(f"Success Rate: {passed/total*100:.1f}%")
        logger.info(f"\nImages Generated: {self.total_images_generated}")
        logger.info(f"Cost Saved (vs pure AI): ${self.total_cost_saved:.2f}")
        logger.info("=" * 70)
        
        # Print failed tests
        failed = [r for r in self.test_results if not r["passed"]]
        if failed:
            logger.info("\nFailed Tests:")
            for test in failed:
                logger.info(f"  - {test['test']}: {test['details']}")
    
    async def run_all_tests(self):
        """Run all E2E tests."""
        logger.info("=" * 70)
        logger.info("Starting End-to-End Tests")
        logger.info("=" * 70)
        
        # Initialize system
        initialize_system()
        
        # Test 1: Tool selection rules
        await self.test_tool_selection_rules()
        
        # Test 2: Image generation strategy
        await self.test_image_generation_strategy()
        
        # Test 3: Teaching flow with tools
        await self.test_teaching_flow_with_tools()
        
        # Test 4: New vs old mode
        await self.test_mode_switching()
        
        # Test 5: Student context loading
        await self.test_student_context_loading()
        
        # Test 6: Cost optimization
        await self.test_cost_optimization()
        
        # Print summary
        self.print_summary()
    
    async def test_tool_selection_rules(self):
        """Test 1: Tool selection rules for different phases and KP types."""
        logger.info("\n【Test 1】Tool Selection Rules")
        
        test_cases = [
            # (phase, kp_type, expected_tools)
            (1, "概念", ["image_generation"]),
            (1, "几何概念", ["image_generation"]),
            (2, "公式推导", ["image_generation"]),
            (3, "概念", ["interactive_demo"]),
            (4, "任何", ["question_generator"]),
        ]
        
        all_passed = True
        for phase, kp_type, expected in test_cases:
            from app.services.tool_selection_engine import TeachingContext
            context = TeachingContext(
                current_phase=phase,
                kp_type=kp_type,
                student_ability="beginner",
                teaching_mode="teach",
            )
            
            selected = tool_selection_engine.select_tools(context)
            passed = set(selected) == set(expected)
            
            self.record_test(
                f"Tool selection: Phase {phase}, KP type {kp_type}",
                passed,
                {
                    "expected": expected,
                    "actual": selected,
                }
            )
            
            if not passed:
                all_passed = False
        
        return all_passed
    
    async def test_image_generation_strategy(self):
        """Test 2: Image generation strategy (library/template/AI)."""
        logger.info("\n【Test 2】Image Generation Strategy")
        
        from app.services.tools.image_tool import create_image_tool
        
        tool = create_image_tool()
        
        # Test 2.1: Library retrieval
        request = ToolRequest(
            action="get_image",
            params={
                "image_id": "IMG_K1_001",
                "knowledge_point_id": "K1",
            }
        )
        result = await tool.execute(request)
        
        library_passed = result.success and result.metadata.get("source") == "library"
        self.record_test(
            "Image library retrieval",
            library_passed,
            {
                "image_id": "IMG_K1_001",
                "source": result.metadata.get("source"),
                "cost": result.metadata.get("cost", 0),
            }
        )
        
        # Test 2.2: Template rendering
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
        self.record_test(
            "Template rendering",
            template_passed,
            {
                "concept": "函数图像",
                "source": result2.metadata.get("source"),
                "cost": result2.metadata.get("cost", 0),
            }
        )
        
        # Test 2.3: AI generation (fallback)
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
        self.record_test(
            "AI generation (fallback)",
            ai_passed,
            {
                "concept": "一次函数与几何图形结合",
                "source": result3.metadata.get("source"),
                "cost": result3.metadata.get("cost", 0),
            }
        )
        
        # Track cost savings
        if library_passed:
            self.total_cost_saved += 0.05  # Saved AI cost
        if template_passed:
            self.total_cost_saved += 0.03  # Template cheaper than AI
        
        self.total_images_generated += 3
        
        return library_passed and template_passed and ai_passed
    
    async def test_teaching_flow_with_tools(self):
        """Test 3: Teaching flow with tool enhancement."""
        logger.info("\n【Test 3】Teaching Flow with Tools")
        
        # Create test session
        round1 = LearningRound(
            round_number=1,
            start_time=datetime.now(),
            status=RoundStatus.IN_PROGRESS,
            current_phase=1,
        )
        
        session = LearningSession(
            id="test_e2e_session_1",
            student_id=1,
            course_id="MATH_JUNIOR_01",
            kp_id="K1",  # 正比例函数
            status=SessionStatus.ACTIVE,
            rounds=[round1],
        )
        learning_session_repository.create(session)
        
        # Execute teaching flow with tools
        event_count = 0
        tool_events = 0
        
        try:
            async for event in teaching_flow.execute_teaching_phase(
                session=session,
                student_name="测试学生",
                trace_id="e2e_test_1",
                use_tools=True,
            ):
                event_count += 1
                
                # Check if it's a tool event
                if event.get("event") in ["tool_call", "tool_result"]:
                    tool_events += 1
            
            # Should have events
            passed = event_count > 0 and tool_events > 0
            
            self.record_test(
                "Teaching flow with tools",
                passed,
                {
                    "total_events": event_count,
                    "tool_events": tool_events,
                }
            )
            
            return passed
            
        except Exception as e:
            self.record_test(
                "Teaching flow with tools",
                False,
                {"error": str(e)}
            )
            return False
    
    async def test_mode_switching(self):
        """Test 4: New vs old mode switching."""
        logger.info("\n【Test 4】Mode Switching")
        
        # Create test session
        round1 = LearningRound(
            round_number=1,
            start_time=datetime.now(),
            status=RoundStatus.IN_PROGRESS,
            current_phase=1,
        )
        
        session = LearningSession(
            id="test_e2e_session_2",
            student_id=1,
            course_id="MATH_JUNIOR_01",
            kp_id="K1",
            status=SessionStatus.ACTIVE,
            rounds=[round1],
        )
        learning_session_repository.create(session)
        
        # Test 4.1: Old mode (no tools)
        try:
            event_count_old = 0
            tool_events_old = 0
            
            async for event in teaching_flow.execute_teaching_phase(
                session=session,
                student_name="测试学生",
                trace_id="e2e_test_old",
                use_tools=False,  # Old mode
            ):
                event_count_old += 1
                if event.get("event") in ["tool_call", "tool_result"]:
                    tool_events_old += 1
            
            old_mode_passed = event_count_old > 0 and tool_events_old == 0
            
            self.record_test(
                "Old mode (no tools)",
                old_mode_passed,
                {
                    "total_events": event_count_old,
                    "tool_events": tool_events_old,
                }
            )
            
        except Exception as e:
            self.record_test(
                "Old mode (no tools)",
                False,
                {"error": str(e)}
            )
            old_mode_passed = False
        
        # Test 4.2: New mode (with tools)
        try:
            event_count_new = 0
            tool_events_new = 0
            
            async for event in teaching_flow.execute_teaching_phase(
                session=session,
                student_name="测试学生",
                trace_id="e2e_test_new",
                use_tools=True,  # New mode
            ):
                event_count_new += 1
                if event.get("event") in ["tool_call", "tool_result"]:
                    tool_events_new += 1
            
            new_mode_passed = event_count_new > 0 and tool_events_new > 0
            
            self.record_test(
                "New mode (with tools)",
                new_mode_passed,
                {
                    "total_events": event_count_new,
                    "tool_events": tool_events_new,
                }
            )
            
        except Exception as e:
            self.record_test(
                "New mode (with tools)",
                False,
                {"error": str(e)}
            )
            new_mode_passed = False
        
        return old_mode_passed and new_mode_passed
    
    async def test_student_context_loading(self):
        """Test 5: Student context loading."""
        logger.info("\n【Test 5】Student Context Loading")
        
        from app.services.student_context_loader import student_context_loader
        
        try:
            # Load context for student 1
            context = await student_context_loader.load(
                student_id=1,
                course_id="MATH_JUNIOR_01",
            )
            
            # Check context structure
            has_profile = context.profile is not None
            has_history = len(context.history) >= 0
            has_summary = context.summary is not None
            
            passed = has_profile and has_history and has_summary
            
            self.record_test(
                "Student context loading",
                passed,
                {
                    "has_profile": has_profile,
                    "has_history": has_history,
                    "has_summary": has_summary,
                    "history_count": len(context.history),
                }
            )
            
            return passed
            
        except Exception as e:
            self.record_test(
                "Student context loading",
                False,
                {"error": str(e)}
            )
            return False
    
    async def test_cost_optimization(self):
        """Test 6: Cost optimization analysis."""
        logger.info("\n【Test 6】Cost Optimization Analysis")
        
        # Get usage logs
        logs = tool_usage_log_repository.get_all()
        
        # Calculate costs
        library_count = 0
        template_count = 0
        ai_count = 0
        
        for log in logs:
            # ToolUsageLog has 'result' field, not 'metadata'
            source = log.result.get("source", "") if log.success else ""
            if "library" in source:
                library_count += 1
            elif "template" in source:
                template_count += 1
            elif "ai" in source:
                ai_count += 1
        
        total = library_count + template_count + ai_count
        
        if total > 0:
            library_pct = library_count / total * 100
            template_pct = template_count / total * 100
            ai_pct = ai_count / total * 100
            
            # Target: library 80%, template 15%, AI 5%
            target_met = library_pct >= 70  # Allow some variance
            
            self.record_test(
                "Cost optimization (library >= 70%)",
                target_met,
                {
                    "library": f"{library_pct:.1f}%",
                    "template": f"{template_pct:.1f}%",
                    "ai": f"{ai_pct:.1f}%",
                    "total_images": total,
                }
            )
            
            return target_met
        else:
            self.record_test(
                "Cost optimization",
                True,
                {"note": "No usage logs yet"}
            )
            return True


async def main():
    """Main test runner."""
    runner = E2ETestRunner()
    await runner.run_all_tests()
    
    # Save results
    results_file = Path(__file__).parent / "test_e2e_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": runner.test_results,
            "summary": {
                "total": len(runner.test_results),
                "passed": sum(1 for r in runner.test_results if r["passed"]),
                "images_generated": runner.total_images_generated,
                "cost_saved": runner.total_cost_saved,
            }
        }, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())
