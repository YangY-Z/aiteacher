#!/usr/bin/env python3
"""
Demo: 宿主Agent + 图片工具 架构验证
场景：三角形内角和定理教学

架构：
- HostAgent: 决策引擎 + 内容组装
- ImageTool: SVG图解生成工具
- RuleEngine: 简化决策逻辑
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


# ============== 数据模型 ==============

class IntentType(Enum):
    """学生意图类型"""
    NEW_CONCEPT = "new_concept"           # 学习新概念
    CONFUSION = "confusion"               # 表示困惑
    DEEP_DIVE = "deep_dive"              # 深入探究
    PRACTICE = "practice"                 # 练习巩固
    PROOF_REQUEST = "proof_request"       # 请求证明


class ModalityType(Enum):
    """内容模态类型"""
    INFOGRAPHIC = "infographic"           # 信息图
    STEP_BY_STEP = "step_by_step"         # 步骤图
    COMPARISON = "comparison"             # 对比图
    PROOF_DIAGRAM = "proof_diagram"       # 证明图
    PROBLEM_VISUALIZATION = "problem_vis" # 问题可视化


@dataclass
class StudentState:
    """学生状态"""
    current_concept: str
    last_modality: Optional[ModalityType] = None
    confusion_count: int = 0
    ability_score: float = 0.5  # 0-1
    learning_history: List[str] = None
    
    def __post_init__(self):
        if self.learning_history is None:
            self.learning_history = []


@dataclass
class Intent:
    """意图分析结果"""
    type: IntentType
    concept: str
    confidence: float
    details: Dict[str, Any] = None


@dataclass
class ToolRequest:
    """工具调用请求"""
    tool_name: str
    params: Dict[str, Any]
    priority: int  # 1-5, 5最高


@dataclass
class ContentPiece:
    """生成的内容片段"""
    modality: ModalityType
    content: str  # SVG代码或其他格式
    metadata: Dict[str, Any]
    generation_time: float


@dataclass
class TeachingResponse:
    """教学响应"""
    narration: str                    # 宿主生成的引导语
    content_pieces: List[ContentPiece]
    next_steps: List[str]
    metadata: Dict[str, Any]


# ============== 规则引擎（简化决策）==============

class RuleEngine:
    """
    规则引擎：处理80%的常见教学场景
    避免过度依赖LLM决策
    """
    
    # 知识点难度映射
    CONCEPT_DIFFICULTY = {
        "三角形内角和": "medium",
        "勾股定理": "hard",
        "平行线性质": "easy",
        "圆的性质": "medium"
    }
    
    # 场景-模态映射规则
    SCENARIO_RULES = {
        (IntentType.NEW_CONCEPT, "easy"): [
            ToolRequest("image_tool", {
                "type": ModalityType.INFOGRAPHIC,
                "layout": "simple",
                "annotations": True
            }, priority=3)
        ],
        (IntentType.NEW_CONCEPT, "medium"): [
            ToolRequest("image_tool", {
                "type": ModalityType.PROOF_DIAGRAM,
                "show_process": True
            }, priority=4)
        ],
        (IntentType.NEW_CONCEPT, "hard"): [
            ToolRequest("image_tool", {
                "type": ModalityType.STEP_BY_STEP,
                "breakdown": 4
            }, priority=5)
        ],
        (IntentType.CONFUSION, "any"): [
            ToolRequest("image_tool", {
                "type": ModalityType.COMPARISON,
                "highlight_difference": True
            }, priority=4)
        ],
        (IntentType.PROOF_REQUEST, "any"): [
            ToolRequest("image_tool", {
                "type": ModalityType.PROOF_DIAGRAM,
                "methods": ["parallel_lines", "paper_tearing"],
                "show_animation": False  # demo只生成静态图
            }, priority=5)
        ],
        (IntentType.PRACTICE, "any"): [
            ToolRequest("image_tool", {
                "type": ModalityType.PROBLEM_VISUALIZATION,
                "variations": 3
            }, priority=3)
        ]
    }
    
    @classmethod
    def plan_modality(cls, intent: Intent, student_state: StudentState) -> List[ToolRequest]:
        """
        规则驱动的模态规划
        """
        difficulty = cls.CONCEPT_DIFFICULTY.get(intent.concept, "medium")
        
        # 查找匹配规则
        rule_key = (intent.type, difficulty)
        rule_key_any = (intent.type, "any")
        
        tool_requests = cls.SCENARIO_RULES.get(rule_key) or cls.SCENARIO_RULES.get(rule_key_any)
        
        if not tool_requests:
            # 降级策略：生成信息图
            tool_requests = [
                ToolRequest("image_tool", {
                    "type": ModalityType.INFOGRAPHIC,
                    "layout": "default"
                }, priority=3)
            ]
        
        # 如果学生已经困惑，调整策略
        if intent.type == IntentType.CONFUSION and student_state.last_modality:
            # 换一种模态
            if student_state.last_modality == ModalityType.PROOF_DIAGRAM:
                tool_requests = [
                    ToolRequest("image_tool", {
                        "type": ModalityType.STEP_BY_STEP,
                        "breakdown": 3,
                        "simplify": True
                    }, priority=5)
                ]
        
        return tool_requests


# ============== 图片生成工具 ==============

class ImageTool:
    """
    图片生成工具：生成教学图解
    技术栈：SVG代码生成（精确可控）
    """
    
    def __init__(self):
        # 简化版，直接在方法中生成SVG
        pass
    
    async def generate(self, params: Dict[str, Any]) -> ContentPiece:
        """
        生成图解内容
        """
        start_time = datetime.now()
        
        modality_type = params.get("type")
        
        if modality_type == ModalityType.PROOF_DIAGRAM:
            svg_content = await self._generate_proof_diagram(params)
        elif modality_type == ModalityType.COMPARISON:
            svg_content = await self._generate_comparison(params)
        elif modality_type == ModalityType.STEP_BY_STEP:
            svg_content = await self._generate_steps(params)
        else:
            svg_content = await self._generate_infographic(params)
        
        generation_time = (datetime.now() - start_time).total_seconds()
        
        return ContentPiece(
            modality=modality_type,
            content=svg_content,
            metadata={
                "format": "svg",
                "interactive": True,
                "layers": 3
            },
            generation_time=generation_time
        )
    
    async def _generate_proof_diagram(self, params: Dict[str, Any]) -> str:
        """生成证明图解"""
        methods = params.get("methods", ["parallel_lines"])
        
        # 生成平行线证明法的SVG
        svg = """<svg viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg" style="background: #f8f9fa; border-radius: 12px;">
  <!-- 标题 -->
  <text x="400" y="30" text-anchor="middle" font-size="20" font-weight="bold" fill="#2c3e50">
    三角形内角和定理证明
  </text>
  
  <!-- 主三角形 -->
  <g id="main-triangle">
    <polygon points="150,350 350,350 250,150" 
             fill="#e3f2fd" stroke="#1976d2" stroke-width="2"/>
    
    <!-- 角度标记 -->
    <path d="M 170,350 A 20,20 0 0,1 150,330" fill="none" stroke="#f44336" stroke-width="2"/>
    <text x="180" y="370" font-size="16" fill="#f44336">∠A</text>
    
    <path d="M 330,350 A 20,20 0 0,0 350,330" fill="none" stroke="#4caf50" stroke-width="2"/>
    <text x="330" y="370" font-size="16" fill="#4caf50">∠B</text>
    
    <path d="M 240,170 A 20,20 0 0,1 260,170" fill="none" stroke="#2196f3" stroke-width="2"/>
    <text x="265" y="175" font-size="16" fill="#2196f3">∠C</text>
  </g>
  
  <!-- 平行线 -->
  <g id="parallel-lines">
    <line x1="200" y1="150" x2="400" y2="150" stroke="#ff9800" stroke-width="2" stroke-dasharray="5,5"/>
    <text x="410" y="155" font-size="14" fill="#ff9800">过C点的平行线</text>
    
    <!-- 内错角标记 -->
    <path d="M 240,150 A 15,15 0 0,0 230,165" fill="none" stroke="#f44336" stroke-width="2"/>
    <text x="215" y="145" font-size="14" fill="#f44336">∠1=∠A</text>
    
    <path d="M 260,150 A 15,15 0 0,1 270,165" fill="none" stroke="#4caf50" stroke-width="2"/>
    <text x="275" y="145" font-size="14" fill="#4caf50">∠2=∠B</text>
  </g>
  
  <!-- 结论 -->
  <g id="conclusion">
    <rect x="450" y="180" width="300" height="150" fill="#fff3e0" rx="8" stroke="#ff9800"/>
    <text x="600" y="210" text-anchor="middle" font-size="16" font-weight="bold" fill="#e65100">
      证明过程
    </text>
    <text x="470" y="240" font-size="14" fill="#333">
      ∵ ∠1 = ∠A (内错角相等)
    </text>
    <text x="470" y="265" font-size="14" fill="#333">
      ∵ ∠2 = ∠B (内错角相等)
    </text>
    <text x="470" y="290" font-size="14" fill="#333">
      ∵ ∠1 + ∠C + ∠2 = 180° (平角定义)
    </text>
    <text x="470" y="315" font-size="14" font-weight="bold" fill="#1976d2">
      ∴ ∠A + ∠B + ∠C = 180°
    </text>
  </g>
  
  <!-- 交互提示 -->
  <text x="400" y="390" text-anchor="middle" font-size="12" fill="#999">
    💡 点击角度标记可以查看详细说明
  </text>
</svg>"""
        return svg
    
    async def _generate_comparison(self, params: Dict[str, Any]) -> str:
        """生成对比图"""
        return """<svg viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg" style="background: #f8f9fa; border-radius: 12px;">
  <!-- 错误方法 -->
  <g id="wrong-method">
    <rect x="20" y="50" width="350" height="300" fill="#ffebee" rx="8" stroke="#f44336" stroke-width="2"/>
    <text x="195" y="80" text-anchor="middle" font-size="18" font-weight="bold" fill="#c62828">
      ❌ 常见误解
    </text>
    
    <!-- 错误示例 -->
    <polygon points="100,300 200,300 150,150" fill="#ffcdd2" stroke="#c62828" stroke-width="2"/>
    <text x="100" y="280" font-size="14" fill="#c62828">60°</text>
    <text x="200" y="280" font-size="14" fill="#c62828">60°</text>
    <text x="160" y="200" font-size="14" fill="#c62828">60°</text>
    
    <text x="195" y="330" text-anchor="middle" font-size="14" fill="#333">
      认为"所有三角形都是60°"
    </text>
    <text x="195" y="350" text-anchor="middle" font-size="12" fill="#666">
      (只适用于等边三角形)
    </text>
  </g>
  
  <!-- 正确方法 -->
  <g id="correct-method">
    <rect x="430" y="50" width="350" height="300" fill="#e8f5e9" rx="8" stroke="#4caf50" stroke-width="2"/>
    <text x="605" y="80" text-anchor="middle" font-size="18" font-weight="bold" fill="#2e7d32">
      ✓ 正确理解
    </text>
    
    <!-- 不同类型的三角形 -->
    <polygon points="480,300 560,300 520,180" fill="#c8e6c9" stroke="#2e7d32" stroke-width="2"/>
    <text x="470" y="290" font-size="12" fill="#2e7d32">40°</text>
    <text x="560" y="290" font-size="12" fill="#2e7d32">80°</text>
    <text x="530" y="220" font-size="12" fill="#2e7d32">60°</text>
    <text x="520" y="340" text-anchor="middle" font-size="12" fill="#666">锐角三角形</text>
    
    <polygon points="640,300 720,300 680,180" fill="#c8e6c9" stroke="#2e7d32" stroke-width="2"/>
    <text x="630" y="290" font-size="12" fill="#2e7d32">30°</text>
    <text x="720" y="290" font-size="12" fill="#2e7d32">60°</text>
    <text x="690" y="220" font-size="12" fill="#2e7d32">90°</text>
    <text x="680" y="340" text-anchor="middle" font-size="12" fill="#666">直角三角形</text>
    
    <text x="605" y="370" text-anchor="middle" font-size="14" font-weight="bold" fill="#2e7d32">
      内角和总是180°，但各角大小可以变化
    </text>
  </g>
  
  <!-- 连接箭头 -->
  <path d="M 380 200 L 420 200" stroke="#666" stroke-width="3" marker-end="url(#arrowhead)"/>
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#666"/>
    </marker>
  </defs>
</svg>"""
    
    async def _generate_steps(self, params: Dict[str, Any]) -> str:
        """生成步骤图"""
        breakdown = params.get("breakdown", 4)
        
        return f"""<svg viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" style="background: #f8f9fa; border-radius: 12px;">
  <text x="400" y="30" text-anchor="middle" font-size="20" font-weight="bold" fill="#2c3e50">
    理解内角和定理的4个步骤
  </text>
  
  <!-- 步骤1 -->
  <g id="step-1" transform="translate(50, 60)">
    <rect width="160" height="90" fill="#e3f2fd" rx="8" stroke="#1976d2" stroke-width="2"/>
    <circle cx="20" cy="20" r="15" fill="#1976d2"/>
    <text x="20" y="25" text-anchor="middle" font-size="14" fill="white" font-weight="bold">1</text>
    <text x="80" y="25" text-anchor="middle" font-size="14" font-weight="bold" fill="#1976d2">观察三角形</text>
    <text x="80" y="50" text-anchor="middle" font-size="12" fill="#333">任意三角形都有</text>
    <text x="80" y="70" text-anchor="middle" font-size="12" fill="#333">三个内角</text>
  </g>
  
  <!-- 箭头 -->
  <path d="M 220 105 L 250 105" stroke="#1976d2" stroke-width="2" marker-end="url(#arrow)"/>
  
  <!-- 步骤2 -->
  <g id="step-2" transform="translate(260, 60)">
    <rect width="160" height="90" fill="#e3f2fd" rx="8" stroke="#1976d2" stroke-width="2"/>
    <circle cx="20" cy="20" r="15" fill="#1976d2"/>
    <text x="20" y="25" text-anchor="middle" font-size="14" fill="white" font-weight="bold">2</text>
    <text x="80" y="25" text-anchor="middle" font-size="14" font-weight="bold" fill="#1976d2">画平行线</text>
    <text x="80" y="50" text-anchor="middle" font-size="12" fill="#333">过顶点画对边</text>
    <text x="80" y="70" text-anchor="middle" font-size="12" fill="#333">的平行线</text>
  </g>
  
  <!-- 箭头 -->
  <path d="M 430 105 L 460 105" stroke="#1976d2" stroke-width="2" marker-end="url(#arrow)"/>
  
  <!-- 步骤3 -->
  <g id="step-3" transform="translate(470, 60)">
    <rect width="160" height="90" fill="#e3f2fd" rx="8" stroke="#1976d2" stroke-width="2"/>
    <circle cx="20" cy="20" r="15" fill="#1976d2"/>
    <text x="20" y="25" text-anchor="middle" font-size="14" fill="white" font-weight="bold">3</text>
    <text x="80" y="25" text-anchor="middle" font-size="14" font-weight="bold" fill="#1976d2">找等角</text>
    <text x="80" y="50" text-anchor="middle" font-size="12" fill="#333">利用平行线性质</text>
    <text x="80" y="70" text-anchor="middle" font-size="12" fill="#333">找出相等的角</text>
  </g>
  
  <!-- 箭头 -->
  <path d="M 640 105 L 670 105" stroke="#1976d2" stroke-width="2" marker-end="url(#arrow)"/>
  
  <!-- 步骤4 -->
  <g id="step-4" transform="translate(680, 60)">
    <rect width="160" height="90" fill="#e3f2fd" rx="8" stroke="#1976d2" stroke-width="2"/>
    <circle cx="20" cy="20" r="15" fill="#1976d2"/>
    <text x="20" y="25" text-anchor="middle" font-size="14" fill="white" font-weight="bold">4</text>
    <text x="80" y="25" text-anchor="middle" font-size="14" font-weight="bold" fill="#1976d2">得出结论</text>
    <text x="80" y="50" text-anchor="middle" font-size="12" fill="#333">三个角组成平角</text>
    <text x="80" y="70" text-anchor="middle" font-size="12" fill="#333">所以和为180°</text>
  </g>
  
  <!-- 可视化示例 -->
  <g id="visual-example" transform="translate(200, 180)">
    <text x="200" y="0" text-anchor="middle" font-size="16" font-weight="bold" fill="#2c3e50">
      动手验证：撕纸法
    </text>
    
    <!-- 原始三角形 -->
    <polygon points="100,200 200,200 150,100" fill="#fff3e0" stroke="#ff9800" stroke-width="2"/>
    <text x="120" y="180" font-size="14" fill="#ff9800">A</text>
    <text x="190" y="180" font-size="14" fill="#ff9800">B</text>
    <text x="155" y="120" font-size="14" fill="#ff9800">C</text>
    
    <!-- 箭头 -->
    <path d="M 250 150 L 300 150" stroke="#666" stroke-width="2" marker-end="url(#arrow)"/>
    <text x="275" y="140" text-anchor="middle" font-size="12" fill="#666">撕下</text>
    
    <!-- 撕下的角拼在一起 -->
    <g transform="translate(350, 100)">
      <path d="M 50,150 L 0,100 A 30,30 0 0,1 50,150" fill="#ffcdd2" stroke="#f44336" stroke-width="2"/>
      <text x="30" y="130" font-size="12" fill="#f44336">A</text>
      
      <path d="M 50,150 L 100,100 A 30,30 0 0,0 50,150" fill="#c8e6c9" stroke="#4caf50" stroke-width="2"/>
      <text x="70" y="130" font-size="12" fill="#4caf50">B</text>
      
      <path d="M 0,100 L 50,50 L 100,100" fill="#bbdefb" stroke="#2196f3" stroke-width="2"/>
      <text x="50" y="85" font-size="12" fill="#2196f3">C</text>
      
      <line x1="-10" y1="100" x2="110" y2="100" stroke="#666" stroke-width="1" stroke-dasharray="5,5"/>
    </g>
    
    <text x="425" y="280" text-anchor="middle" font-size="14" font-weight="bold" fill="#2e7d32">
      A + B + C = 180°
    </text>
  </g>
  
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#1976d2"/>
    </marker>
  </defs>
  
  <text x="400" y="480" text-anchor="middle" font-size="12" fill="#999">
    💡 每个步骤可点击展开详细说明
  </text>
</svg>"""
    
    async def _generate_infographic(self, params: Dict[str, Any]) -> str:
        """生成信息图"""
        return """<svg viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg" style="background: #f8f9fa; border-radius: 12px;">
  <text x="400" y="30" text-anchor="middle" font-size="20" font-weight="bold" fill="#2c3e50">
    三角形内角和定理
  </text>
  
  <!-- 核心信息 -->
  <g id="core-info">
    <rect x="50" y="60" width="700" height="100" fill="#e3f2fd" rx="8" stroke="#1976d2"/>
    <text x="400" y="90" text-anchor="middle" font-size="24" font-weight="bold" fill="#1976d2">
      三角形三个内角的和等于180°
    </text>
    <text x="400" y="130" text-anchor="middle" font-size="16" fill="#333">
      无论三角形的形状如何，这个结论永远成立
    </text>
  </g>
  
  <!-- 不同类型的三角形示例 -->
  <g id="examples">
    <!-- 锐角三角形 -->
    <g transform="translate(100, 200)">
      <polygon points="50,120 100,120 75,40" fill="#c8e6c9" stroke="#4caf50" stroke-width="2"/>
      <text x="45" y="110" font-size="12" fill="#4caf50">50°</text>
      <text x="100" y="110" font-size="12" fill="#4caf50">60°</text>
      <text x="80" y="60" font-size="12" fill="#4caf50">70°</text>
      <text x="75" y="150" text-anchor="middle" font-size="14" font-weight="bold" fill="#4caf50">锐角三角形</text>
      <text x="75" y="170" text-anchor="middle" font-size="12" fill="#666">50+60+70=180°</text>
    </g>
    
    <!-- 直角三角形 -->
    <g transform="translate(300, 200)">
      <polygon points="30,120 120,120 30,40" fill="#fff3e0" stroke="#ff9800" stroke-width="2"/>
      <text x="35" y="110" font-size="12" fill="#ff9800">30°</text>
      <text x="100" y="110" font-size="12" fill="#ff9800">60°</text>
      <text x="45" y="70" font-size="12" fill="#ff9800">90°</text>
      <rect x="30" y="100" width="15" height="15" fill="none" stroke="#ff9800" stroke-width="1"/>
      <text x="75" y="150" text-anchor="middle" font-size="14" font-weight="bold" fill="#ff9800">直角三角形</text>
      <text x="75" y="170" text-anchor="middle" font-size="12" fill="#666">30+60+90=180°</text>
    </g>
    
    <!-- 钝角三角形 -->
    <g transform="translate(500, 200)">
      <polygon points="20,120 130,120 50,50" fill="#ffebee" stroke="#f44336" stroke-width="2"/>
      <text x="25" y="110" font-size="12" fill="#f44336">20°</text>
      <text x="110" y="110" font-size="12" fill="#f44336">30°</text>
      <text x="60" y="65" font-size="12" fill="#f44336">130°</text>
      <text x="75" y="150" text-anchor="middle" font-size="14" font-weight="bold" fill="#f44336">钝角三角形</text>
      <text x="75" y="170" text-anchor="middle" font-size="12" fill="#666">20+30+130=180°</text>
    </g>
  </g>
  
  <!-- 应用场景 -->
  <g id="applications" transform="translate(50, 320)">
    <text x="350" y="0" text-anchor="middle" font-size="14" font-weight="bold" fill="#2c3e50">
      💡 应用场景：已知两个角，求第三个角
    </text>
    <text x="350" y="25" text-anchor="middle" font-size="12" fill="#666">
      例：∠A=45°，∠B=65°，则∠C=180°-45°-65°=70°
    </text>
  </g>
  
  <text x="400" y="390" text-anchor="middle" font-size="12" fill="#999">
    💡 点击不同三角形查看详细计算过程
  </text>
</svg>"""


# ============== 宿主Agent ==============

class HostAgent:
    """
    宿主Agent：教学决策 + 内容编排
    核心职责：
    1. 理解学生意图
    2. 规划教学内容
    3. 调用工具生成
    4. 组装多模态响应
    5. 生成教学引导语
    """
    
    def __init__(self):
        self.rule_engine = RuleEngine()
        self.image_tool = ImageTool()
        self.student_memory = {}  # 简化版学生状态存储
    
    def understand_intent(self, student_input: str, context: Dict[str, Any]) -> Intent:
        """
        意图理解（简化版：基于关键词）
        实际应用中应该用NLU模型
        """
        input_lower = student_input.lower()
        
        # 简单的规则匹配
        if any(kw in input_lower for kw in ["为什么", "怎么证明", "证明"]):
            return Intent(
                type=IntentType.PROOF_REQUEST,
                concept=self._extract_concept(student_input),
                confidence=0.8
            )
        elif any(kw in input_lower for kw in ["不懂", "不明白", "不理解", "还是不懂"]):
            return Intent(
                type=IntentType.CONFUSION,
                concept=self._extract_concept(student_input) or context.get("current_concept", ""),
                confidence=0.9
            )
        elif any(kw in input_lower for kw in ["练习", "做题", "试一试"]):
            return Intent(
                type=IntentType.PRACTICE,
                concept=self._extract_concept(student_input) or context.get("current_concept", ""),
                confidence=0.8
            )
        elif any(kw in input_lower for kw in ["再讲讲", "深入", "详细"]):
            return Intent(
                type=IntentType.DEEP_DIVE,
                concept=self._extract_concept(student_input) or context.get("current_concept", ""),
                confidence=0.7
            )
        else:
            return Intent(
                type=IntentType.NEW_CONCEPT,
                concept=self._extract_concept(student_input) or "三角形内角和",
                confidence=0.6
            )
    
    def _extract_concept(self, text: str) -> str:
        """提取知识点（简化版）"""
        concepts = ["三角形内角和", "勾股定理", "平行线", "圆的性质"]
        for concept in concepts:
            if concept in text:
                return concept
        return "三角形内角和"  # 默认
    
    def get_student_state(self, student_id: str) -> StudentState:
        """获取学生状态"""
        if student_id not in self.student_memory:
            self.student_memory[student_id] = StudentState(
                current_concept="",
                learning_history=[]
            )
        return self.student_memory[student_id]
    
    def update_student_state(self, student_id: str, intent: Intent, modality_used: ModalityType):
        """更新学生状态"""
        state = self.get_student_state(student_id)
        state.current_concept = intent.concept
        state.last_modality = modality_used
        
        if intent.type == IntentType.CONFUSION:
            state.confusion_count += 1
        
        state.learning_history.append(f"{intent.type.value}:{intent.concept}")
    
    async def orchestrate_tools(self, tool_requests: List[ToolRequest]) -> List[ContentPiece]:
        """
        编排工具调用（并行生成）
        """
        tasks = []
        
        for request in tool_requests:
            if request.tool_name == "image_tool":
                task = self.image_tool.generate(request.params)
                tasks.append(task)
        
        # 并行执行
        results = await asyncio.gather(*tasks)
        return list(results)
    
    def generate_narration(self, content_pieces: List[ContentPiece], intent: Intent) -> str:
        """
        生成教学引导语（宿主的核心价值）
        """
        if intent.type == IntentType.PROOF_REQUEST:
            return """
好的，让我为你展示三角形内角和定理的证明过程。

我们用平行线的方法来证明：

首先，看左边的三角形，我们画一条过顶点C且平行于底边AB的直线。

然后，利用平行线的性质，我们可以发现：
- 角A和角1是内错角，所以相等
- 角B和角2是内错角，所以也相等

最后，角1、角C、角2正好组成一个平角，也就是180度。

所以，角A + 角B + 角C = 180度！

你看懂了吗？如果有任何疑问，随时问我。😊
            """.strip()
        
        elif intent.type == IntentType.CONFUSION:
            return """
我理解你还有些困惑。让我换一种方式来解释。

看看这张对比图，左边是常见的误解，右边是正确的理解。

关键点是：三角形的内角和永远是180度，但每个角的大小可以变化。

想象你在撕纸：
1. 把三角形的三个角撕下来
2. 把它们拼在一起
3. 正好组成一条直线（180度）

试试看，用纸剪一个三角形，真的撕开拼一拼，你会发现这个定理是正确的！

现在清楚了吗？🎯
            """.strip()
        
        elif intent.type == IntentType.NEW_CONCEPT:
            return """
今天我们来学习一个重要的几何定理：三角形内角和定理。

无论什么形状的三角形，它的三个内角加起来总是等于180度。

这听起来很神奇，对吧？让我们通过几个例子来看看：

看图中展示了三种不同的三角形：
- 锐角三角形：所有角都小于90度
- 直角三角形：有一个角等于90度
- 钝角三角形：有一个角大于90度

虽然它们形状不同，但内角和都是180度！

接下来，你想看证明过程，还是做几道练习题？📚
            """.strip()
        
        else:
            return "让我们来学习这个知识点。"
    
    def plan_next_steps(self, content_pieces: List[ContentPiece], intent: Intent) -> List[str]:
        """
        规划下一步教学建议
        """
        if intent.type == IntentType.NEW_CONCEPT:
            return [
                "查看定理证明过程",
                "做几道练习题巩固理解",
                "了解这个定理的应用场景"
            ]
        elif intent.type == IntentType.PROOF_REQUEST:
            return [
                "换一种证明方法",
                "做练习题验证理解",
                "学习相关定理（如外角定理）"
            ]
        elif intent.type == IntentType.CONFUSION:
            return [
                "观看动态演示",
                "做基础练习题",
                "换个角度重新讲解"
            ]
        else:
            return ["继续学习", "做练习", "回顾之前的内容"]
    
    async def teach(self, student_input: str, student_id: str = "demo_student") -> TeachingResponse:
        """
        主教学流程
        """
        # 1. 获取学生状态
        student_state = self.get_student_state(student_id)
        
        # 2. 理解意图
        intent = self.understand_intent(student_input, {
            "current_concept": student_state.current_concept
        })
        
        # 3. 规划模态
        tool_requests = self.rule_engine.plan_modality(intent, student_state)
        
        # 4. 调用工具生成内容
        content_pieces = await self.orchestrate_tools(tool_requests)
        
        # 5. 生成引导语
        narration = self.generate_narration(content_pieces, intent)
        
        # 6. 规划下一步
        next_steps = self.plan_next_steps(content_pieces, intent)
        
        # 7. 更新学生状态
        if content_pieces:
            self.update_student_state(student_id, intent, content_pieces[0].modality)
        
        return TeachingResponse(
            narration=narration,
            content_pieces=content_pieces,
            next_steps=next_steps,
            metadata={
                "intent": intent.type.value,
                "concept": intent.concept,
                "confidence": intent.confidence,
                "tools_used": [req.tool_name for req in tool_requests]
            }
        )


# ============== Demo演示 ==============

async def demo():
    """
    演示宿主Agent + 图片工具的完整流程
    """
    print("=" * 60)
    print("🎓 宿主Agent + 图片工具 架构演示")
    print("=" * 60)
    
    agent = HostAgent()
    
    # 场景1：学生首次学习新概念
    print("\n【场景1】学生提问：\"什么是三角形内角和定理？\"")
    print("-" * 60)
    response1 = await agent.teach("什么是三角形内角和定理？")
    print(f"📖 宿主引导语：\n{response1.narration}\n")
    print(f"🛠️  使用工具：{response1.metadata['tools_used']}")
    print(f"📊 生成内容类型：{response1.content_pieces[0].modality.value if response1.content_pieces else 'None'}")
    print(f"💡 下一步建议：{', '.join(response1.next_steps)}")
    
    # 保存SVG到文件
    if response1.content_pieces:
        with open("/Users/zhaoyang/iFlow/aiteacher-2/demo_output_1.svg", "w", encoding="utf-8") as f:
            f.write(response1.content_pieces[0].content)
        print("✅ 图片已保存：demo_output_1.svg")
    
    # 场景2：学生要求证明
    print("\n\n【场景2】学生追问：\"能证明一下这个定理吗？\"")
    print("-" * 60)
    response2 = await agent.teach("能证明一下这个定理吗？")
    print(f"📖 宿主引导语：\n{response2.narration}\n")
    print(f"🛠️  使用工具：{response2.metadata['tools_used']}")
    print(f"📊 生成内容类型：{response2.content_pieces[0].modality.value if response2.content_pieces else 'None'}")
    
    if response2.content_pieces:
        with open("/Users/zhaoyang/iFlow/aiteacher-2/demo_output_2.svg", "w", encoding="utf-8") as f:
            f.write(response2.content_pieces[0].content)
        print("✅ 图片已保存：demo_output_2.svg")
    
    # 场景3：学生表示困惑
    print("\n\n【场景3】学生困惑：\"我还是不太明白...\"")
    print("-" * 60)
    response3 = await agent.teach("我还是不太明白")
    print(f"📖 宿主引导语：\n{response3.narration}\n")
    print(f"🛠️  使用工具：{response3.metadata['tools_used']}")
    print(f"📊 生成内容类型：{response3.content_pieces[0].modality.value if response3.content_pieces else 'None'}")
    print(f"🔄 学生困惑次数：{agent.student_memory['demo_student'].confusion_count}")
    
    if response3.content_pieces:
        with open("/Users/zhaoyang/iFlow/aiteacher-2/demo_output_3.svg", "w", encoding="utf-8") as f:
            f.write(response3.content_pieces[0].content)
        print("✅ 图片已保存：demo_output_3.svg")
    
    # 架构优势总结
    print("\n\n" + "=" * 60)
    print("📋 架构优势总结")
    print("=" * 60)
    print("""
✅ 职责清晰：
   - 宿主Agent：理解意图 → 规划内容 → 生成引导语
   - 图片工具：专注生成高质量教学图解
   
✅ 可维护性强：
   - 工具独立迭代（如升级SVG生成算法）
   - 规则引擎可快速调整教学策略
   
✅ 成本可控：
   - 图片生成成本低（SVG代码生成）
   - 决策逻辑简单，不需要每次调用大模型
   
✅ 可扩展性好：
   - 易于添加新工具（视频、3D、交互式组件）
   - 学生状态追踪机制已就位
   
✅ 质量可保证：
   - SVG代码生成，精确可控
   - 教学引导语根据场景定制
    """)
    
    print("\n📁 生成的SVG文件可在浏览器中查看")


if __name__ == "__main__":
    asyncio.run(demo())
