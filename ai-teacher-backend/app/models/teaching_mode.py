"""
教学模式模板系统 - 模型定义
支持6种教学模式：概念建构型、程序技能型、可视化理解型、对比辨析型、问题探究型、错误诊断型
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TeachingModeType(str, Enum):
    """教学模式类型"""
    CONCEPT_CONSTRUCTION = "concept_construction"   # 概念建构型
    PROCEDURAL_SKILL = "procedural_skill"           # 程序技能型
    VISUAL_UNDERSTANDING = "visual_understanding"   # 可视化理解型
    CONTRAST_ANALYSIS = "contrast_analysis"         # 对比辨析型
    PROBLEM_INQUIRY = "problem_inquiry"             # 问题探究型
    ERROR_DIAGNOSIS = "error_diagnosis"             # 错误诊断型


class KnowledgeType(str, Enum):
    """知识类型"""
    CONCEPT = "concept"           # 概念类：定义、定理
    SKILL = "skill"               # 技能类：操作步骤、算法
    VISUAL = "visual"             # 可视化类：几何、图像
    CONTRAST = "contrast"         # 对比类：易混淆概念
    INQUIRY = "inquiry"           # 探究类：开放性问题
    ERROR_PRONE = "error_prone"   # 易错类：高频错误点


class InteractionType(str, Enum):
    """交互类型"""
    OBSERVE = "observe"           # 观察
    GUIDE = "guide"               # 引导
    PRACTICE = "practice"         # 练习
    INDEPENDENT = "independent"   # 独立完成


class AIInterventionLevel(str, Enum):
    """AI介入级别"""
    HIGH = "high"       # 高介入：每步指导
    MEDIUM = "medium"   # 中介入：关键点提示
    LOW = "low"         # 低介入：仅响应请求


@dataclass
class TeachingPhase:
    """教学阶段配置"""
    name: str                              # 阶段名称
    order: int                             # 阶段顺序
    duration_minutes: tuple[int, int]      # 时长范围 (最小, 最大)
    description: str                       # 阶段描述
    activities: list[str] = field(default_factory=list)  # 活动列表
    interaction_type: InteractionType = InteractionType.OBSERVE
    ai_intervention_level: AIInterventionLevel = AIInterventionLevel.MEDIUM
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "order": self.order,
            "duration_minutes": self.duration_minutes,
            "description": self.description,
            "activities": self.activities,
            "interaction_type": self.interaction_type.value,
            "ai_intervention_level": self.ai_intervention_level.value,
        }


@dataclass
class StructuredOption:
    """结构化对话选项"""
    id: str
    text: str
    type: str = "answer"  # answer/reason/feedback/skip
    is_correct: Optional[bool] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "type": self.type,
            "is_correct": self.is_correct,
        }


@dataclass
class InteractionTemplate:
    """交互模板"""
    name: str
    prompt_template: str
    options: list[StructuredOption] = field(default_factory=list)
    allow_custom_input: bool = True
    allow_skip: bool = True
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "prompt_template": self.prompt_template,
            "options": [opt.to_dict() for opt in self.options],
            "allow_custom_input": self.allow_custom_input,
            "allow_skip": self.allow_skip,
        }


@dataclass
class TeachingModeConfig:
    """教学模式配置"""
    mode_type: TeachingModeType
    name: str
    description: str
    applicable_knowledge_types: list[KnowledgeType] = field(default_factory=list)
    phases: list[TeachingPhase] = field(default_factory=list)
    learner_type_strategies: dict[str, str] = field(default_factory=dict)  # 学习者类型 -> 策略
    assessment_criteria: list[str] = field(default_factory=list)
    common_errors: list[str] = field(default_factory=list)
    interaction_templates: dict[str, InteractionTemplate] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "mode_type": self.mode_type.value,
            "name": self.name,
            "description": self.description,
            "applicable_knowledge_types": [kt.value for kt in self.applicable_knowledge_types],
            "phases": [p.to_dict() for p in self.phases],
            "learner_type_strategies": self.learner_type_strategies,
            "assessment_criteria": self.assessment_criteria,
            "common_errors": self.common_errors,
            "interaction_templates": {k: v.to_dict() for k, v in self.interaction_templates.items()},
        }


@dataclass
class KnowledgePointTeachingConfig:
    """知识点教学配置"""
    kp_id: str
    kp_name: str
    mode_type: TeachingModeType
    knowledge_type: KnowledgeType
    custom_content: dict[str, Any] = field(default_factory=dict)
    prerequisites: list[str] = field(default_factory=list)
    estimated_time: int = 15  # 分钟
    
    def to_dict(self) -> dict:
        return {
            "kp_id": self.kp_id,
            "kp_name": self.kp_name,
            "mode_type": self.mode_type.value,
            "knowledge_type": self.knowledge_type.value,
            "custom_content": self.custom_content,
            "prerequisites": self.prerequisites,
            "estimated_time": self.estimated_time,
        }


# ============= 预定义的6种教学模式配置 =============

CONCEPT_CONSTRUCTION_MODE = TeachingModeConfig(
    mode_type=TeachingModeType.CONCEPT_CONSTRUCTION,
    name="概念建构型",
    description="适用于抽象概念、定义、定理的教学，通过情境引入、探索发现、辨析深化、简单应用四个阶段帮助学生理解概念本质",
    applicable_knowledge_types=[KnowledgeType.CONCEPT],
    phases=[
        TeachingPhase(
            name="情境引入",
            order=1,
            duration_minutes=(2, 3),
            description="展示生活场景或问题，引发认知冲突或好奇心",
            activities=["展示情境", "提出问题", "学生预测/猜想"],
            interaction_type=InteractionType.GUIDE,
            ai_intervention_level=AIInterventionLevel.MEDIUM,
        ),
        TeachingPhase(
            name="探索发现",
            order=2,
            duration_minutes=(5, 8),
            description="提供可操作的工具/例子，学生操作观察规律",
            activities=["操作工具", "观察规律", "AI引导归纳", "正式定义引入"],
            interaction_type=InteractionType.PRACTICE,
            ai_intervention_level=AIInterventionLevel.HIGH,
        ),
        TeachingPhase(
            name="辨析深化",
            order=3,
            duration_minutes=(3, 5),
            description="正例/反例判断，常见误解诊断",
            activities=["正反例判断", "误解诊断", "用自己的话解释"],
            interaction_type=InteractionType.PRACTICE,
            ai_intervention_level=AIInterventionLevel.MEDIUM,
        ),
        TeachingPhase(
            name="简单应用",
            order=4,
            duration_minutes=(3, 5),
            description="基础练习题，即时反馈",
            activities=["基础练习", "即时反馈", "错误分析"],
            interaction_type=InteractionType.INDEPENDENT,
            ai_intervention_level=AIInterventionLevel.LOW,
        ),
    ],
    learner_type_strategies={
        "novice": "完整讲授+多示例+分步引导",
        "intermediate": "引导发现+自主归纳",
        "reviewer": "概念图回顾+辨析练习",
        "advanced": "应用拓展+举一反三",
    },
    assessment_criteria=[
        "能用自己的话解释定义",
        "能识别正例和反例",
        "能判断常见误解",
        "能简单应用概念",
    ],
    common_errors=[
        "只记定义不理解本质",
        "混淆相似概念",
        "无法识别反例",
    ],
)

PROCEDURAL_SKILL_MODE = TeachingModeConfig(
    mode_type=TeachingModeType.PROCEDURAL_SKILL,
    name="程序技能型",
    description="适用于操作步骤、算法、解题程序的教学，通过整体感知、分步拆解、完整流程、变式迁移四个阶段培养技能自动化",
    applicable_knowledge_types=[KnowledgeType.SKILL],
    phases=[
        TeachingPhase(
            name="整体感知",
            order=1,
            duration_minutes=(2, 3),
            description="展示完整示例，强调最终目标",
            activities=["观看完整示例", "理解目标", "观察步骤"],
            interaction_type=InteractionType.OBSERVE,
            ai_intervention_level=AIInterventionLevel.MEDIUM,
        ),
        TeachingPhase(
            name="分步拆解",
            order=2,
            duration_minutes=(8, 12),
            description="每一步单独讲解，学生模仿操作",
            activities=["分步讲解", "模仿操作", "即时验证", "错误纠正"],
            interaction_type=InteractionType.PRACTICE,
            ai_intervention_level=AIInterventionLevel.HIGH,
        ),
        TeachingPhase(
            name="完整流程",
            order=3,
            duration_minutes=(4, 6),
            description="学生独立完成完整流程",
            activities=["独立完成", "计时挑战(可选)", "效率与正确率平衡"],
            interaction_type=InteractionType.INDEPENDENT,
            ai_intervention_level=AIInterventionLevel.LOW,
        ),
        TeachingPhase(
            name="变式迁移",
            order=4,
            duration_minutes=(4, 6),
            description="改变数字/情境，识别模式，形成自动化",
            activities=["变式练习", "识别模式", "自动化形成"],
            interaction_type=InteractionType.INDEPENDENT,
            ai_intervention_level=AIInterventionLevel.LOW,
        ),
    ],
    learner_type_strategies={
        "novice": "完整示范+模仿练习+分步指导",
        "intermediate": "分步练习+独立完成",
        "reviewer": "完整练习+变式训练",
        "advanced": "变式训练+效率提升",
    },
    assessment_criteria=[
        "能正确执行每个步骤",
        "能独立完成完整流程",
        "能应对变式问题",
        "能在合理时间内完成",
    ],
    common_errors=[
        "跳过关键步骤",
        "步骤顺序错误",
        "忽略检验环节",
    ],
)

VISUAL_UNDERSTANDING_MODE = TeachingModeConfig(
    mode_type=TeachingModeType.VISUAL_UNDERSTANDING,
    name="可视化理解型",
    description="适用于几何、图像、空间关系的教学，通过观察猜想、验证探索、形式化表达、应用拓展四个阶段培养直观理解",
    applicable_knowledge_types=[KnowledgeType.VISUAL],
    phases=[
        TeachingPhase(
            name="观察猜想",
            order=1,
            duration_minutes=(2, 4),
            description="展示动态图形，学生操作观察，提出猜想",
            activities=["观察图形", "操作探索", "提出猜想"],
            interaction_type=InteractionType.GUIDE,
            ai_intervention_level=AIInterventionLevel.MEDIUM,
        ),
        TeachingPhase(
            name="验证探索",
            order=2,
            duration_minutes=(6, 10),
            description="提供验证工具，多角度验证，特殊情况检验",
            activities=["选择验证方法", "执行验证", "特殊情况检验", "结论形成"],
            interaction_type=InteractionType.PRACTICE,
            ai_intervention_level=AIInterventionLevel.HIGH,
        ),
        TeachingPhase(
            name="形式化表达",
            order=3,
            duration_minutes=(2, 4),
            description="符号表示，语言描述，与直观联系",
            activities=["符号表示", "语言描述", "联系直观"],
            interaction_type=InteractionType.GUIDE,
            ai_intervention_level=AIInterventionLevel.MEDIUM,
        ),
        TeachingPhase(
            name="应用拓展",
            order=4,
            duration_minutes=(4, 6),
            description="计算应用，逆向问题，实际情境",
            activities=["计算应用", "逆向问题", "实际情境"],
            interaction_type=InteractionType.INDEPENDENT,
            ai_intervention_level=AIInterventionLevel.LOW,
        ),
    ],
    learner_type_strategies={
        "novice": "动画演示+引导操作",
        "intermediate": "操作探索+归纳发现",
        "reviewer": "关键点回顾+辨析练习",
        "advanced": "创造应用+开放问题",
    },
    assessment_criteria=[
        "能正确操作可视化工具",
        "能从直观发现数学规律",
        "能进行形式化表达",
        "能应用到相关问题",
    ],
    common_errors=[
        "只看图形不理解本质",
        "无法进行形式化表达",
        "忽略特殊情况",
    ],
)

CONTRAST_ANALYSIS_MODE = TeachingModeConfig(
    mode_type=TeachingModeType.CONTRAST_ANALYSIS,
    name="对比辨析型",
    description="适用于易混淆概念、相似知识点的教学，通过并置呈现、对比分析、决策练习、整合总结四个阶段帮助学生区分概念",
    applicable_knowledge_types=[KnowledgeType.CONTRAST],
    phases=[
        TeachingPhase(
            name="并置呈现",
            order=1,
            duration_minutes=(2, 4),
            description="两个概念同时展示，找相同点和不同点",
            activities=["展示两个概念", "学生找相同点", "学生找不同点"],
            interaction_type=InteractionType.GUIDE,
            ai_intervention_level=AIInterventionLevel.MEDIUM,
        ),
        TeachingPhase(
            name="对比分析",
            order=2,
            duration_minutes=(6, 10),
            description="定义对比、符号对比、例子对比、反例辨析",
            activities=["定义对比", "符号对比", "例子对比", "反例辨析"],
            interaction_type=InteractionType.PRACTICE,
            ai_intervention_level=AIInterventionLevel.HIGH,
        ),
        TeachingPhase(
            name="决策练习",
            order=3,
            duration_minutes=(4, 6),
            description="情境判断用哪个，解释选择理由",
            activities=["情境判断", "解释理由", "错误预防"],
            interaction_type=InteractionType.PRACTICE,
            ai_intervention_level=AIInterventionLevel.MEDIUM,
        ),
        TeachingPhase(
            name="整合总结",
            order=4,
            duration_minutes=(2, 4),
            description="对比表格生成，记忆口诀，自我检测",
            activities=["生成对比表格", "记忆口诀", "自我检测"],
            interaction_type=InteractionType.INDEPENDENT,
            ai_intervention_level=AIInterventionLevel.LOW,
        ),
    ],
    learner_type_strategies={
        "novice": "直接对比+详细讲解",
        "intermediate": "学生对比+引导辨析",
        "reviewer": "辨析练习+错误归类",
        "advanced": "教别人+编制辨析题",
    },
    assessment_criteria=[
        "能说出两个概念的区别",
        "能正确判断使用哪个概念",
        "能举例说明两者的应用场景",
    ],
    common_errors=[
        "混淆定义细节",
        "无法正确选择概念",
        "忽略关键区别",
    ],
)

PROBLEM_INQUIRY_MODE = TeachingModeConfig(
    mode_type=TeachingModeType.PROBLEM_INQUIRY,
    name="问题探究型",
    description="适用于开放性问题、数学思想方法的教学，通过问题情境、方案设计、执行探究、反思总结四个阶段培养探究能力",
    applicable_knowledge_types=[KnowledgeType.INQUIRY],
    phases=[
        TeachingPhase(
            name="问题情境",
            order=1,
            duration_minutes=(2, 4),
            description="真实或有趣的问题，明确探究目标",
            activities=["展示问题", "明确目标", "学生提出思路"],
            interaction_type=InteractionType.GUIDE,
            ai_intervention_level=AIInterventionLevel.MEDIUM,
        ),
        TeachingPhase(
            name="方案设计",
            order=2,
            duration_minutes=(4, 6),
            description="讨论可能方法，选择策略，预测结果",
            activities=["讨论方法", "选择策略", "预测结果"],
            interaction_type=InteractionType.PRACTICE,
            ai_intervention_level=AIInterventionLevel.MEDIUM,
        ),
        TeachingPhase(
            name="执行探究",
            order=3,
            duration_minutes=(8, 12),
            description="实施计划，记录数据，调整策略",
            activities=["实施计划", "记录数据", "调整策略", "AI提供脚手架"],
            interaction_type=InteractionType.INDEPENDENT,
            ai_intervention_level=AIInterventionLevel.MEDIUM,
        ),
        TeachingPhase(
            name="反思总结",
            order=4,
            duration_minutes=(4, 6),
            description="结果分享，方法比较，迁移应用",
            activities=["结果分享", "方法比较", "迁移应用", "思维显性化"],
            interaction_type=InteractionType.INDEPENDENT,
            ai_intervention_level=AIInterventionLevel.LOW,
        ),
    ],
    learner_type_strategies={
        "novice": "脚手架探究+分步引导",
        "intermediate": "独立探究+关键提示",
        "reviewer": "方法反思+优化策略",
        "advanced": "开放问题+自主探究",
    },
    assessment_criteria=[
        "能提出合理的探究方案",
        "能执行探究并记录数据",
        "能从探究中得出结论",
        "能反思探究过程",
    ],
    common_errors=[
        "缺乏探究方向",
        "数据记录不完整",
        "无法得出有效结论",
    ],
)

ERROR_DIAGNOSIS_MODE = TeachingModeConfig(
    mode_type=TeachingModeType.ERROR_DIAGNOSIS,
    name="错误诊断型",
    description="适用于学生高频错误点、易错计算的教学，通过暴露错误、深度分析、针对性练习、预防巩固四个阶段帮助学生避免常见错误",
    applicable_knowledge_types=[KnowledgeType.ERROR_PRONE],
    phases=[
        TeachingPhase(
            name="暴露错误",
            order=1,
            duration_minutes=(1, 2),
            description="展示典型错误解法，学生找错误",
            activities=["展示错误解法", "学生找错误", "猜测错误原因"],
            interaction_type=InteractionType.GUIDE,
            ai_intervention_level=AIInterventionLevel.MEDIUM,
        ),
        TeachingPhase(
            name="深度分析",
            order=2,
            duration_minutes=(4, 6),
            description="错误类型归类，错误原因剖析，正确方法对比",
            activities=["错误归类", "原因分析", "正确方法对比", "记忆策略"],
            interaction_type=InteractionType.GUIDE,
            ai_intervention_level=AIInterventionLevel.HIGH,
        ),
        TeachingPhase(
            name="针对性练习",
            order=3,
            duration_minutes=(6, 10),
            description="同类错误题目，即时纠错，自我监控训练",
            activities=["同类错误练习", "即时纠错", "自我监控", "连续正确"],
            interaction_type=InteractionType.PRACTICE,
            ai_intervention_level=AIInterventionLevel.HIGH,
        ),
        TeachingPhase(
            name="预防巩固",
            order=4,
            duration_minutes=(2, 4),
            description="检查清单，自我提醒策略，类似情境迁移",
            activities=["检查清单", "自我提醒", "类似情境迁移"],
            interaction_type=InteractionType.INDEPENDENT,
            ai_intervention_level=AIInterventionLevel.LOW,
        ),
    ],
    learner_type_strategies={
        "novice": "错误预防+正确示范",
        "intermediate": "错误分析+针对性练习",
        "reviewer": "错误归类+辨析练习",
        "advanced": "错误编制+教别人",
    },
    assessment_criteria=[
        "能识别典型错误",
        "能分析错误原因",
        "能避免同类错误",
        "能帮助他人避免错误",
    ],
    common_errors=[
        "错误原因分析不深入",
        "重复犯同类错误",
        "无法迁移到类似情境",
    ],
)

# 教学模式配置字典
TEACHING_MODE_CONFIGS: dict[TeachingModeType, TeachingModeConfig] = {
    TeachingModeType.CONCEPT_CONSTRUCTION: CONCEPT_CONSTRUCTION_MODE,
    TeachingModeType.PROCEDURAL_SKILL: PROCEDURAL_SKILL_MODE,
    TeachingModeType.VISUAL_UNDERSTANDING: VISUAL_UNDERSTANDING_MODE,
    TeachingModeType.CONTRAST_ANALYSIS: CONTRAST_ANALYSIS_MODE,
    TeachingModeType.PROBLEM_INQUIRY: PROBLEM_INQUIRY_MODE,
    TeachingModeType.ERROR_DIAGNOSIS: ERROR_DIAGNOSIS_MODE,
}