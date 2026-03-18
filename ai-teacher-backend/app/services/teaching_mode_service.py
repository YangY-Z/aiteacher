"""
教学模式服务 - 教学模式模板系统的核心服务
"""

from typing import Any, Optional
from app.models.teaching_mode import (
    TeachingModeType,
    TeachingModeConfig,
    TeachingPhase,
    KnowledgeType,
    InteractionType,
    StructuredOption,
    InteractionTemplate,
    TEACHING_MODE_CONFIGS,
    KnowledgePointTeachingConfig,
)
from app.models.learner_profile import LearnerType


class TeachingModeService:
    """教学模式服务"""
    
    def __init__(self):
        self._mode_configs = TEACHING_MODE_CONFIGS
    
    def get_mode_config(self, mode_type: TeachingModeType) -> TeachingModeConfig:
        """获取教学模式配置"""
        return self._mode_configs.get(mode_type)
    
    def get_all_modes(self) -> list[TeachingModeConfig]:
        """获取所有教学模式配置"""
        return list(self._mode_configs.values())
    
    def recommend_mode_for_knowledge(
        self,
        kp_type: str,
        learner_type: LearnerType = LearnerType.INTERMEDIATE,
        error_rate: float = 0.0,
        has_similar_concept: bool = False,
    ) -> TeachingModeType:
        """
        根据知识点类型、学习者类型、错误历史推荐教学模式
        
        Args:
            kp_type: 知识点类型 (concept/skill/visual/contrast/inquiry)
            learner_type: 学习者类型
            error_rate: 历史错误率
            has_similar_concept: 是否有相似概念需要辨析
            
        Returns:
            推荐的教学模式类型
        """
        # 规则1: 高错误率 → 错误诊断型
        if error_rate > 0.4:
            return TeachingModeType.ERROR_DIAGNOSIS
        
        # 规则2: 有相似概念 → 对比辨析型
        if has_similar_concept:
            return TeachingModeType.CONTRAST_ANALYSIS
        
        # 规则3: 根据知识类型匹配
        type_mapping = {
            "concept": TeachingModeType.CONCEPT_CONSTRUCTION,
            "formula": TeachingModeType.CONCEPT_CONSTRUCTION,
            "skill": TeachingModeType.PROCEDURAL_SKILL,
            "visual": TeachingModeType.VISUAL_UNDERSTANDING,
            "contrast": TeachingModeType.CONTRAST_ANALYSIS,
            "inquiry": TeachingModeType.PROBLEM_INQUIRY,
            "error_prone": TeachingModeType.ERROR_DIAGNOSIS,
        }
        
        return type_mapping.get(kp_type, TeachingModeType.CONCEPT_CONSTRUCTION)
    
    def get_teaching_strategy(
        self,
        mode_type: TeachingModeType,
        learner_type: LearnerType,
    ) -> str:
        """根据学习者类型获取教学策略"""
        mode_config = self.get_mode_config(mode_type)
        if not mode_config:
            return "标准教学流程"
        
        return mode_config.learner_type_strategies.get(
            learner_type.value, 
            "标准教学流程"
        )
    
    def get_current_phase(
        self,
        mode_type: TeachingModeType,
        phase_order: int,
    ) -> Optional[TeachingPhase]:
        """获取当前教学阶段"""
        mode_config = self.get_mode_config(mode_type)
        if not mode_config:
            return None
        
        for phase in mode_config.phases:
            if phase.order == phase_order:
                return phase
        
        return None
    
    def get_next_phase(
        self,
        mode_type: TeachingModeType,
        current_phase_order: int,
    ) -> Optional[TeachingPhase]:
        """获取下一个教学阶段"""
        mode_config = self.get_mode_config(mode_type)
        if not mode_config:
            return None
        
        for phase in mode_config.phases:
            if phase.order == current_phase_order + 1:
                return phase
        
        return None  # 已是最后阶段
    
    def get_phase_count(self, mode_type: TeachingModeType) -> int:
        """获取教学模式的总阶段数"""
        mode_config = self.get_mode_config(mode_type)
        if not mode_config:
            return 0
        return len(mode_config.phases)
    
    def generate_structured_options(
        self,
        mode_type: TeachingModeType,
        context: str,
        question_type: str = "reason",
    ) -> list[StructuredOption]:
        """
        生成结构化对话选项
        
        Args:
            mode_type: 教学模式类型
            context: 当前上下文（如学生选择了错误答案）
            question_type: 问题类型 (reason/choice/feedback)
            
        Returns:
            结构化选项列表
        """
        # 根据上下文生成不同类型的选项
        if question_type == "reason":
            # 学生选择错误答案时，询问原因
            return [
                StructuredOption(
                    id="reason_1",
                    text="我记得老师讲过，但记不清具体内容",
                    type="reason",
                ),
                StructuredOption(
                    id="reason_2",
                    text="我觉得这个答案更合理",
                    type="reason",
                ),
                StructuredOption(
                    id="reason_3",
                    text="我猜的，不确定",
                    type="reason",
                ),
                StructuredOption(
                    id="reason_custom",
                    text="其他（请简短说明）",
                    type="reason",
                ),
            ]
        
        elif question_type == "choice":
            # 选择题选项（需要根据具体题目生成）
            return [
                StructuredOption(id="A", text="选项A", type="answer"),
                StructuredOption(id="B", text="选项B", type="answer"),
                StructuredOption(id="C", text="选项C", type="answer"),
                StructuredOption(id="D", text="选项D", type="answer"),
            ]
        
        elif question_type == "feedback":
            # 反馈选项
            return [
                StructuredOption(
                    id="understand",
                    text="我理解了，继续",
                    type="feedback",
                ),
                StructuredOption(
                    id="confused",
                    text="还是有点困惑",
                    type="feedback",
                ),
                StructuredOption(
                    id="more_example",
                    text="能再举个例子吗？",
                    type="feedback",
                ),
            ]
        
        return []
    
    def generate_teaching_prompt(
        self,
        mode_type: TeachingModeType,
        phase: TeachingPhase,
        kp_info: dict[str, Any],
        learner_type: LearnerType,
    ) -> str:
        """
        生成教学Prompt
        
        Args:
            mode_type: 教学模式类型
            phase: 当前教学阶段
            kp_info: 知识点信息
            learner_type: 学习者类型
            
        Returns:
            教学Prompt字符串
        """
        strategy = self.get_teaching_strategy(mode_type, learner_type)
        
        prompt = f"""当前教学模式：{mode_type.value}
当前阶段：{phase.name}（第{phase.order}阶段）
教学策略：{strategy}
交互类型：{phase.interaction_type.value}
AI介入级别：{phase.ai_intervention_level.value}

知识点信息：
- 名称：{kp_info.get('name', '未知')}
- 描述：{kp_info.get('description', '')}
- 难度：{kp_info.get('difficulty', 2)}

阶段目标：{phase.description}
阶段活动：{', '.join(phase.activities)}

请根据以上信息，生成适合当前阶段的教学内容。
输出格式使用JSONL，每行一个JSON对象。
"""
        return prompt
    
    def create_kp_teaching_config(
        self,
        kp_id: str,
        kp_name: str,
        kp_type: str,
        prerequisites: list[str] = None,
        custom_content: dict[str, Any] = None,
        estimated_time: int = 15,
    ) -> KnowledgePointTeachingConfig:
        """
        创建知识点教学配置
        
        Args:
            kp_id: 知识点ID
            kp_name: 知识点名称
            kp_type: 知识点类型
            prerequisites: 前置知识点ID列表
            custom_content: 自定义内容
            estimated_time: 预估时间（分钟）
            
        Returns:
            知识点教学配置
        """
        # 推荐教学模式
        mode_type = self.recommend_mode_for_knowledge(kp_type)
        
        # 映射知识类型
        knowledge_type_mapping = {
            "concept": KnowledgeType.CONCEPT,
            "formula": KnowledgeType.CONCEPT,
            "skill": KnowledgeType.SKILL,
            "visual": KnowledgeType.VISUAL,
            "contrast": KnowledgeType.CONTRAST,
            "inquiry": KnowledgeType.INQUIRY,
            "error_prone": KnowledgeType.ERROR_PRONE,
        }
        
        return KnowledgePointTeachingConfig(
            kp_id=kp_id,
            kp_name=kp_name,
            mode_type=mode_type,
            knowledge_type=knowledge_type_mapping.get(kp_type, KnowledgeType.CONCEPT),
            custom_content=custom_content or {},
            prerequisites=prerequisites or [],
            estimated_time=estimated_time,
        )


# 单例实例
teaching_mode_service = TeachingModeService()
