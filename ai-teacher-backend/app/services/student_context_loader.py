"""Student context loader for loading complete student information."""

import logging
from datetime import datetime
from typing import Any, Optional

from app.models.tool import StudentContext
from app.models.learning import LearningRecord, LearningStatus
from app.repositories.learning_repository import (
    student_profile_repository,
    learning_record_repository,
)

logger = logging.getLogger(__name__)


class StudentContextLoader:
    """Loader for student complete context.
    
    This class is responsible for:
    - Loading student profile for a course
    - Loading recent learning history
    - Loading recent dialogue history
    - Computing aggregated summary statistics
    
    Key Design Decision:
    - Student context is loaded FIRST in the teaching flow
    - This enables personalized teaching based on student history
    - Summary statistics help identify struggle areas
    
    Example:
        >>> loader = StudentContextLoader()
        >>> context = await loader.load(student_id=1, course_id="MATH_JUNIOR_01")
        >>> print(context.summary["average_score"])
        0.85
        >>> print(context.summary["struggle_areas"])
        ["几何证明"]
    """
    
    def __init__(self):
        """Initialize the student context loader."""
        self.profile_repo = student_profile_repository
        self.record_repo = learning_record_repository
    
    async def load(
        self,
        student_id: int,
        course_id: str,
        max_history: int = 10,
        max_dialogues: int = 5,
    ) -> StudentContext:
        """Load complete student context.
        
        This method:
        1. Loads student profile for the course
        2. Loads recent learning records
        3. Loads recent dialogue history
        4. Computes summary statistics
        
        Args:
            student_id: Student ID
            course_id: Course ID
            max_history: Maximum number of learning records to load
            max_dialogues: Maximum number of recent dialogues to load
            
        Returns:
            StudentContext with profile, history, dialogues, and summary
            
        Example:
            >>> context = await loader.load(1, "MATH_JUNIOR_01")
            >>> print(context.profile.student_id)
            1
            >>> print(len(context.history))
            10
        """
        logger.info(f"Loading student context: student_id={student_id}, course_id={course_id}")
        
        # Step 1: Load student profile
        profile = self.profile_repo.get_by_student_and_course(student_id, course_id)
        
        # Step 2: Load recent learning records
        history = self.record_repo.get_by_student_and_course(student_id, course_id)
        # Sort by updated_at descending and limit
        history = sorted(history, key=lambda r: r.updated_at, reverse=True)[:max_history]
        
        # Step 3: Load recent dialogues (if available)
        recent_dialogues = self._get_recent_dialogues(student_id, course_id, max_dialogues)
        
        # Step 4: Compute summary statistics
        summary = self._compute_summary(history, profile)
        
        context = StudentContext(
            profile=profile,
            history=history,
            recent_dialogues=recent_dialogues,
            summary=summary,
        )
        
        logger.info(
            f"Student context loaded: "
            f"total_learned={summary['total_learned']}, "
            f"average_score={summary['average_score']:.2%}, "
            f"struggle_areas={len(summary['struggle_areas'])}"
        )
        
        return context
    
    def _get_recent_dialogues(
        self,
        student_id: int,
        course_id: str,
        max_dialogues: int,
    ) -> list[dict[str, str]]:
        """Get recent dialogue history.
        
        This is a placeholder implementation. In the future, this should:
        - Load recent conversations from a dialogue repository
        - Filter by student and course
        - Limit to max_dialogues
        
        Args:
            student_id: Student ID
            course_id: Course ID
            max_dialogues: Maximum number of dialogues to return
            
        Returns:
            List of dialogue messages (currently empty)
        """
        # TODO: Implement dialogue loading from repository
        # For now, return empty list
        return []
    
    def _compute_summary(
        self,
        history: list[LearningRecord],
        profile: Optional[Any],
    ) -> dict:
        """Compute summary statistics from learning history.
        
        This method computes:
        - total_learned: Number of learning attempts
        - average_score: Average score across attempts
        - struggle_areas: Knowledge points with difficulties
        - learning_velocity: Average score (simplified metric)
        
        Args:
            history: List of learning records
            profile: Student profile (optional)
            
        Returns:
            Dictionary with summary statistics
        """
        if not history:
            return {
                "total_learned": 0,
                "average_score": 0.0,
                "struggle_areas": [],
                "learning_velocity": 0.5,
            }
        
        # Total learned
        total_learned = len(history)
        
        # Average score
        scores = [
            attempt.score
            for record in history
            for attempt in record.attempts
            if attempt.score > 0
        ]
        average_score = sum(scores) / len(scores) if scores else 0.0
        
        # Struggle areas: knowledge points with high attempt count but not mastered
        struggle_areas = []
        for record in history:
            if record.attempt_count >= 3 and record.status != LearningStatus.MASTERED:
                # Get KP name (would need to query KP repository)
                struggle_areas.append(record.kp_id)
        
        # Learning velocity (simplified: average score)
        learning_velocity = average_score
        
        return {
            "total_learned": total_learned,
            "average_score": average_score,
            "struggle_areas": struggle_areas[:5],  # Limit to top 5
            "learning_velocity": learning_velocity,
        }
    
    def _identify_struggles(self, history: list[LearningRecord]) -> list[str]:
        """Identify knowledge points where the student struggles.
        
        A student struggles with a knowledge point if:
        - Attempt count >= 3 AND
        - Status is not mastered
        
        Args:
            history: List of learning records
            
        Returns:
            List of knowledge point IDs where student struggles
        """
        struggles = []
        for record in history:
            if record.attempt_count >= 3 and record.status != LearningStatus.MASTERED:
                struggles.append(record.kp_id)
        return struggles
    
    def _calculate_velocity(self, history: list[LearningRecord]) -> float:
        """Calculate learning velocity.
        
        Simplified metric: average score across all attempts.
        
        In the future, this could be enhanced to:
        - Consider time between attempts
        - Consider improvement rate
        - Consider difficulty of knowledge points
        
        Args:
            history: List of learning records
            
        Returns:
            Learning velocity (0.0 to 1.0)
        """
        if not history:
            return 0.5  # Default to middle
        
        scores = [
            attempt.score
            for record in history
            for attempt in record.attempts
            if attempt.score > 0
        ]
        
        return sum(scores) / len(scores) if scores else 0.5


# Global instance
student_context_loader = StudentContextLoader()
