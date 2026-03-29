"""Agent 架构单元测试。"""

import pytest
from app.agents.improvement_agent import ImprovementAgent
from app.agents.tools.improvement_tools import (
    ImprovementTools,
    DiagnoseStudentInput,
    ClarifyStudentInput,
    GenerateLearningPlanInput,
    TeachKnowledgePointInput,
    EvaluateQuizInput,
)
from app.services.improvement_service import improvement_service
from app.services.course_service import course_service
from app.services.llm_service import llm_service


class TestImprovementTools:
    """测试 ImprovementTools 工具集。"""

    @pytest.fixture
    def tools(self):
        return ImprovementTools(
            improvement_service=improvement_service,
            course_service=course_service,
            llm_service=llm_service,
        )

    def test_diagnose_student(self, tools):
        """测试诊断工具。"""
        input_data = DiagnoseStudentInput(
            score=60.0,
            total_score=100.0,
            error_description="不懂一元二次函数",
            available_time=30,
            difficulty="normal",
            foundation="average",
        )
        result = tools.diagnose_student(input_data)

        assert result.target_kp_id is not None
        assert 0 <= result.confidence <= 1
        assert result.reason is not None
        assert isinstance(result.prerequisite_gaps, list)

    def test_generate_learning_plan(self, tools):
        """测试方案生成工具。"""
        input_data = GenerateLearningPlanInput(
            target_kp_id="K1",
            available_time=30,
            difficulty="normal",
            foundation="average",
        )
        result = tools.generate_learning_plan(input_data)

        assert len(result.steps) > 0
        assert result.total_estimated_minutes > 0
        for step in result.steps:
            assert step.step_order > 0
            assert step.knowledge_point_id is not None
            assert step.goal is not None
            assert step.estimated_minutes > 0

    def test_teach_knowledge_point(self, tools):
        """测试教学工具。"""
        input_data = TeachKnowledgePointInput(
            knowledge_point_id="K1",
            goal="学习一次函数的定义",
            attempt_count=1,
        )
        result = tools.teach_knowledge_point(input_data)

        assert result.response_type is not None
        assert result.content is not None
        assert result.whiteboard is not None
        assert result.next_action is not None

    def test_evaluate_quiz(self, tools):
        """测试评估工具。"""
        input_data = EvaluateQuizInput(
            knowledge_point_id="K1",
            answers=[
                {"question_id": "K1_Q1", "answer": "A"},
                {"question_id": "K1_Q2", "answer": "B"},
            ],
        )
        result = tools.evaluate_quiz(input_data)

        assert 0 <= result.score <= 1
        assert isinstance(result.passed, bool)
        assert result.feedback is not None

    def test_analyze_error_pattern(self, tools):
        """测试错误模式分析工具。"""
        error_history = [
            {"type": "calculation", "description": "计算错误"},
            {"type": "calculation", "description": "计算错误"},
            {"type": "concept", "description": "概念错误"},
        ]
        result = tools.analyze_error_pattern("1", error_history)

        assert "error_root_cause" in result
        assert "suggested_kp_ids" in result
        assert len(result["suggested_kp_ids"]) > 0

    def test_query_knowledge_graph(self, tools):
        """测试知识图谱查询工具。"""
        result = tools.query_knowledge_graph("K1", "prerequisites")

        assert "query_type" in result
        assert "target_kp_id" in result
        assert "related_kp_ids" in result

    def test_fetch_similar_questions(self, tools):
        """测试相似题目获取工具。"""
        result = tools.fetch_similar_questions("K1", "基础", "选择题")

        assert "questions" in result
        assert "count" in result
        assert isinstance(result["questions"], list)

    def test_record_learning_progress(self, tools):
        """测试学习进度记录工具。"""
        result = tools.record_learning_progress("1", "K1", 0.8)

        assert "success" in result
        assert "message" in result


class TestImprovementAgent:
    """测试 ImprovementAgent。"""

    @pytest.fixture
    def agent(self):
        return ImprovementAgent(
            improvement_service=improvement_service,
            course_service=course_service,
            llm_service=llm_service,
        )

    def test_agent_initialization(self, agent):
        """测试 Agent 初始化。"""
        assert agent.improvement_service is not None
        assert agent.course_service is not None
        assert agent.llm_service is not None
        assert len(agent.tool_map) == 5
        assert len(agent.tool_definitions) == 5

    def test_tool_definitions(self, agent):
        """测试工具定义。"""
        for tool_def in agent.tool_definitions:
            assert tool_def.name is not None
            assert tool_def.description is not None
            assert tool_def.input_schema is not None
            assert tool_def.handler is not None

    def test_tool_map(self, agent):
        """测试工具映射。"""
        expected_tools = [
            "diagnose_student",
            "clarify_student",
            "generate_learning_plan",
            "teach_knowledge_point",
            "evaluate_quiz",
        ]
        for tool_name in expected_tools:
            assert tool_name in agent.tool_map
            assert callable(agent.tool_map[tool_name])
