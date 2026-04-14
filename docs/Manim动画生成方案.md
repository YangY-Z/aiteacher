# Manim 动画生成技术方案

> **文档版本**: v1.0  
> **创建日期**: 2026年4月13日  
> **目标**: 让教学主 Agent 自主决定生成动画，并通过 LLM 生成 Manim 代码

---

## 一、整体架构设计

### 1.1 架构流程图

```
┌──────────────────────────────────────────────────────┐
│    教学主 Agent (现有 TeachingFlow)                   │
│    - 分析学生上下文                                   │
│    - 判断知识点类型                                   │
│    - 决定是否需要动画                                 │
└──────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────┐
│    工具选择引擎 (现有 ToolSelectionEngine)            │
│    - 规则触发: 几何概念、公式推导 → 动画工具          │
│    - 准备 tool_context                               │
└──────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────┐
│    动画生成服务 (新增 AnimationGenerator)             │
│    Step 1: Prompt工程 - 构建Manim代码生成提示        │
│    Step 2: LLM生成 - 调用GLM-4生成Python代码         │
│    Step 3: 代码验证 - AST静态分析+白名单检查         │
│    Step 4: 沙箱执行 - 容器隔离渲染                   │
│    Step 5: 结果处理 - 返回视频URL                    │
└──────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────┐
│    资源存储与分发                                     │
│    - 视频文件存储 (本地/OSS)                         │
│    - 缓存管理 (相同参数复用)                         │
│    - 前端展示                                        │
└──────────────────────────────────────────────────────┘
```

### 1.2 核心设计原则

1. **安全性第一**: 所有LLM生成的代码必须在沙箱中执行
2. **渐进式增强**: 先实现基础功能，再优化性能和体验
3. **成本控制**: 缓存机制 + 异步生成 + 超时保护
4. **可观测性**: 完整的日志和监控

---

## 二、核心组件实现

### 2.1 动画生成服务 (AnimationGenerator)

#### 代码结构

```python
# ai-teacher-backend/app/services/animation_generator.py

import ast
import logging
import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Optional, Dict

from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ManimCodeValidator:
    """Manim代码验证器 - AST静态分析 + 白名单检查"""
    
    ALLOWED_IMPORTS = {
        # Manim核心模块
        'manim', 'math', 'numpy',
        # 允许的标准库
        'typing', 'collections',
    }
    
    FORBIDDEN_BUILTINS = {
        'eval', 'exec', 'compile', 'open', 
        '__import__', 'globals', 'locals',
        'input', 'breakpoint',
    }
    
    def validate(self, code: str) -> tuple[bool, str]:
        """验证代码安全性
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # 1. 解析AST
            tree = ast.parse(code)
            
            # 2. 检查imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name.split('.')[0]
                        if module not in self.ALLOWED_IMPORTS:
                            return False, f"禁止导入模块: {module}"
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module = node.module.split('.')[0]
                        if module not in self.ALLOWED_IMPORTS:
                            return False, f"禁止导入模块: {module}"
                
                # 3. 检查禁止的函数调用
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.FORBIDDEN_BUILTINS:
                            return False, f"禁止使用函数: {node.func.id}"
            
            return True, ""
            
        except SyntaxError as e:
            return False, f"代码语法错误: {e}"


class AnimationGenerator:
    """动画生成服务"""
    
    def __init__(
        self,
        output_dir: str = "./generated_media",
        timeout: int = 30,
        use_cache: bool = True,
    ):
        self.validator = ManimCodeValidator()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timeout = timeout
        self.use_cache = use_cache
        
        logger.info(f"AnimationGenerator初始化: output_dir={output_dir}")
    
    async def generate_animation(
        self,
        animation_type: str,
        params: Dict[str, Any],
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """生成动画主流程
        
        Args:
            animation_type: 动画类型 (如 "linear_function", "coordinate_system")
            params: 动画参数
            trace_id: 追踪ID
            
        Returns:
            {
                "video_url": "/media/xxx.mp4",
                "duration": 15.0,
                "cached": false
            }
        """
        trace_id = trace_id or str(uuid.uuid4())
        logger.info(f"[{trace_id}] 开始生成动画: type={animation_type}")
        
        # Step 1: 检查缓存
        cache_key = self._build_cache_key(animation_type, params)
        if self.use_cache:
            cached_result = self._check_cache(cache_key)
            if cached_result:
                logger.info(f"[{trace_id}] 使用缓存: {cache_key}")
                cached_result["cached"] = True
                return cached_result
        
        # Step 2: 生成Manim代码
        manim_code = await self._generate_manim_code(
            animation_type, params, trace_id
        )
        
        # Step 3: 验证代码
        is_valid, error = self.validator.validate(manim_code)
        if not is_valid:
            logger.error(f"[{trace_id}] 代码验证失败: {error}")
            raise ValueError(f"代码验证失败: {error}")
        
        # Step 4: 沙箱执行
        video_path = await self._execute_in_sandbox(
            manim_code, cache_key, trace_id
        )
        
        # Step 5: 返回结果
        result = {
            "video_url": f"/media/{Path(video_path).name}",
            "file_path": str(video_path),
            "duration": self._get_video_duration(video_path),
            "cached": False,
        }
        
        logger.info(f"[{trace_id}] 动画生成成功: {result['video_url']}")
        return result
    
    async def _generate_manim_code(
        self,
        animation_type: str,
        params: Dict[str, Any],
        trace_id: str,
    ) -> str:
        """使用LLM生成Manim代码"""
        
        # Prompt工程
        prompt = self._build_manim_prompt(animation_type, params)
        
        logger.info(f"[{trace_id}] 调用LLM生成Manim代码")
        
        # 调用LLM
        response = llm_service.chat(
            system_prompt=MANIM_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
        
        # 提取代码块
        code = self._extract_code_from_response(response)
        
        logger.info(f"[{trace_id}] Manim代码生成完成, 长度={len(code)}")
        return code
    
    def _build_manim_prompt(
        self, 
        animation_type: str, 
        params: Dict[str, Any]
    ) -> str:
        """构建Manim代码生成提示"""
        
        # 根据动画类型选择示例模板
        template = ANIMATION_TEMPLATES.get(
            animation_type, 
            ANIMATION_TEMPLATES["default"]
        )
        
        prompt = f"""
请生成一个Manim动画场景,要求如下:

【动画类型】
{animation_type}

【参数】
{params}

【代码示例】
```python
{template}
```

【输出要求】
1. 只输出Python代码,不要包含任何解释
2. 必须定义一个继承自Scene的类
3. 类名必须是AnimationScene
4. 代码必须可以直接运行
5. 动画时长控制在10-20秒

请输出代码:
"""
        return prompt
    
    async def _execute_in_sandbox(
        self,
        code: str,
        cache_key: str,
        trace_id: str,
    ) -> str:
        """在沙箱中执行Manim代码"""
        
        # 创建临时目录
        temp_dir = self.output_dir / f"temp_{trace_id}"
        temp_dir.mkdir(exist_ok=True)
        
        # 写入代码文件
        code_file = temp_dir / "animation.py"
        code_file.write_text(code)
        
        logger.info(f"[{trace_id}] 在沙箱中执行: {code_file}")
        
        try:
            # 使用Docker沙箱执行 (方案见第三章)
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "-v", f"{temp_dir}:/workspace",
                    "-v", f"{self.output_dir}:/output",
                    "manim-sandbox:latest",
                    "python", "/workspace/animation.py",
                ],
                timeout=self.timeout,
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                logger.error(f"[{trace_id}] 沙箱执行失败: {result.stderr}")
                raise RuntimeError(f"沙箱执行失败: {result.stderr}")
            
            # 查找生成的视频文件
            video_files = list(temp_dir.glob("*.mp4"))
            if not video_files:
                raise FileNotFoundError("未找到生成的视频文件")
            
            # 移动到输出目录
            video_path = self.output_dir / f"{cache_key}.mp4"
            video_files[0].rename(video_path)
            
            logger.info(f"[{trace_id}] 视频生成成功: {video_path}")
            return str(video_path)
            
        except subprocess.TimeoutExpired:
            logger.error(f"[{trace_id}] 沙箱执行超时")
            raise TimeoutError("动画生成超时")
        
        finally:
            # 清理临时目录
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def _build_cache_key(self, animation_type: str, params: Dict) -> str:
        """构建缓存键"""
        import hashlib
        import json
        params_str = json.dumps(params, sort_keys=True)
        hash_str = hashlib.md5(f"{animation_type}:{params_str}".encode()).hexdigest()
        return f"{animation_type}_{hash_str}"
    
    def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """检查缓存"""
        video_path = self.output_dir / f"{cache_key}.mp4"
        if video_path.exists():
            return {
                "video_url": f"/media/{cache_key}.mp4",
                "file_path": str(video_path),
                "duration": self._get_video_duration(video_path),
            }
        return None
    
    def _extract_code_from_response(self, response: str) -> str:
        """从LLM响应中提取代码块"""
        import re
        pattern = r"```python\n(.*?)\n```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1)
        return response
    
    def _get_video_duration(self, video_path: str) -> float:
        """获取视频时长"""
        # 使用ffprobe获取视频时长
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())


# Manim系统提示
MANIM_SYSTEM_PROMPT = """
你是一个专业的Manim动画代码生成专家。

你的职责:
1. 根据教学需求生成高质量的Manim动画代码
2. 代码必须安全、可运行、符合规范
3. 动画要清晰、美观、适合教学

代码规范:
- 只使用允许的导入 (manim, math, numpy)
- 不使用任何危险函数 (eval, exec, open等)
- 类名必须是 AnimationScene
- 动画时长控制在10-20秒
"""

# 动画模板库
ANIMATION_TEMPLATES = {
    "linear_function": """
from manim import *

class AnimationScene(Scene):
    def construct(self):
        # 创建坐标系
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            axis_config={"color": GREY}
        )
        
        # 绘制一次函数 y = 2x + 1
        graph = axes.plot(
            lambda x: 2*x + 1,
            color=BLUE
        )
        
        # 添加标签
        label = axes.get_graph_label(
            graph, "y=2x+1"
        )
        
        # 动画展示
        self.play(Create(axes))
        self.play(Create(graph), Write(label))
        self.wait(2)
""",
    
    "coordinate_system": """
from manim import *

class AnimationScene(Scene):
    def construct(self):
        # 创建坐标系
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
        )
        labels = axes.get_axis_labels()
        
        self.play(Create(axes), Write(labels))
        self.wait(2)
""",
    
    "default": """
from manim import *

class AnimationScene(Scene):
    def construct(self):
        text = Text("数学动画演示")
        self.play(Write(text))
        self.wait(2)
""",
}


# 全局实例
animation_generator = AnimationGenerator()
```

---

## 三、沙箱安全方案（三种可选）

### 3.1 方案一：Docker 容器沙箱（推荐）✅

#### 优势
- **隔离性强**: 进程、文件系统、网络完全隔离
- **安全性高**: 即使代码恶意也无法影响宿主机
- **资源限制**: CPU、内存、超时可精确控制
- **生产可用**: 业界成熟方案

#### 实现步骤

**1. 构建 Manim Docker 镜像**

```dockerfile
# Dockerfile.manim-sandbox
FROM python:3.11-slim

# 安装 Manim 依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libcairo2-dev \
    libpango1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Manim
RUN pip install manim==0.18.0

# 创建非root用户
RUN useradd -m -s /bin/bash manimuser

# 设置工作目录
WORKDIR /workspace

# 设置权限
RUN chown -R manimuser:manimuser /workspace

# 切换用户
USER manimuser

# 设置只读文件系统
# (在运行时通过docker run参数控制)

# 默认命令
CMD ["python"]
```

**2. 构建镜像**

```bash
cd ai-teacher-backend
docker build -f Dockerfile.manim-sandbox -t manim-sandbox:latest .
```

**3. 运行容器时的安全配置**

```python
# 在 _execute_in_sandbox 方法中

subprocess.run([
    "docker", "run", "--rm",
    
    # 资源限制
    "--memory=512m",          # 内存限制
    "--cpus=1",               # CPU限制
    "--pids-limit=50",        # 进程数限制
    
    # 文件系统隔离
    "-v", f"{temp_dir}:/workspace:rw",    # 代码目录可读写
    "-v", f"{output_dir}:/output:rw",     # 输出目录可读写
    "--read-only",                        # 其他目录只读
    "--tmpfs", "/tmp:rw,size=100m",      # 临时文件系统
    
    # 网络隔离
    "--network=none",         # 禁用网络
    
    # 安全选项
    "--security-opt=no-new-privileges",   # 禁止提权
    "--cap-drop=ALL",                     # 移除所有capabilities
    
    # 用户权限
    "--user=1000:1000",       # 非root用户运行
    
    # 镜像和命令
    "manim-sandbox:latest",
    "python", "/workspace/animation.py",
], timeout=30)
```

**4. Docker安全配置详解**

| 安全配置 | 作用 | 必要性 |
|---------|------|--------|
| `--memory=512m` | 限制内存使用 | ⭐⭐⭐ 防止内存耗尽 |
| `--cpus=1` | 限制CPU使用 | ⭐⭐⭐ 防止CPU占用过高 |
| `--pids-limit=50` | 限制进程数量 | ⭐⭐⭐ 防止fork炸弹 |
| `--network=none` | 禁用网络 | ⭐⭐⭐⭐⭐ 防止数据外泄 |
| `--read-only` | 只读文件系统 | ⭐⭐⭐⭐ 防止文件篡改 |
| `--cap-drop=ALL` | 移除所有权限 | ⭐⭐⭐⭐⭐ 最小权限原则 |
| `--user=1000:1000` | 非root用户 | ⭐⭐⭐⭐ 防止提权 |
| `--security-opt` | 禁止新权限 | ⭐⭐⭐⭐ 额外保护层 |

---

### 3.2 方案二：Python 限制执行（轻量级）

#### 适用场景
- 开发环境、快速原型验证
- 信任LLM生成的代码（已通过AST验证）

#### 实现

```python
import resource
import signal
from contextlib import contextmanager

@contextmanager
def resource_limits(timeout=30, memory_mb=512):
    """资源限制上下文管理器"""
    
    # 设置CPU时间限制
    resource.setrlimit(
        resource.RLIMIT_CPU,
        (timeout, timeout)
    )
    
    # 设置内存限制
    resource.setrlimit(
        resource.RLIMIT_AS,
        (memory_mb * 1024 * 1024, memory_mb * 1024 * 1024)
    )
    
    # 设置超时信号
    def timeout_handler(signum, frame):
        raise TimeoutError("执行超时")
    
    signal.signal(signal.SIGXCPU, timeout_handler)
    
    try:
        yield
    finally:
        # 恢复默认信号处理
        signal.signal(signal.SIGXCPU, signal.SIG_DFL)


# 使用示例
def execute_code_safely(code: str):
    """在受限环境中执行代码"""
    
    # AST验证
    validator = ManimCodeValidator()
    is_valid, error = validator.validate(code)
    if not is_valid:
        raise ValueError(error)
    
    # 创建受限的全局命名空间
    safe_globals = {
        '__builtins__': {
            'print': print,
            'range': range,
            'len': len,
            # 只添加必要的内置函数
        },
        'manim': __import__('manim'),
        'math': __import__('math'),
        'numpy': __import__('numpy'),
    }
    
    # 在资源限制下执行
    with resource_limits(timeout=30, memory_mb=512):
        exec(code, safe_globals, {})
```

#### 优缺点对比

| 特性 | Docker沙箱 | Python限制 |
|------|-----------|-----------|
| 隔离性 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 安全性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 性能开销 | 中等 | 低 |
| 实现复杂度 | 中等 | 低 |
| 生产推荐 | ✅ 是 | ❌ 否 |

---

### 3.3 方案三：gVisor/Kata Containers（企业级）

#### 适用场景
- 高安全要求的生产环境
- 多租户场景

#### gVisor 方案

```bash
# 安装gVisor
curl -fsSL https://gvisor.dev/archive.key | sudo gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" | sudo tee /etc/apt/sources.list.d/gvisor.list > /dev/null
sudo apt-get update && sudo apt-get install -y runsc

# 配置Docker使用gVisor
docker run --runtime=runsc ...
```

#### 优势
- 内核级隔离，比Docker更安全
- 性能损失小于虚拟机

---

## 四、集成到现有架构

### 4.1 工具选择引擎扩展

```python
# 修改 ai-teacher-backend/app/services/tool_selection_engine.py

class ToolSelectionRuleEngine:
    # 添加动画生成规则
    TOOL_SELECTION_RULES = {
        # Phase 1: 概念讲解
        ("phase_1", "几何概念"): ["image_generation", "animation_generator"],
        ("phase_1", "公式推导"): ["image_generation", "animation_generator"],
        ("phase_1", "函数图像"): ["animation_generator"],  # 新增
        
        # Phase 2: 深入理解
        ("phase_2", "几何概念"): ["image_generation", "animation_generator"],
        
        # ... 其他规则
    }
```

### 4.2 工具注册

```python
# ai-teacher-backend/app/services/tools/registry.py

from app.services.animation_generator import animation_generator

class ToolRegistry:
    def __init__(self):
        # 注册动画生成工具
        self.register_tool("animation_generator", {
            "name": "动画生成工具",
            "description": "生成数学动画演示",
            "executor": animation_generator,
            "context_builder": self._build_animation_context,
        })
    
    async def _build_animation_context(
        self, 
        kp_id: str
    ) -> ToolContext:
        """构建动画工具上下文"""
        
        kp_info = course_service.get_knowledge_point_info(kp_id)
        
        # 根据知识点类型确定动画类型
        animation_type = self._infer_animation_type(kp_info)
        
        context = ToolContext(
            tool_name="animation_generator",
            description=f"""
【动画生成工具】
可用生成以下类型的动画:
- linear_function: 一次函数图像
- coordinate_system: 坐标系演示
- geometric_transform: 几何变换

使用方式:
{{"animation_type": "linear_function", "params": {{"k": 2, "b": 1}}}}
""",
            params_example={
                "animation_type": animation_type,
                "params": {"kp_name": kp_info["name"]},
            }
        )
        
        return context
```

### 4.3 教学流程集成

```python
# 已有的 teaching_flow.py 会自动调用

# LLM 返回格式:
{"type":"segment", "message":"让我们看一个动画演示", "animation_id":"ANI_001"}

# TeachingFlow 会自动:
# 1. 解析 animation_id
# 2. 调用动画生成服务
# 3. 返回视频URL给前端
```

---

## 五、前端展示方案

### 5.1 视频播放组件

```typescript
// ai-teacher-frontend/src/components/AnimationPlayer.tsx

import React from 'react';

interface AnimationPlayerProps {
  videoUrl: string;
  duration?: number;
  autoPlay?: boolean;
}

export const AnimationPlayer: React.FC<AnimationPlayerProps> = ({
  videoUrl,
  duration,
  autoPlay = false,
}) => {
  return (
    <div className="animation-player">
      <video
        src={videoUrl}
        controls
        autoPlay={autoPlay}
        className="w-full rounded-lg shadow-lg"
        style={{ maxHeight: '400px' }}
      >
        您的浏览器不支持视频播放
      </video>
      
      {duration && (
        <div className="text-sm text-gray-500 mt-2">
          时长: {duration.toFixed(1)}秒
        </div>
      )}
    </div>
  );
};
```

### 5.2 API 端点

```python
# ai-teacher-backend/app/api/animation.py

from fastapi import APIRouter, HTTPException
from app.services.animation_generator import animation_generator

router = APIRouter(prefix="/api/v1/animations", tags=["animations"])

@router.post("/generate")
async def generate_animation(request: AnimationRequest):
    """生成动画API"""
    try:
        result = await animation_generator.generate_animation(
            animation_type=request.animation_type,
            params=request.params,
        )
        return result
    except TimeoutError:
        raise HTTPException(status_code=504, detail="动画生成超时")
    except Exception as e:
        logger.error(f"动画生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/{cache_key}")
async def get_cached_animation(cache_key: str):
    """获取缓存的动画"""
    video_path = animation_generator.output_dir / f"{cache_key}.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="动画不存在")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"{cache_key}.mp4"
    )
```

---

## 六、部署和运维

### 6.1 服务器要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 存储 | 20GB | 50GB+ SSD |
| Docker | 必需 | 最新稳定版 |
| FFmpeg | 必需 | 4.0+ |

### 6.2 性能优化

#### 缓存策略

```python
# 使用 Redis 缓存生成结果

import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

async def generate_animation_with_cache(
    animation_type: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """带Redis缓存的动画生成"""
    
    cache_key = _build_cache_key(animation_type, params)
    
    # 1. 检查Redis缓存
    cached = redis_client.get(f"animation:{cache_key}")
    if cached:
        return json.loads(cached)
    
    # 2. 生成动画
    result = await animation_generator.generate_animation(
        animation_type, params
    )
    
    # 3. 存入Redis (TTL 24小时)
    redis_client.setex(
        f"animation:{cache_key}",
        86400,
        json.dumps(result)
    )
    
    return result
```

#### 异步队列

```python
# 使用 Celery 异步生成

from celery import Celery

celery_app = Celery('animations', broker='redis://localhost:6379/0')

@celery_app.task(bind=True, time_limit=60)
def generate_animation_task(
    self,
    animation_type: str,
    params: Dict[str, Any],
):
    """异步动画生成任务"""
    import asyncio
    return asyncio.run(
        animation_generator.generate_animation(
            animation_type, params, trace_id=self.request.id
        )
    )


# API调用
@router.post("/generate-async")
async def generate_animation_async(request: AnimationRequest):
    """异步生成动画"""
    task = generate_animation_task.delay(
        request.animation_type,
        request.params
    )
    return {"task_id": task.id, "status": "pending"}


@router.get("/status/{task_id}")
async def get_animation_status(task_id: str):
    """查询生成状态"""
    task = generate_animation_task.AsyncResult(task_id)
    
    if task.ready():
        return {"status": "completed", "result": task.result}
    elif task.failed():
        return {"status": "failed", "error": str(task.result)}
    else:
        return {"status": "processing"}
```

---

## 七、监控和日志

### 7.1 关键指标

```python
# Prometheus metrics

from prometheus_client import Counter, Histogram, Gauge

# 动画生成计数
animation_generated_total = Counter(
    'animation_generated_total',
    'Total animations generated',
    ['animation_type', 'cached']
)

# 生成耗时
animation_generation_duration = Histogram(
    'animation_generation_duration_seconds',
    'Time spent generating animations',
    ['animation_type']
)

# 沙箱执行失败
sandbox_failures_total = Counter(
    'sandbox_failures_total',
    'Total sandbox execution failures',
    ['error_type']
)
```

### 7.2 日志规范

```python
# 结构化日志示例

logger.info(
    "动画生成完成",
    extra={
        "trace_id": trace_id,
        "animation_type": animation_type,
        "duration": duration,
        "cached": False,
        "file_size": file_size,
        "llm_tokens": tokens_used,
    }
)
```

---

## 八、成本估算

### 8.1 单次生成成本

| 项目 | 成本估算 |
|------|---------|
| LLM调用 (GLM-4) | ¥0.02-0.05 |
| CPU渲染 | ¥0.01 |
| 存储 (50MB视频) | ¥0.001 |
| **总计** | **¥0.03-0.06** |

### 8.2 月度成本（1000学生）

| 项目 | 数量 | 成本 |
|------|------|------|
| 动画生成 | 5000次 | ¥150-300 |
| 缓存命中 | 80% | 节省 ¥120-240 |
| **实际成本** | - | **¥30-60/月** |

---

## 九、实施路线图

### Phase 1: MVP (2周)

- [x] 方案设计
- [ ] Manim代码生成Prompt优化
- [ ] AST验证器实现
- [ ] Docker沙箱搭建
- [ ] 基础动画模板库 (3-5种)

### Phase 2: 集成 (1周)

- [ ] 工具注册和上下文构建
- [ ] API端点开发
- [ ] 前端视频播放组件
- [ ] 缓存机制

### Phase 3: 优化 (持续)

- [ ] 异步队列 (Celery)
- [ ] 监控和告警
- [ ] 性能优化
- [ ] 更多动画模板

---

## 十、风险评估和应对

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| LLM生成恶意代码 | 高 | 低 | AST验证 + 沙箱隔离 |
| 渲染超时 | 中 | 中 | 超时控制 + 降级方案 |
| 资源耗尽 | 高 | 中 | Docker资源限制 |
| 生成质量差 | 中 | 中 | Prompt优化 + 模板库 |

---

## 十一、总结

### 推荐方案

**生产环境**: Docker容器沙箱 + Redis缓存 + Celery异步队列

**开发环境**: Python限制执行 + 本地缓存

### 核心优势

1. **安全性**: 多层防护（AST + Docker + 资源限制）
2. **灵活性**: Agent自主决策 + LLM动态生成
3. **性能**: 缓存 + 异步 + 超时控制
4. **成本**: 缓存命中率80%+，成本可控

---

**文档版本**: v1.0  
**最后更新**: 2026年4月13日
