"""Regression tests for improvement quiz state transitions."""

import json
from pathlib import Path

from app.models.improvement import DifficultyLevel, FoundationLevel, ScoreInput, ImprovementSessionStatus
from app.repositories.assessment_repository import assessment_question_repository
from app.repositories.memory_db import db
from app.services.improvement_service import improvement_service
from app.utils.data_loader import load_assessment_data


ASSESSMENT_PATH = Path(__file__).resolve().parents[1] / "评估题库_一次函数.json"
COURSE_ID = "MATH_JUNIOR_01"
STUDENT_ID = "1"



def ensureAssessmentLoaded() -> None:
    """Load assessment questions used by improvement quiz tests."""
    if assessment_question_repository.get_by_kp("K6"):
        return

    with open(ASSESSMENT_PATH, "r", encoding="utf-8") as file:
        assessment_data = json.load(file)
    load_assessment_data(assessment_data)



def createDiagnosedSession() -> tuple[str, list[dict[str, str]]]:
    """Create a session that is ready to submit quiz answers."""
    ensureAssessmentLoaded()

    score_input = ScoreInput(
        exam_name="专项回归测试",
        score=30,
        total_score=100,
        error_description="概念理解不清",
        available_time=30,
        difficulty=DifficultyLevel.NORMAL,
        foundation=FoundationLevel.WEAK,
    )
    session = improvement_service.start_session(STUDENT_ID, COURSE_ID, score_input)
    if session.status == ImprovementSessionStatus.CLARIFYING:
        session = improvement_service.submit_clarification_answer(session.session_id, "函数定义和概念总是混淆")

    session = improvement_service.generate_plan(session.session_id)
    assert session.plan is not None
    for step in session.plan.steps:
        improvement_service.complete_plan_step(session.session_id, step.step_order)

    quiz = improvement_service.get_quiz(session.session_id)
    return session.session_id, quiz["questions"]



def testSubmitQuizKeepsQuizStatusWhenFailed() -> None:
    """Quiz failure should not complete the improvement session."""
    session_id, questions = createDiagnosedSession()

    answers = [{"question_id": question["id"], "answer": "__wrong__"} for question in questions]
    result = improvement_service.submit_quiz(session_id, answers)
    session = improvement_service.get_session(session_id)

    assert result.passed is False
    assert session.status == ImprovementSessionStatus.QUIZ
    assert session.completed_at is None



def testSubmitQuizCompletesSessionWhenPassed() -> None:
    """Quiz success should complete the improvement session."""
    session_id, questions = createDiagnosedSession()

    answers = []
    for question in questions:
        stored_question = assessment_question_repository.get_by_id(question["id"])
        assert stored_question is not None
        answers.append({"question_id": question["id"], "answer": stored_question.correct_answer})

    result = improvement_service.submit_quiz(session_id, answers)
    session = improvement_service.get_session(session_id)

    assert result.passed is True
    assert session.status == ImprovementSessionStatus.COMPLETED
    assert session.completed_at is not None
