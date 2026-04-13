"""Tool selection rule engine for determining which tools to use."""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TeachingContext:
    """Context for tool selection.
    
    Contains all information needed to determine which tools are appropriate.
    
    Args:
        current_phase: Current teaching phase (1, 2, 3, etc.)
        kp_type: Knowledge point type (e.g., "几何概念", "公式推导")
        student_ability: Student ability level (novice, intermediate, advanced)
        teaching_mode: Teaching mode (e.g., "概念建构型")
    """
    
    def __init__(
        self,
        current_phase: int = 1,
        kp_type: str = "",
        student_ability: str = "intermediate",
        teaching_mode: str = "",
    ):
        """Initialize teaching context."""
        self.current_phase = current_phase
        self.kp_type = kp_type
        self.student_ability = student_ability
        self.teaching_mode = teaching_mode
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TeachingContext("
            f"phase={self.current_phase}, "
            f"kp_type={self.kp_type}, "
            f"ability={self.student_ability})"
        )


class ToolSelectionRuleEngine:
    """Rule-based tool selection engine.
    
    This engine uses simple rule mapping instead of AI decision-making to:
    - Reduce complexity
    - Avoid AI decision errors
    - Ensure predictable behavior
    
    Design Principles:
    - Rules > AI: Use explicit rules instead of AI decisions
    - Simplicity: Keep rule logic straightforward
    - Extensibility: Easy to add new rules
    
    Example:
        >>> engine = ToolSelectionRuleEngine()
        >>> context = TeachingContext(current_phase=1, kp_type="几何概念")
        >>> tools = engine.select_tools(context)
        >>> print(tools)
        ["image_generation"]
    """
    
    # Tool selection rules: (phase, kp_type) -> list of tools
    TOOL_SELECTION_RULES = {
        # Phase 1: Introduction
        ("phase_1", "几何概念"): ["image_generation"],
        ("phase_1", "公式推导"): ["image_generation", "video_generation"],
        ("phase_1", "概念"): ["image_generation"],
        ("phase_1", "计算"): ["image_generation"],
        
        # Phase 2: Deep dive
        ("phase_2", "几何概念"): ["image_generation"],
        ("phase_2", "公式推导"): ["image_generation"],
        ("phase_2", "概念"): ["image_generation"],
        ("phase_2", "计算"): ["image_generation"],
        
        # Phase 3: Practice
        ("phase_3", "几何概念"): ["image_generation", "interactive_demo"],
        ("phase_3", "公式推导"): ["image_generation", "interactive_demo"],
        ("phase_3", "概念"): ["interactive_demo"],
        ("phase_3", "计算"): ["interactive_demo"],
        
        # Phase 4: Assessment
        ("phase_4", "几何概念"): ["question_generator"],
        ("phase_4", "公式推导"): ["question_generator"],
        ("phase_4", "概念"): ["question_generator"],
        ("phase_4", "计算"): ["question_generator"],
        
        # Wildcard rules
        ("phase_3", "任何"): ["interactive_demo"],
    }
    
    def __init__(self):
        """Initialize the tool selection rule engine."""
        self.rules = self.TOOL_SELECTION_RULES.copy()
        logger.info(f"ToolSelectionRuleEngine initialized with {len(self.rules)} rules")
    
    def select_tools(self, context: TeachingContext) -> list[str]:
        """Select tools based on teaching context.
        
        This method:
        1. Looks up rules for the current context
        2. Applies dynamic adjustments based on student ability
        3. Returns a list of tool names
        
        Args:
            context: Teaching context with phase, kp_type, and student ability
            
        Returns:
            List of tool names to prepare contexts for
            
        Example:
            >>> context = TeachingContext(current_phase=1, kp_type="几何概念")
            >>> tools = engine.select_tools(context)
            >>> print(tools)
            ["image_generation"]
        """
        logger.info(f"Selecting tools for context: {context}")
        
        # Step 1: Look up rules
        rule_key = (f"phase_{context.current_phase}", context.kp_type)
        tools = self.rules.get(rule_key, [])
        
        # Fallback: Try wildcard rule
        if not tools:
            wildcard_key = (f"phase_{context.current_phase}", "任何")
            tools = self.rules.get(wildcard_key, [])
        
        # Step 2: Dynamic adjustments based on student ability
        if context.student_ability == "novice":
            # Novices may need more visualization
            if "image_generation" not in tools and context.current_phase <= 2:
                tools = tools + ["image_generation"]
        
        elif context.student_ability == "advanced":
            # Advanced students may need less visualization
            # But keep tools for practice phases
            if context.current_phase >= 3:
                pass  # Keep all tools
        
        # Step 3: Remove duplicates while preserving order
        seen = set()
        unique_tools = []
        for tool in tools:
            if tool not in seen:
                seen.add(tool)
                unique_tools.append(tool)
        
        logger.info(f"Selected tools: {unique_tools}")
        return unique_tools
    
    def add_rule(self, phase: int, kp_type: str, tools: list[str]) -> None:
        """Add a new tool selection rule.
        
        Args:
            phase: Teaching phase (1, 2, 3, etc.)
            kp_type: Knowledge point type
            tools: List of tool names
            
        Example:
            >>> engine.add_rule(phase=5, kp_type="综合应用", tools=["interactive_demo"])
        """
        rule_key = (f"phase_{phase}", kp_type)
        self.rules[rule_key] = tools
        logger.info(f"Added rule: {rule_key} -> {tools}")
    
    def remove_rule(self, phase: int, kp_type: str) -> bool:
        """Remove a tool selection rule.
        
        Args:
            phase: Teaching phase
            kp_type: Knowledge point type
            
        Returns:
            True if rule was removed, False if not found
        """
        rule_key = (f"phase_{phase}", kp_type)
        if rule_key in self.rules:
            del self.rules[rule_key]
            logger.info(f"Removed rule: {rule_key}")
            return True
        return False
    
    def get_rule(self, phase: int, kp_type: str) -> Optional[list[str]]:
        """Get tools for a specific rule.
        
        Args:
            phase: Teaching phase
            kp_type: Knowledge point type
            
        Returns:
            List of tool names if rule exists, None otherwise
        """
        rule_key = (f"phase_{phase}", kp_type)
        return self.rules.get(rule_key)
    
    def get_all_rules(self) -> dict[tuple[str, str], list[str]]:
        """Get all tool selection rules.
        
        Returns:
            Dictionary of all rules
        """
        return self.rules.copy()
    
    def determine_student_ability(
        self,
        attempt_count: int,
        last_score: Optional[float] = None,
    ) -> str:
        """Determine student ability level.
        
        This is a simplified heuristic based on:
        - Number of attempts
        - Last score (if available)
        
        Args:
            attempt_count: Number of learning attempts
            last_score: Last assessment score (0.0 to 1.0)
            
        Returns:
            Ability level: "novice", "intermediate", or "advanced"
            
        Example:
            >>> ability = engine.determine_student_ability(attempt_count=0)
            >>> print(ability)
            "novice"
        """
        # New learner
        if attempt_count == 0:
            return "novice"
        
        # Multiple failed attempts
        if attempt_count >= 3:
            return "novice"
        
        # Single successful attempt
        if attempt_count == 1 and last_score and last_score >= 0.8:
            return "advanced"
        
        # Default
        return "intermediate"


# Global instance
tool_selection_engine = ToolSelectionRuleEngine()
