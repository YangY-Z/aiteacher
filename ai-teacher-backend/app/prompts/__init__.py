"""Prompts module for LLM prompts."""

from app.prompts.system_prompt import (
    SYSTEM_PROMPT,
    FIRST_LEARNING_PROMPT,
    REVIEW_PROMPT,
    BACKTRACK_PROMPT,
)
from app.prompts.teaching_prompt import (
    TEACHING_PROMPT,
    CONCEPT_TEACHING_PROMPT,
    FORMULA_TEACHING_PROMPT,
    SKILL_TEACHING_PROMPT,
)
from app.prompts.question_prompt import (
    QUESTION_PROMPT,
    STUDENT_ANSWER_PROMPT,
)
from app.prompts.backtrack_prompt import BACKTRACK_DECISION_PROMPT

__all__ = [
    "SYSTEM_PROMPT",
    "FIRST_LEARNING_PROMPT",
    "REVIEW_PROMPT",
    "BACKTRACK_PROMPT",
    "TEACHING_PROMPT",
    "CONCEPT_TEACHING_PROMPT",
    "FORMULA_TEACHING_PROMPT",
    "SKILL_TEACHING_PROMPT",
    "QUESTION_PROMPT",
    "STUDENT_ANSWER_PROMPT",
    "BACKTRACK_DECISION_PROMPT",
]
