# 分层Agent架构设计方案 v2.0

## 📋 文档信息

- **创建时间**: 2026-04-10
- **更新时间**: 2026-04-10
- **版本**: v2.0 (重大修订)
- **作者**: 赵阳
- **状态**: 设计方案 - 已优化
- **变更记录**: 
  - v2.0: 根据讨论优化架构,简化决策逻辑,增强扩展性
  - v1.0: 初始版本

---

## 🎯 设计目标

### 核心目标

构建一个**简洁、可扩展的工具增强型教学系统**,实现:

1. **AI主动引导教学** - 按照知识地图和教学阶段主动引导学生
2. **工具增强教学** - 图片、视频、交互等工具辅助教学
3. **规则驱动决策** - 基于规则映射,避免过度AI决策
4. **渐进式扩展** - 新工具注册即可,无需修改核心代码

### 核心理念

```
AI主动引导 + 知识地图驱动 + 工具增强教学
```

**与传统问答式AI的区别**:

| 维度 | 传统问答式AI | 本方案 |
|------|-------------|--------|
| **交互模式** | 学生提问 → AI回答 | AI讲解 → 学生回答 |
| **学习路径** | 学生主导,随意提问 | 知识地图驱动,有规划 |
| **教学阶段** | 单轮问答,无阶段 | 多阶段递进教学 |
| **工具调用** | 学生请求触发 | AI主动决策调用 |
| **学生角色** | 主动提问者 | 被引导学习者 |
| **AI角色** | 答疑助手 | 教学引导者 |

### 设计原则

- ✅ **简单优先** - 避免过度设计,规则优于AI决策
- ✅ **扩展性强** - 新工具注册即可,符合开闭原则
- ✅ **成本可控** - LLM自决策工具使用,减少不必要调用
- ✅ **渐进演进** - 从现有服务层平滑迁移

---

## 🏗️ 整体架构

### 架构全景图

```
┌─────────────────────────────────────────────────────────┐
│                    用户层 (Frontend)                     │
│            React + TypeScript 学习界面                   │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTP/SSE
┌─────────────────────────────────────────────────────────┐
│                  API层 (FastAPI)                        │
│         /api/v1/learning  /api/v1/chat                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│           TeachingFlow (教学流程协调器)                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1. 学生上下文加载                                 │  │
│  │     - 学生档案                                     │  │
│  │     - 历史学习记录                                 │  │
│  │     - 当前知识点进度                               │  │
│  │                                                    │  │
│  │  2. 教学配置加载                                   │  │
│  │     - 知识点信息                                   │  │
│  │     - 教学模式(已绑定)                             │  │
│  │     - 当前教学阶段                                 │  │
│  │                                                    │  │
│  │  3. 工具上下文准备                                 │  │
│  │     - 确定需要的工具(规则映射)                     │  │
│  │     - 准备工具上下文(注入Prompt)                   │  │
│  │                                                    │  │
│  │  4. Prompt生成                                     │  │
│  │     - 组装所有上下文                               │  │
│  │     - 注入工具使用指引                             │  │
│  │                                                    │  │
│  │  5. LLM生成内容                                    │  │
│  │     - LLM自决策是否使用工具                        │  │
│  │     - 流式输出                                     │  │
│  │                                                    │  │
│  │  6. 工具结果处理                                   │  │
│  │     - 根据工具类型决定处理策略                     │  │
│  │     - 静态资源直接透出,动态内容LLM处理             │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────┐
│            ToolRegistry (工具注册中心)                   │
├─────────────────────────────────────────────────────────┤
│  tools = {                                              │
│    "image_generation": ImageTool,                       │
│    "video_generation": VideoTool,                       │
│    "interactive_demo": InteractiveTool,                 │
│  }                                                      │
│                                                         │
│  统一接口:                                               │
│  - get_context(kp_id) → 准备工具上下文                  │
│  - execute(request) → 执行工具调用                      │
│  - get_metadata() → 工具元数据                          │
└─────────────────────────────────────────────────────────┘
         │
         ├──────────┬─────────────┬─────────────┐
         ↓          ↓             ↓             ↓
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ImageTool│ │VideoTool│ │Interact │ │Future...│
    └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

---

## 🤖 核心组件设计

### 1. TeachingFlow (教学流程协调器)

**职责**: 协调教学流程,加载上下文,组装Prompt,**不涉及复杂AI决策**

```python
class TeachingFlow:
    """
    教学流程协调器 - 替代原TeachingHostAgent
    
    核心特点:
    - 不叫"Agent",避免过度设计
    - 基于规则映射,不依赖AI决策
    - LLM自决策工具使用,无需外部决策引擎
    """
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self.student_context_loader = StudentContextLoader()
        self.llm_service = llm_service
        self.course_service = course_service
        
        # 初始化策略选择器
        self.strategy_selector = self.build_strategy_selector()
    
    def build_strategy_selector(self) -> 'ToolProcessStrategySelector':
        """构建策略选择器"""
        selector = ToolProcessStrategySelector()
        
        # 注册所有策略
        selector.register_strategy(ImageProcessStrategy())
        selector.register_strategy(VideoProcessStrategy())
        selector.register_strategy(QuestionProcessStrategy())
        selector.register_strategy(InteractiveProcessStrategy())
        
        return selector
    
    async def execute_teaching_phase(
        self,
        session: LearningSession,
        student_name: str
    ) -> AsyncGenerator[TeachingEvent, None]:
        """执行教学阶段 - 6步流程"""
        
        # ========== 步骤1: 加载学生上下文 ==========
        # 关键改进: 第一步加载学生档案和历史记录
        student_context = await self.student_context_loader.load(
            student_id=session.student_id,
            course_id=session.course_id
        )
        # student_context = {
        #     "profile": StudentProfile(...),
        #     "history": [LearningRecord(...), ...],
        #     "recent_dialogues": [...],
        #     "summary": {
        #         "total_learned": 10,
        #         "average_score": 0.85,
        #         "struggle_areas": ["几何证明"],
        #         "learning_velocity": 0.7
        #     }
        # }
        
        # ========== 步骤2: 加载教学配置 ==========
        kp_info = self.course_service.get_knowledge_point_info(session.kp_id)
        teaching_mode = get_teaching_mode_for_kp(kp_info.type)  # 已绑定
        phase_config = self.get_phase_config(teaching_mode, session.current_phase)
        
        # ========== 步骤3: 准备工具上下文 ==========
        # 关键改进: 工具选择交给模型决策,准备所有工具上下文
        # 优势: 
        # - 更灵活,模型可以根据实际需要选择工具
        # - 避免规则遗漏,导致模型无法使用工具
        # - Prompt略长,但换来更高的决策自由度
        
        # 获取所有已注册的工具
        all_tools = self.tool_registry.get_all_registered_tools()
        
        # 准备所有工具的上下文
        tool_contexts = await self.tool_registry.prepare_tool_contexts(
            all_tools,
            session.kp_id
        )
        
        # ========== 步骤4: 生成教学Prompt ==========
        prompt = self.build_teaching_prompt(
            kp_info=kp_info,
            phase_config=phase_config,
            student_context=student_context,
            tool_contexts=tool_contexts
        )
        
        # ========== 步骤5: LLM生成内容 ==========
        # 关键设计: LLM自己决定是否使用工具
        async for event in self.llm_service.stream_chat(prompt):
            
            # ========== 步骤6: 工具结果处理 ==========
            # 关键改进: 根据工具类型决定处理策略
            event = await self.process_tool_references(event, tool_contexts)
            yield event
    
    async def process_tool_references(
        self,
        event: TeachingEvent,
        tool_contexts: Dict[str, ToolContext]
    ) -> TeachingEvent:
        """
        处理工具引用 - 使用策略模式
        
        策略模式优势:
        - 策略之间完全独立
        - 策略选择逻辑清晰
        - 易于扩展新策略
        """
        # 选择并执行策略
        return await self.strategy_selector.select_and_process(
            event,
            self.tool_registry,
            self.llm_service
        )
```

---

### 2. StudentContextLoader (学生上下文加载器)

**职责**: 加载学生完整上下文,第一步就要执行

```python
class StudentContextLoader:
    """
    学生上下文加载器
    
    关键改进: 
    - 第一步加载学生档案和历史记录
    - 聚合学生画像信息
    """
    
    def __init__(self):
        self.profile_repo = student_profile_repository
        self.record_repo = learning_record_repository
    
    async def load(self, student_id: int, course_id: str) -> StudentContext:
        """加载学生完整上下文"""
        
        # 学生档案
        profile = self.profile_repo.get_by_student_and_course(
            student_id, course_id
        )
        
        # 历史学习记录
        history = self.record_repo.get_recent_by_student(
            student_id, 
            limit=10  # 最近10条记录
        )
        
        # 历史对话(如果有)
        recent_dialogues = self.get_recent_dialogues(student_id, limit=5)
        
        return StudentContext(
            profile=profile,
            history=history,
            recent_dialogues=recent_dialogues,
            
            # 聚合信息
            summary={
                "total_learned": len(history),
                "average_score": self.calculate_avg_score(history),
                "struggle_areas": self.identify_struggles(history),
                "learning_velocity": self.calculate_velocity(history)
            }
        )
    
    def identify_struggles(self, history: List[LearningRecord]) -> List[str]:
        """识别学生的困难领域"""
        struggles = []
        for record in history:
            if record.attempt_count >= 3 and record.status != "mastered":
                struggles.append(record.kp_name)
        return struggles
    
    def calculate_velocity(self, history: List[LearningRecord]) -> float:
        """计算学习速度"""
        if not history:
            return 0.5
        # 简单计算: 最近记录的平均得分
        return sum(r.score for r in history if r.score) / len(history)
```

---

### 3. ToolRegistry (工具注册中心)

**职责**: 统一管理所有教学工具,提供注册和调用接口

```python
class ToolRegistry:
    """
    工具注册中心
    
    核心特点:
    - 统一接口,新工具注册即可
    - 基于规则选择工具,不依赖AI决策
    """
    
    def __init__(self):
        self.tools: Dict[str, TeachingTool] = {}
        self.rule_engine = ToolSelectionRuleEngine()
    
    def register(self, tool_name: str, tool: 'TeachingTool'):
        """
        注册工具 - 新工具只需调用这个方法
        
        示例:
        tool_registry.register("image_generation", ImageTool())
        tool_registry.register("video_generation", VideoTool())
        """
        self.tools[tool_name] = tool
        logger.info(f"Tool registered: {tool_name}")
    
    def get_tools_needed(self, teaching_context: TeachingContext) -> List[str]:
        """
        根据教学上下文确定需要哪些工具 - 基于规则映射
        
        例如: ["image_generation", "interactive_demo"]
        """
        return self.rule_engine.select_tools(teaching_context)
    
    async def prepare_tool_contexts(
        self,
        tool_names: List[str],
        kp_id: str
    ) -> Dict[str, ToolContext]:
        """
        准备工具上下文 - 统一接口
        
        关键改进: 只加载当前知识点相关的工具上下文
        """
        contexts = {}
        for tool_name in tool_names:
            if tool_name in self.tools:
                tool = self.tools[tool_name]
                context = await tool.get_context(kp_id)
                contexts[tool_name] = context
        return contexts
    
    async def execute_tool(
        self,
        tool_name: str,
        tool_request: ToolRequest
    ) -> ToolResult:
        """执行工具调用"""
        if tool_name not in self.tools:
            raise ToolNotFoundError(tool_name)
        
        tool = self.tools[tool_name]
        return await tool.execute(tool_request)
```

---

### 4. TeachingTool (工具抽象基类)

**职责**: 定义统一接口,所有工具必须实现

```python
from abc import ABC, abstractmethod

class TeachingTool(ABC):
    """
    教学工具抽象基类
    
    所有工具必须实现这个接口,保证扩展性
    """
    
    @abstractmethod
    async def get_context(self, kp_id: str) -> ToolContext:
        """
        获取工具上下文 - 注入到Prompt中
        
        返回格式:
        {
            "tool_name": "image_generation",
            "description": "可用图片资源",
            "available_resources": [
                {"id": "IMG_001", "description": "...", "type": "..."}
            ],
            "usage_guide": "在whiteboard中返回图片ID..."
        }
        """
        pass
    
    @abstractmethod
    async def execute(self, request: ToolRequest) -> ToolResult:
        """
        执行工具调用 - LLM引用工具资源时触发
        
        request: {
            "action": "get_resource" | "generate" | ...,
            "params": {...}
        }
        
        返回: {
            "success": True,
            "resource": {...}
        }
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> ToolMetadata:
        """
        工具元数据
        
        返回: {
            "name": "image_generation",
            "description": "生图工具",
            "capabilities": ["检索图片", "模板渲染", "AI生成"],
            "resource_types": ["image"]
        }
        """
        pass
```

---

### 5. ImageTool (生图工具实现)

**职责**: 图片检索、模板渲染、AI生成

```python
class ImageTool(TeachingTool):
    """
    生图工具 - 第一期实现
    
    关键特点:
    - 三层策略: 图片库 → 模板渲染 → AI生成
    - 按需加载: 只加载当前知识点相关图片
    """
    
    def __init__(self):
        self.image_library = ImageLibrary()
        self.template_engine = TemplateEngine()
        self.ai_generator = AIImageGenerator()
    
    async def get_context(self, kp_id: str) -> ToolContext:
        """
        获取图片上下文 - 支持图片库和动态生成
        
        关键改进:
        - 如果图片库有图片,返回描述列表
        - 如果图片库无图片,返回"可生成新图片"的提示
        - 模型可以选择使用现有图片或生成新图片
        """
        
        # 检索该知识点的图片库
        images = await self.image_library.find_by_kp(kp_id)
        
        if images:
            # 情况1: 图片库有图片
            return ToolContext(
                tool_name="image_generation",
                description="可用图片资源",
                available_resources=[
                    {
                        "id": img.id,
                        "description": img.description,
                        "type": img.modality,
                        "suitable_phases": img.applicable_phases
                    }
                    for img in images
                ],
                usage_guide="""
【图片使用方式】
- 在消息中添加: "image_id": "IMG_001"
- 示例: {"type":"segment", "message":"...", "image_id":"IMG_001"}

【生成新图片】
- 如果没有合适图片,在消息中添加: "need_image": {"concept": "...", "type": "..."}
- 示例: {"type":"segment", "message":"...", "need_image": {"concept": "三角形内角和证明", "type": "proof_diagram"}}

【重要规则】
- 每个 segment 最多只能引用一个资源
- 如果需要多个图片,请分成多个 segment 输出
"""
            )
        else:
            # 情况2: 图片库无图片 - 提示可生成新图片
            return ToolContext(
                tool_name="image_generation",
                description="图片生成工具",
                available_resources=[],  # 空列表
                usage_guide="""
【图片生成功能】
- 当前知识点暂无预置图片
- 可以动态生成教学图片
- 在消息中添加: "need_image": {"concept": "图片描述", "type": "图片类型"}

【支持的图片类型】
- infographic: 信息图表(适合概念讲解)
- proof_diagram: 证明图(适合几何证明)
- step_by_step: 步骤图(适合公式推导)
- comparison: 对比图(适合辨析)

【示例】
{"type":"segment", "message":"让我们看一个例子...", "need_image": {"concept": "三角形内角和证明", "type": "proof_diagram"}}

【重要规则】
- 每个 segment 最多只能引用一个资源
"""
            )
    
    async def execute(self, request: ToolRequest) -> ToolResult:
        """执行图片获取或生成"""
        
        action = request.action
        params = request.params
        
        if action == "get_image":
            # 获取已有图片
            image_id = params["image_id"]
            image = await self.image_library.get_by_id(image_id)
            return ToolResult(success=True, resource=image)
        
        elif action == "generate_image":
            # 生成新图片
            concept = params["concept"]
            modality = params["type"]
            
            # 策略1: 尝试模板渲染
            template = self.template_engine.find_template(concept, modality)
            if template:
                image = self.template_engine.render(template, params)
                return ToolResult(success=True, resource=image)
            
            # 策略2: AI生成
            image = await self.ai_generator.generate(concept, modality, params)
            return ToolResult(success=True, resource=image)
        
        else:
            return ToolResult(success=False, error=f"Unknown action: {action}")
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="image_generation",
            description="教学图片生成工具",
            capabilities=["图片库检索", "模板渲染", "AI生成"],
            resource_types=["image"]
        )
```

---

### 7. ToolHandler (工具处理器抽象类) - 责任链模式

**职责**: 定义统一的工具处理接口,支持链式处理

```python
from abc import ABC, abstractmethod

class ToolProcessStrategy(ABC):
    """
    工具处理策略抽象基类 - 策略模式
    
    核心思想:
    - 每种工具定义自己的处理策略
    - 策略之间完全独立,互不依赖
    - 通过策略选择器选择合适的策略
    """
    
    @abstractmethod
    def can_handle(self, event: TeachingEvent) -> bool:
        """判断该策略是否能处理该事件"""
        pass
    
    @abstractmethod
    async def process(
        self, 
        event: TeachingEvent,
        tool_registry: ToolRegistry,
        llm_service: LLMService
    ) -> TeachingEvent:
        """处理事件的具体逻辑"""
        pass
```

---

### 8. ImageProcessStrategy (图片处理策略)

**职责**: 处理图片引用和生成请求

```python
class ImageProcessStrategy(ToolProcessStrategy):
    """
    图片处理策略
    
    处理场景:
    1. 引用已有图片 (image_id)
    2. 动态生成图片 (need_image)
    
    处理方式:
    - 静态资源,直接附加到事件
    - 不需要LLM处理
    """
    
    def can_handle(self, event: TeachingEvent) -> bool:
        """判断是否包含图片引用或生成请求"""
        return event.has_image_reference() or event.needs_image_generation()
    
    async def process(
        self, 
        event: TeachingEvent,
        tool_registry: ToolRegistry,
        llm_service: LLMService
    ) -> TeachingEvent:
        """处理图片引用或生成"""
        
        # 情况1: 引用已有图片
        if event.has_image_reference():
            tool_request = event.get_image_request()
            result = await tool_registry.execute_tool(
                "image_generation",
                tool_request
            )
            
            # 静态资源: 直接附加
            event.image = result.resource
            return event
        
        # 情况2: 需要生成新图片
        if event.needs_image_generation():
            tool_request = event.get_generation_request()
            result = await tool_registry.execute_tool(
                "image_generation",
                tool_request
            )
            
            event.image = result.resource
            return event
```

---

### 9. VideoProcessStrategy (视频处理策略)

```python
class VideoProcessStrategy(ToolProcessStrategy):
    """视频处理策略 - 静态资源,直接附加"""
    
    def can_handle(self, event: TeachingEvent) -> bool:
        return event.has_video_reference()
    
    async def process(
        self, 
        event: TeachingEvent,
        tool_registry: ToolRegistry,
        llm_service: LLMService
    ) -> TeachingEvent:
        tool_request = event.get_video_request()
        result = await tool_registry.execute_tool(
            "video_generation",
            tool_request
        )
        
        event.video = result.resource
        return event
```

---

### 10. QuestionProcessStrategy (题目生成处理策略)

```python
class QuestionProcessStrategy(ToolProcessStrategy):
    """题目生成处理策略 - 动态内容,需要LLM处理"""
    
    def can_handle(self, event: TeachingEvent) -> bool:
        return event.needs_question()
    
    async def process(
        self, 
        event: TeachingEvent,
        tool_registry: ToolRegistry,
        llm_service: LLMService
    ) -> TeachingEvent:
        # 生成题目
        tool_request = event.get_question_request()
        result = await tool_registry.execute_tool(
            "question_generator",
            tool_request
        )
        
        # 动态内容: 需要LLM处理
        processed_event = await llm_service.process_question(
            generated_question=result.resource,
            context=event.context
        )
        return processed_event
```

---

### 11. InteractiveProcessStrategy (交互演示处理策略)

```python
class InteractiveProcessStrategy(ToolProcessStrategy):
    """交互演示处理策略"""
    
    def can_handle(self, event: TeachingEvent) -> bool:
        return event.has_interactive_reference()
    
    async def process(
        self, 
        event: TeachingEvent,
        tool_registry: ToolRegistry,
        llm_service: LLMService
    ) -> TeachingEvent:
        tool_request = event.get_interactive_request()
        result = await tool_registry.execute_tool(
            "interactive_demo",
            tool_request
        )
        
        event.interactive = result.resource
        return event
```

---

### 12. ToolProcessStrategySelector (策略选择器)

```python
class ToolProcessStrategySelector:
    """
    工具处理策略选择器 - 策略模式的核心
    
    职责:
    - 注册所有策略
    - 根据事件选择合适的策略
    - 策略之间完全独立
    """
    
    def __init__(self):
        self.strategies: List[ToolProcessStrategy] = []
    
    def register_strategy(self, strategy: ToolProcessStrategy):
        """注册策略 - 新增工具只需注册新策略"""
        self.strategies.append(strategy)
        logger.info(f"Strategy registered: {strategy.__class__.__name__}")
    
    async def select_and_process(
        self,
        event: TeachingEvent,
        tool_registry: ToolRegistry,
        llm_service: LLMService
    ) -> TeachingEvent:
        """
        选择策略并处理事件
        
        策略选择逻辑:
        - 遍历所有策略
        - 找到第一个能处理的策略
        - 执行处理
        """
        for strategy in self.strategies:
            if strategy.can_handle(event):
                return await strategy.process(event, tool_registry, llm_service)
        
        # 没有策略能处理,返回原事件
        return event
```

---

### 6. ToolSelectionRuleEngine (工具选择规则引擎)

**职责**: 基于规则映射选择工具,不依赖AI决策

```python
class ToolSelectionRuleEngine:
    """
    工具选择规则引擎 - 基于映射
    
    关键改进: 
    - 不叫"决策引擎",避免误导
    - 基于规则映射,无需AI决策
    """
    
    # 规则: 教学阶段 + 知识点类型 → 需要的工具
    TOOL_SELECTION_RULES = {
        ("phase_1", "几何概念"): ["image_generation"],
        ("phase_2", "几何概念"): ["image_generation"],
        ("phase_1", "公式推导"): ["image_generation", "video_generation"],
        ("phase_3", "任何"): ["interactive_demo"],
        # 更多规则...
    }
    
    def select_tools(self, context: TeachingContext) -> List[str]:
        """选择需要的工具 - 基于规则映射"""
        
        # 基础规则匹配
        rule_key = (f"phase_{context.current_phase}", context.kp_type)
        tools = self.TOOL_SELECTION_RULES.get(rule_key, [])
        
        # 动态调整(根据学生能力等)
        if context.student_ability == "novice":
            # 新手可能需要更多可视化
            if "image_generation" not in tools:
                tools.append("image_generation")
        
        return tools
```

---

## 🎨 Prompt设计

### 增强的教学Prompt

```python
def build_teaching_prompt(
    kp_info: KnowledgePoint,
    phase_config: TeachingPhase,
    student_context: StudentContext,
    tool_contexts: Dict[str, ToolContext]
) -> str:
    """构建教学Prompt,注入工具上下文"""
    
    # 基础部分(现有)
    prompt = f"""
【教学任务】
讲解知识点: {kp_info.name}

【知识点信息】
- 编号: {kp_info.id}
- 类型: {kp_info.type}
- 描述: {kp_info.description}
- 核心要点: {kp_info.key_points}
- 前置知识: {kp_info.dependencies}

【学生情况】
- 学生姓名: {student_context.profile.name}
- 学习者类型: {student_context.profile.learner_type}
- 历史学习次数: {student_context.summary['total_learned']}
- 平均得分: {student_context.summary['average_score']:.0%}
- 困难领域: {', '.join(student_context.summary['struggle_areas'])}

【当前阶段】
阶段 {phase_config.order}/{phase_config.total_phases}: {phase_config.name}
- 阶段目标: {phase_config.description}
- 阶段活动: {' → '.join(phase_config.activities)}
"""
    
    # 新增: 工具上下文 ← 关键增强
    if tool_contexts:
        prompt += "\n\n【可用教学资源】\n"
        
        for tool_name, context in tool_contexts.items():
            prompt += f"\n{context.description}:\n"
            
            # 列出可用资源
            if context.available_resources:
                for resource in context.available_resources:
                    prompt += f"- ID: {resource['id']}, 类型: {resource['type']}, 描述: {resource['description']}\n"
            
            # 使用指引
            prompt += f"\n{context.usage_guide}\n"
    
    # 输出格式约束
    prompt += """

【返回格式】
请严格按照以下JSONL格式输出,每行一个独立的JSON对象:

{"type":"segment","message":"教学内容...","image_id":"IMG_001"}
{"type":"segment","message":"教学内容...","video_id":"VID_002"}
{"type":"segment","message":"提问内容...","is_question":true}
{"type":"complete","next_action":"wait_for_student"}

【重要规则】
1. 每个 segment 最多只能引用一个资源(图片/视频/演示)
2. 如果需要多个资源,请分成多个 segment 输出
3. 必须包含提问环节
4. next_action 设为 "wait_for_student"

请开始输出第{phase_config.order}阶段的内容:
"""
    
    return prompt
```

---

## 🔄 工作流程

### 完整教学流程

```
学生开始学习知识点 K3 (三角形内角和)
    ↓
┌─────────────────────────────────────────┐
│ TeachingFlow - 步骤1: 加载学生上下文     │
├─────────────────────────────────────────┤
│ 学生档案:                                │
│ - 学习者类型: intermediate               │
│ - 历史学习次数: 10                       │
│ - 平均得分: 85%                          │
│ - 困难领域: ["几何证明"]                 │
│                                          │
│ 历史学习记录:                            │
│ - K1, K2 已掌握                          │
│ - K3 正在学习                            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ TeachingFlow - 步骤2: 加载教学配置       │
├─────────────────────────────────────────┤
│ 知识点信息:                              │
│ - ID: K3                                 │
│ - 类型: 几何概念                         │
│ - 教学模式: 概念建构型                   │
│ - 当前阶段: Phase 1/4 (情境引入)         │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ TeachingFlow - 步骤3: 准备工具上下文     │
├─────────────────────────────────────────┤
│ ToolRegistry.get_tools_needed():        │
│ - 规则: (phase_1, 几何概念) → 图片      │
│ - 返回: ["image_generation"]            │
│                                          │
│ ImageTool.get_context("K3"):            │
│ - 检索K3的图片库                         │
│ - 返回:                                  │
│   IMG_001: 三角形内角和证明图            │
│   IMG_002: 三角形撕角演示                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ TeachingFlow - 步骤4: 生成Prompt         │
├─────────────────────────────────────────┤
│ 组装Prompt:                              │
│ - 知识点信息                             │
│ - 学生上下文                             │
│ - 当前阶段配置                           │
│ - 图片上下文(IMG_001, IMG_002)          │
│ - 输出格式约束                           │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ TeachingFlow - 步骤5: LLM生成内容        │
├─────────────────────────────────────────┤
│ LLM输出:                                 │
│ {"type":"segment","message":"让我们..."} │
│ {"type":"segment","message":"看这个图...",│
│  "image_id":"IMG_001"}                  │
│ {"type":"segment","message":"你发现了...│
│  什么?","is_question":true}             │
│ {"type":"complete","next_action":...}   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ TeachingFlow - 步骤6: 工具结果处理       │
├─────────────────────────────────────────┤
│ 检测到 image_id: "IMG_001"              │
│ ↓                                        │
│ 调用 ImageTool.get_image("IMG_001")     │
│ ↓                                        │
│ 返回图片资源:                            │
│ {                                        │
│   "id": "IMG_001",                       │
│   "url": "https://...",                  │
│   "svgCode": "<svg>...</svg>"           │
│ }                                        │
│ ↓                                        │
│ 静态资源: 直接附加到事件,不经过LLM       │
└─────────────────────────────────────────┘
    ↓
返回给学生: 消息文本 + 图片
```

---

## 📊 数据结构设计

### 消息结构

```typescript
interface Message {
  id: string;
  role: 'ai' | 'student';
  content: string;
  type?: 'teacher_question' | 'question' | 'feedback' | 'segment';
  
  // 图片资源 - 直接展示在消息中
  image?: {
    id: string;
    url: string;
    description: string;
    svgCode?: string;  // SVG图片
  };
  
  // 视频资源 - 未来扩展
  video?: {
    id: string;
    url: string;
    duration: number;
    description: string;
  };
  
  // 交互演示 - 未来扩展
  interactive?: {
    id: string;
    type: string;
    config: any;
  };
  
  question?: Question;
  timestamp: Date;
}
```

### 前端渲染

```typescript
const renderContent = () => {
  return (
    <div className="message-text">
      {renderMarkdown(contentToShow)}
      
      {/* 图片直接展示在消息中 */}
      {message.image && (
        <div className="message-image">
          {message.image.svgCode ? (
            <div dangerouslySetInnerHTML={{ __html: message.image.svgCode }} />
          ) : (
            <img src={message.image.url} alt={message.image.description} />
          )}
        </div>
      )}
      
      {/* 视频直接展示 */}
      {message.video && (
        <video src={message.video.url} controls />
      )}
      
      {enableTypewriter && !isComplete && <span className="typing-cursor">|</span>}
    </div>
  );
};
```

---

## 🔧 工具结果处理策略

### 核心决策

| 工具类型 | 资源性质 | 处理方式 | 理由 |
|---------|---------|---------|------|
| **图片** | 静态资源 | ✅ 直接透给学生 | 无需LLM处理,节省成本 |
| **视频** | 静态资源 | ✅ 直接透给学生 | 同上 |
| **交互演示** | 可交互资源 | ⚠️ 可能需要模型决策 | 根据交互结果决定 |
| **题目生成** | 动态生成内容 | ❌ 需要LLM处理 | 需要LLM组织语言 |

### 代码实现

```python
class ToolResultProcessor:
    """工具结果处理器 - 根据资源类型决定处理策略"""
    
    async def process_result(
        self,
        tool_name: str,
        tool_result: ToolResult,
        event: TeachingEvent,
        session: LearningSession
    ) -> ProcessingDecision:
        """
        根据工具类型决定处理策略
        
        返回:
        - DIRECT_SHOW: 直接展示给学生
        - LLM_PROCESS: 输入到LLM处理
        - INTERACTIVE: 交互式处理
        """
        
        tool = self.tool_registry.get_tool(tool_name)
        metadata = tool.get_metadata()
        
        # 策略1: 静态资源 - 直接展示
        if metadata.resource_type in ["image", "video"]:
            return ProcessingDecision(
                action="DIRECT_SHOW",
                event=event.attach_resource(tool_result.resource)
            )
        
        # 策略2: 题目生成 - 需要LLM处理
        if tool_name == "question_generator":
            return ProcessingDecision(
                action="LLM_PROCESS",
                context={
                    "generated_question": tool_result.resource,
                    "purpose": "评估学生理解"
                }
            )
        
        # 策略3: 交互演示 - 可能需要额外处理
        if tool_name == "interactive_demo":
            return ProcessingDecision(
                action="INTERACTIVE",
                event=event.attach_resource(tool_result.resource),
                instructions="学生可以操作演示,完成后继续教学"
            )
        
        # 默认: 直接展示
        return ProcessingDecision(action="DIRECT_SHOW")
```

---

## 🚀 扩展新工具

### 示例: 新增交互演示工具

#### 步骤1: 实现TeachingTool接口

```python
class InteractiveDemoTool(TeachingTool):
    """交互演示工具"""
    
    async def get_context(self, kp_id: str) -> ToolContext:
        """返回可用的交互演示"""
        demos = await self.demo_library.find_by_kp(kp_id)
        return ToolContext(
            tool_name="interactive_demo",
            description="可用交互演示",
            available_resources=[
                {"id": demo.id, "description": demo.description, "type": demo.type}
                for demo in demos
            ],
            usage_guide="在消息中添加: 'demo_id': 'DEMO_001'"
        )
    
    async def execute(self, request: ToolRequest) -> ToolResult:
        """执行交互演示"""
        if request.action == "get_demo":
            demo = await self.demo_library.get_by_id(request.params["demo_id"])
            return ToolResult(success=True, resource=demo)
        # ... 其他action
```

#### 步骤2: 注册到ToolRegistry

```python
# 系统启动时
tool_registry = ToolRegistry()

# 注册工具
tool_registry.register("image_generation", ImageTool())
tool_registry.register("interactive_demo", InteractiveDemoTool())  # ← 新增

# 更新规则引擎
TOOL_SELECTION_RULES = {
    # ...existing rules
    ("phase_3", "几何概念"): ["image_generation", "interactive_demo"],  # ← 新增
}
```

#### 步骤3: 完成!

**不需要修改TeachingFlow代码**,系统自动支持新工具。

---

## 💾 数据库设计

### 新增: 教学图片库表

```sql
-- 教学图片库表
CREATE TABLE teaching_image_library (
    id SERIAL PRIMARY KEY,
    image_id VARCHAR(50) UNIQUE NOT NULL,
    image_url TEXT,
    svg_code TEXT,
    description TEXT NOT NULL,
    
    -- 标签和分类
    knowledge_points TEXT[],  -- 关联知识点ID数组
    modality VARCHAR(50),     -- 图片类型: infographic, proof_diagram等
    difficulty VARCHAR(20),   -- 难度: easy, medium, hard
    
    -- 适用场景
    applicable_phases INTEGER[],  -- 适用教学阶段
    teaching_modes TEXT[],        -- 适用教学模式
    
    -- 元数据
    tags TEXT[],
    template_id VARCHAR(50),      -- 模板ID(如果是模板生成)
    created_by VARCHAR(20),       -- template/ai_generated/manual
    quality_score FLOAT,          -- 质量评分 0-1
    usage_count INTEGER DEFAULT 0,
    
    -- 向量嵌入(用于语义检索)
    embedding VECTOR(1536),       -- OpenAI embedding维度
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建向量索引
CREATE INDEX idx_image_embedding ON teaching_image_library 
USING ivfflat (embedding vector_cosine_ops);

-- 创建知识点索引
CREATE INDEX idx_image_kp ON teaching_image_library USING GIN(knowledge_points);
```

---

## 📈 实施路线

### Phase 1: 基础设施 (Week 1)

**目标**: 搭建工具架构基础

- [ ] 实现 TeachingTool 抽象基类
- [ ] 实现 ToolRegistry 注册中心
- [ ] 实现 StudentContextLoader
- [ ] 实现 ToolSelectionRuleEngine
- [ ] 数据库表创建(图片库表)

**交付物**:
- 可运行的工具注册框架
- 学生上下文加载功能
- 规则引擎基础版本

---

### Phase 2: 生图工具实现 (Week 2)

**目标**: 完成第一期工具 - 生图工具

- [ ] 实现 ImageTool (图片库检索)
- [ ] 实现模板渲染引擎
- [ ] 接入AI生图API
- [ ] 图片库初始化(50张高质量教学图片)
- [ ] 图片向量化(用于语义检索)

**交付物**:
- 可用的生图工具
- 50张初始教学图片
- 模板库(10个常用模板)

---

### Phase 3: 系统集成 (Week 3)

**目标**: 集成到现有教学流程

- [ ] 修改 TeachingFlow,集成工具调用
- [ ] 修改 Prompt生成,注入工具上下文
- [ ] 修改 LLM输出解析,支持工具引用
- [ ] 前端修改,支持图片渲染
- [ ] API层集成,支持新旧模式切换

**交付物**:
- 完整的端到端流程
- 前后端集成完成
- 可切换新旧模式

---

### Phase 4: 测试优化 (Week 4)

**目标**: 测试和优化

- [ ] 端到端测试(10个知识点)
- [ ] LLM图片引用准确率优化
- [ ] 性能优化(图片缓存、预加载)
- [ ] 成本分析(对比原方案)
- [ ] 文档完善

**交付物**:
- 测试报告
- 性能优化报告
- 完整技术文档

---

## 📊 成本分析

### 运行成本对比

| 场景 | 原方案(无工具) | 新方案(图片工具) | 节省 |
|------|--------------|----------------|------|
| **新知识点教学** | LLM生成文本 | LLM生成文本 + 图片库检索 | +0元 |
| **重复知识点教学** | LLM重新生成 | 图片库复用(80%) | 节省LLM调用费用 |
| **模板化场景** | LLM生成 | 模板渲染(无LLM调用) | 节省100% |
| **个性化需求** | - | AI生图(20%) | 新增成本 |

**预估**:
- 图片库复用率: 80%
- 模板渲染率: 15%
- AI生图率: 5%
- **整体成本**: 与原方案持平,但教学效果大幅提升

---

## 🎯 关键创新点

### 1. 学生上下文优先加载

**问题**: 原方案忽略学生历史信息

**解决**: 第一步加载学生档案和历史记录

```python
# 步骤1: 加载学生上下文
student_context = await self.student_context_loader.load(
    student_id=session.student_id,
    course_id=session.course_id
)
```

**效果**: AI能根据学生历史表现个性化教学

---

### 2. 按需加载工具上下文

**问题**: 原方案一次性加载所有图片

**解决**: 只加载当前知识点相关的工具上下文

```python
# 只加载当前知识点相关的图片
tool_contexts = await self.tool_registry.prepare_tool_contexts(
    tools_needed,
    session.kp_id  # ← 只加载当前知识点
)
```

**效果**: 减少Prompt长度,降低LLM成本

---

### 3. 规则映射替代AI决策

**问题**: 原方案的"决策引擎"过度设计

**解决**: 基于规则映射选择工具,LLM自决策是否使用

```python
# 规则映射: 阶段+知识点类型 → 工具
TOOL_SELECTION_RULES = {
    ("phase_1", "几何概念"): ["image_generation"],
    ("phase_2", "几何概念"): ["image_generation"],
}

# LLM自决策: 是否使用图片
LLM输出: {"type":"segment","message":"...","image_id":"IMG_001"}
```

**效果**: 
- 简化架构
- 避免AI决策错误
- 成本可控

---

### 4. 图片直接展示在消息中

**问题**: 原方案图片在白板中,不符合期望

**解决**: 图片作为消息的独立字段,直接展示

```typescript
interface Message {
  content: string;
  image?: {  // ← 独立字段
    id: string;
    url: string;
    description: string;
  };
}
```

**效果**: 更自然的内容呈现

---

### 5. 工具结果分类处理

**问题**: 原方案未考虑不同工具的处理差异

**解决**: 根据资源类型决定处理策略

```python
# 静态资源: 直接透出
if metadata.resource_type in ["image", "video"]:
    return ProcessingDecision(action="DIRECT_SHOW")

# 动态内容: LLM处理
if tool_name == "question_generator":
    return ProcessingDecision(action="LLM_PROCESS")
```

**效果**: 
- 静态资源节省LLM调用成本
- 动态内容保证质量

---

### 6. 统一工具接口

**问题**: 原方案扩展性不足

**解决**: TeachingTool抽象基类,新工具注册即可

```python
# 新增工具只需两步:
# 1. 实现接口
class InteractiveDemoTool(TeachingTool):
    async def get_context(self, kp_id): ...
    async def execute(self, request): ...

# 2. 注册
tool_registry.register("interactive_demo", InteractiveDemoTool())
```

**效果**: 符合开闭原则,扩展性极强

---

## 🎓 总结

### 架构演进

| 版本 | 核心特点 | 问题 |
|------|---------|------|
| v1.0 | 多层Agent,决策引擎 | 过度设计,AI决策不可控 |
| v2.0 | 简化架构,规则映射 | ✅ 简单、可控、可扩展 |

### 核心设计理念

```
简单性 + 扩展性 + 成本可控 + AI主动引导
```

**简单性**:
- 去掉"决策引擎",改为规则映射
- LLM自决策工具使用
- 工具结果分类处理

**扩展性**:
- 统一TeachingTool接口
- 注册机制
- 符合开闭原则

**成本可控**:
- 图片库复用(80%)
- 模板渲染(15%)
- 静态资源直接透出

**AI主动引导**:
- 知识地图驱动
- 多阶段递进教学
- 学生被引导学习

---

## 📚 参考资料

- [现有代码: teaching_prompt.py](../ai-teacher-backend/app/prompts/teaching_prompt.py)
- [现有代码: learning_service.py](../ai-teacher-backend/app/services/learning_service.py)
- [极简版学习系统设计文档](../极简版学习系统设计文档.md)
- [知识点地图: 一次函数](../课程图谱_一次函数.json)

---

**文档状态**: ✅ 已完成 v2.0

**下一步**: 开始实施 Phase 1
