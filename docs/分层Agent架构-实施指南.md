# 分层Agent架构实施指南

## 📚 概述

本文档说明如何使用已实现的分层Agent架构组件。

## 🏗️ 架构组件

### 1. 核心组件

| 组件 | 文件路径 | 职责 |
|------|---------|------|
| **TeachingTool** | `app/services/tools/base.py` | 工具抽象基类,定义统一接口 |
| **ToolRegistry** | `app/services/tools/registry.py` | 工具注册中心,管理所有工具 |
| **StudentContextLoader** | `app/services/student_context_loader.py` | 加载学生完整上下文 |
| **ToolSelectionRuleEngine** | `app/services/tool_selection_engine.py` | 基于规则选择工具 |
| **TeachingFlow** | `app/services/teaching_flow.py` | 教学流程协调器 |
| **ToolProcessStrategy** | `app/services/tool_strategies.py` | 工具处理策略(策略模式) |

### 2. 数据模型

| 模型 | 文件路径 | 用途 |
|------|---------|------|
| **ToolMetadata** | `app/models/tool.py` | 工具元数据 |
| **ToolContext** | `app/models/tool.py` | 工具上下文(注入Prompt) |
| **ToolRequest** | `app/models/tool.py` | 工具调用请求 |
| **ToolResult** | `app/models/tool.py` | 工具执行结果 |
| **TeachingEvent** | `app/models/tool.py` | 教学事件 |
| **StudentContext** | `app/models/tool.py` | 学生上下文 |

## 🚀 快速开始

### 步骤1: 初始化系统

在应用启动时初始化工具系统:

```python
# app/main.py

from app.core.init_tools import initialize_system

# 在应用启动时调用
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 初始化工具系统
    initialize_system()
    
    # 其他初始化...
```

### 步骤2: 注册工具

添加新的教学工具:

```python
from app.services.tools.registry import tool_registry
from app.services.tools.base import TeachingTool

class MyCustomTool(TeachingTool):
    """自定义工具"""
    
    async def get_context(self, kp_id: str):
        # 返回工具上下文
        return ToolContext(
            tool_name="my_custom_tool",
            description="自定义工具",
            available_resources=[...],
            usage_guide="..."
        )
    
    async def execute(self, request: ToolRequest):
        # 执行工具调用
        return ToolResult(success=True, resource={...})
    
    def get_metadata(self):
        return ToolMetadata(
            name="my_custom_tool",
            description="自定义工具",
            capabilities=["功能1", "功能2"],
            resource_types=[ResourceType.IMAGE]
        )

# 注册工具
tool_registry.register("my_custom_tool", MyCustomTool())
```

### 步骤3: 使用TeachingFlow

在API端点中使用TeachingFlow:

```python
from fastapi import APIRouter
from app.services.teaching_flow import teaching_flow
from app.repositories.learning_repository import learning_session_repository

router = APIRouter()

@router.post("/teach")
async def teach(session_id: str):
    """执行教学流程"""
    # 获取学习会话
    session = learning_session_repository.get_by_id(session_id)
    
    # 执行教学流程
    async def generate():
        async for event in teaching_flow.execute_teaching_phase(
            session, 
            student_name="张三"
        ):
            yield f"data: {event}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

## 📖 详细用法

### 1. 工具上下文准备

```python
from app.services.tools.registry import tool_registry

# 获取所有注册的工具
all_tools = tool_registry.get_all_registered_tools()
# 返回: ["image_generation", "video_generation", ...]

# 准备工具上下文
contexts = await tool_registry.prepare_tool_contexts(
    ["image_generation"],
    "K3"  # 知识点ID
)

# 获取工具上下文
image_context = contexts["image_generation"]
print(image_context.description)  # "可用图片资源"
print(image_context.available_resources)  # [...]
```

### 2. 工具选择规则

```python
from app.services.tool_selection_engine import (
    tool_selection_engine,
    TeachingContext
)

# 创建教学上下文
context = TeachingContext(
    current_phase=1,
    kp_type="几何概念",
    student_ability="novice"
)

# 选择工具
tools = tool_selection_engine.select_tools(context)
# 返回: ["image_generation"]

# 添加自定义规则
tool_selection_engine.add_rule(
    phase=5,
    kp_type="综合应用",
    tools=["interactive_demo", "question_generator"]
)
```

### 3. 学生上下文加载

```python
from app.services.student_context_loader import student_context_loader

# 加载学生上下文
student_context = await student_context_loader.load(
    student_id=1,
    course_id="MATH_JUNIOR_01"
)

# 访问学生信息
print(student_context.profile.student_id)
print(student_context.history)  # 学习记录列表
print(student_context.summary["average_score"])  # 平均分
print(student_context.summary["struggle_areas"])  # 困难领域
```

### 4. 工具执行

```python
from app.models.tool import ToolRequest

# 获取图片
request = ToolRequest(
    action="get_image",
    params={"image_id": "IMG_001"}
)
result = await tool_registry.execute_tool("image_generation", request)

if result.success:
    print(result.resource)  # {"id": "IMG_001", "url": "...", ...}

# 生成图片
request = ToolRequest(
    action="generate_image",
    params={
        "concept": "三角形内角和证明",
        "type": "proof_diagram"
    }
)
result = await tool_registry.execute_tool("image_generation", request)
```

### 5. 工具处理策略

```python
from app.services.tool_strategies import (
    build_default_strategy_selector,
    ImageProcessStrategy
)

# 创建策略选择器
selector = build_default_strategy_selector()

# 处理事件
processed_event = await selector.select_and_process(
    event=event,
    tool_registry=tool_registry,
    llm_service=llm_service
)

# 注册自定义策略
selector.register_strategy(MyCustomStrategy())
```

## 🔧 配置与扩展

### 添加新的工具类型

1. 实现TeachingTool接口:

```python
from app.services.tools.base import TeachingTool

class VideoTool(TeachingTool):
    async def get_context(self, kp_id: str):
        # ...
    
    async def execute(self, request: ToolRequest):
        # ...
    
    def get_metadata(self):
        # ...
```

2. 注册工具:

```python
# app/core/init_tools.py

def initialize_tools():
    # ...
    video_tool = VideoTool()
    tool_registry.register("video_generation", video_tool)
```

3. 添加选择规则:

```python
tool_selection_engine.add_rule(
    phase=1,
    kp_type="公式推导",
    tools=["image_generation", "video_generation"]
)
```

### 自定义工具处理策略

1. 实现策略类:

```python
from app.services.tool_strategies import ToolProcessStrategy

class MyCustomStrategy(ToolProcessStrategy):
    def can_handle(self, event):
        # 判断是否能处理该事件
        return event.message.contains("custom_resource")
    
    async def process(self, event, tool_registry, llm_service):
        # 处理事件
        # ...
        return processed_event
```

2. 注册策略:

```python
from app.services.tool_strategies import strategy_selector

strategy_selector.register_strategy(MyCustomStrategy())
```

## 🧪 测试

运行系统测试:

```python
import asyncio
from app.core.init_tools import test_system

# 初始化系统
initialize_system()

# 运行测试
asyncio.run(test_system())
```

## 📊 性能优化

### 1. 工具上下文缓存

```python
# 未来可以添加缓存层
class CachedToolRegistry(ToolRegistry):
    def __init__(self):
        super().__init__()
        self.context_cache = {}
    
    async def prepare_tool_contexts(self, tool_names, kp_id):
        cache_key = f"{kp_id}:{','.join(tool_names)}"
        if cache_key in self.context_cache:
            return self.context_cache[cache_key]
        
        contexts = await super().prepare_tool_contexts(tool_names, kp_id)
        self.context_cache[cache_key] = contexts
        return contexts
```

### 2. 学生上下文预加载

```python
# 在学生登录时预加载上下文
@student_router.post("/login")
async def login(student_id: int):
    # 预加载学生上下文
    student_context = await student_context_loader.load(
        student_id, 
        course_id="MATH_JUNIOR_01"
    )
    # 缓存到Redis...
```

## 🔍 调试与日志

所有组件都使用标准的Python logging:

```python
import logging

logger = logging.getLogger(__name__)

# 日志级别
logging.basicConfig(level=logging.INFO)

# 查看详细日志
logging.getLogger("app.services.tools").setLevel(logging.DEBUG)
logging.getLogger("app.services.teaching_flow").setLevel(logging.DEBUG)
```

## 📝 最佳实践

1. **工具设计原则**:
   - 单一职责: 每个工具只负责一种资源类型
   - 异步优先: 所有方法使用async/await
   - 错误处理: 永远返回ToolResult,不抛出异常

2. **规则设计原则**:
   - 简单映射: 避免复杂的条件逻辑
   - 明确定义: 每个规则有清晰的适用场景
   - 可配置化: 规则可以动态添加/修改

3. **性能优化**:
   - 按需加载: 只加载当前知识点需要的工具
   - 缓存结果: 缓存工具上下文和执行结果
   - 异步处理: 所有IO操作使用async

## 🚨 常见问题

### Q: 如何添加新的工具?

A: 实现`TeachingTool`接口,然后在`initialize_tools()`中注册。

### Q: 如何修改工具选择规则?

A: 使用`tool_selection_engine.add_rule()`或修改`TOOL_SELECTION_RULES`字典。

### Q: 如何扩展StudentContext?

A: 修改`StudentContextLoader._compute_summary()`方法,添加新的统计维度。

### Q: 如何处理工具执行失败?

A: 检查`ToolResult.success`,查看`ToolResult.error`获取错误信息。

## 📚 相关文档

- [分层Agent架构设计方案](./分层Agent架构设计方案.md)
- [Python后端开发规范](../worklog/rules.md)
- [数据库Schema设计](../数据库Schema设计.md)

---

**文档版本**: v1.0  
**创建日期**: 2026-04-10  
**维护者**: 赵阳
