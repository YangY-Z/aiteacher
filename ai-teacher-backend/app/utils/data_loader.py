"""Data loader utility for importing course and assessment data."""

import json
from typing import Any
from pathlib import Path

from app.models.course import (
    Course,
    KnowledgePoint,
    KnowledgePointType,
    KnowledgePointDependency,
    MasteryCriteria,
    TeachingConfig,
)
from app.models.assessment import (
    AssessmentQuestion,
    QuestionType,
    Difficulty,
)
from app.repositories.course_repository import (
    course_repository,
    knowledge_point_repository,
    knowledge_point_dependency_repository,
)
from app.repositories.assessment_repository import assessment_question_repository


def load_course_data(data_dir: str = "/Users/zhaoyang/iFlow/aiteacher") -> None:
    """Load course and knowledge point data from JSON files.

    Args:
        data_dir: Directory containing the JSON data files.
    """
    # Load knowledge points from the spec document (embedded data)
    # For MVP, we'll use the knowledge points defined in the requirements spec
    
    # Create the course
    course = Course(
        id="MATH_JUNIOR_01",
        name="一次函数",
        grade="初一",
        subject="数学",
        description="初一数学一次函数单元",
        total_knowledge_points=32,
        estimated_hours=12.0,
        level_descriptions={
            0: "基础概念层",
            1: "核心概念层",
            2: "函数基础层",
            3: "正比例与一次函数层",
            4: "图象与性质层",
            5: "变换层",
            6: "综合应用层",
        }
    )
    course_repository.create(course)

    # Define all knowledge points from the spec
    knowledge_points_data = [
        # Level 0
        {"id": "K1", "name": "坐标系", "type": "概念", "description": "平面直角坐标系的建立，x轴、y轴、原点", "level": 0, "dependencies": []},
        {"id": "K2", "name": "点的坐标", "type": "技能", "description": "用有序数对(x,y)表示平面上点的位置", "level": 1, "dependencies": ["K1"]},
        {"id": "K3", "name": "象限", "type": "概念", "description": "坐标平面被两轴分成四个象限及其特征", "level": 0, "dependencies": ["K1"]},
        {"id": "K4", "name": "变量", "type": "概念", "description": "可以取不同数值的量", "level": 0, "dependencies": []},
        {"id": "K5", "name": "常量", "type": "概念", "description": "数值固定不变的量", "level": 0, "dependencies": []},
        
        # Level 1-2
        {"id": "K6", "name": "函数定义", "type": "概念", "description": "设x和y是两个变量，若x每取一个值，y都有唯一确定的值与之对应", "level": 1, "dependencies": ["K4", "K5"]},
        {"id": "K7", "name": "自变量与因变量", "type": "概念", "description": "主动变化的量为自变量，随之变化的量为因变量", "level": 2, "dependencies": ["K6"]},
        {"id": "K8", "name": "函数的定义域", "type": "概念", "description": "自变量x允许取值的范围", "level": 2, "dependencies": ["K6"]},
        {"id": "K9", "name": "函数值", "type": "技能", "description": "当x取某值时，y对应的值", "level": 2, "dependencies": ["K6"]},
        {"id": "K10", "name": "函数解析式", "type": "概念", "description": "用数学式子表示函数关系", "level": 2, "dependencies": ["K6"]},
        {"id": "K11", "name": "函数的三种表示法", "type": "技能", "description": "解析式法、列表法、图象法", "level": 2, "dependencies": ["K10"]},
        
        # Level 3
        {"id": "K12", "name": "正比例函数定义", "type": "概念", "description": "y=kx(k≠0)形式的函数", "level": 3, "dependencies": ["K6", "K10"]},
        {"id": "K13", "name": "正比例函数图象", "type": "技能", "description": "正比例函数图象是过原点的直线", "level": 3, "dependencies": ["K11", "K12"]},
        {"id": "K14", "name": "正比例函数性质", "type": "公式", "description": "k>0过一三象限且递增；k<0过二四象限且递减", "level": 3, "dependencies": ["K12", "K3"]},
        {"id": "K15", "name": "一次函数定义", "type": "概念", "description": "y=kx+b(k≠0)形式的函数", "level": 3, "dependencies": ["K12", "K10"]},
        {"id": "K16", "name": "一次函数与正比例函数关系", "type": "概念", "description": "当b=0时，一次函数退化为正比例函数", "level": 3, "dependencies": ["K15"]},
        
        # Level 4
        {"id": "K17", "name": "描点法画函数图象", "type": "技能", "description": "列表、描点、连线的作图方法", "level": 4, "dependencies": ["K11", "K2"]},
        {"id": "K18", "name": "一次函数图象特征", "type": "技能", "description": "一次函数图象是一条直线", "level": 4, "dependencies": ["K15"]},
        {"id": "K19", "name": "两点确定直线", "type": "技能", "description": "画一次函数图象只需描出两点连线", "level": 4, "dependencies": ["K17"]},
        {"id": "K20", "name": "截距概念", "type": "概念", "description": "直线与y轴交点的纵坐标，即b的值", "level": 4, "dependencies": ["K15"]},
        {"id": "K21", "name": "斜率概念", "type": "概念", "description": "直线倾斜程度的度量，即k的值", "level": 4, "dependencies": ["K15"]},
        {"id": "K22", "name": "k对图象方向的影响", "type": "公式", "description": "k>0从左向右上升；k<0从左向右下降", "level": 4, "dependencies": ["K18", "K21"]},
        {"id": "K23", "name": "b对图象位置的影响", "type": "公式", "description": "b>0与y轴交于正半轴；b<0交于负半轴", "level": 4, "dependencies": ["K20"]},
        {"id": "K24", "name": "一次函数增减性", "type": "公式", "description": "k>0时y随x增大而增大；k<0时y随x增大而减小", "level": 4, "dependencies": ["K21", "K18"]},
        
        # Level 5
        {"id": "K25", "name": "平移变换", "type": "技能", "description": "上下平移改变b值，左右平移改变x", "level": 5, "dependencies": ["K18", "K20"]},
        
        # Level 6
        {"id": "K26", "name": "k与b的综合判断", "type": "技能", "description": "根据k、b符号判断图象经过的象限", "level": 6, "dependencies": ["K22", "K23", "K3"]},
        {"id": "K27", "name": "待定系数法", "type": "技能", "description": "设出函数解析式，代入条件求k、b", "level": 6, "dependencies": ["K15", "K9"]},
        {"id": "K28", "name": "由图象求解析式", "type": "技能", "description": "从图象上读取点坐标，用待定系数法求解析式", "level": 6, "dependencies": ["K27", "K19"]},
        {"id": "K29", "name": "求交点坐标", "type": "技能", "description": "联立两一次函数解析式求解方程组", "level": 6, "dependencies": ["K27"]},
        {"id": "K30", "name": "实际问题建模", "type": "技能", "description": "将实际问题转化为一次函数求解", "level": 6, "dependencies": ["K15", "K28"]},
        {"id": "K31", "name": "一次函数与方程的关系", "type": "概念", "description": "求ax+b=0的解等价于求y=ax+b与x轴交点横坐标", "level": 6, "dependencies": ["K18"]},
        {"id": "K32", "name": "一次函数与不等式的关系", "type": "概念", "description": "图象在x轴上方/下方对应的x范围即为不等式解集", "level": 6, "dependencies": ["K18"]},
    ]

    # Create knowledge points
    for i, kp_data in enumerate(knowledge_points_data):
        kp_type = KnowledgePointType(kp_data["type"])
        
        # Set mastery criteria based on type
        if kp_type == KnowledgePointType.CONCEPT:
            mastery_criteria = MasteryCriteria(
                type="concept_check",
                method="选择题",
                question_count=2,
                pass_threshold=1,
            )
        elif kp_type == KnowledgePointType.FORMULA:
            mastery_criteria = MasteryCriteria(
                type="formula_check",
                method="填空题",
                question_count=3,
                pass_threshold=2,
            )
        else:  # SKILL
            mastery_criteria = MasteryCriteria(
                type="skill_check",
                method="计算题",
                question_count=2,
                pass_threshold=1,
            )

        teaching_config = TeachingConfig(
            use_examples=True,
            ask_questions=True,
            question_positions=["讲解结束"],
        )

        kp = KnowledgePoint(
            id=kp_data["id"],
            course_id="MATH_JUNIOR_01",
            name=kp_data["name"],
            type=kp_type,
            description=kp_data["description"],
            level=kp_data["level"],
            sort_order=i,
            mastery_criteria=mastery_criteria,
            teaching_config=teaching_config,
            key_points=[kp_data["description"]],
        )
        knowledge_point_repository.create(kp)

        # Add dependencies
        for dep_id in kp_data["dependencies"]:
            knowledge_point_dependency_repository.add_dependency(kp_data["id"], dep_id)


def load_assessment_data(data: dict[str, Any]) -> None:
    """Load assessment questions from JSON data.

    Args:
        data: Assessment bank JSON data.
    """
    # The JSON has "assessment_bank" at the root level
    assessment_bank = data.get("assessment_bank", [])
    
    for kp_data in assessment_bank:
        kp_id = kp_data.get("knowledge_point_id")

        for q_data in kp_data.get("questions", []):
            question_type = QuestionType(q_data["type"])
            difficulty = Difficulty(q_data.get("difficulty", "基础"))

            question = AssessmentQuestion(
                id=q_data["id"],
                kp_id=kp_id,
                type=question_type,
                content=q_data["content"],
                options=q_data.get("options"),
                correct_answer=q_data["correct_answer"],
                explanation=q_data.get("explanation", ""),
                difficulty=difficulty,
            )
            assessment_question_repository.create(question)
