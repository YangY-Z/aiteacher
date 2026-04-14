"""Animation generator using OpenSandbox for Manim code execution.

This module integrates OpenSandbox to safely execute LLM-generated Manim code
in isolated sandbox environments.

Architecture:
    User Request → LLM generates Manim code → OpenSandbox executes → Return video

Security:
    - OpenSandbox provides container isolation
    - Code execution is sandboxed with resource limits
    - Network disabled for security
"""

import asyncio
import logging
import re
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


# Manim code generation system prompt
MANIM_SYSTEM_PROMPT = """你是一个专业的Manim动画代码生成专家。

你的职责：
1. 根据教学需求生成高质量的Manim动画代码
2. 代码必须安全、可运行、符合规范
3. 动画要清晰、美观、适合教学

代码规范：
- 只使用Manim标准库（from manim import *）
- 不使用任何外部文件操作或网络请求
- 类名必须是 AnimationScene
- 继承自 Scene 或其他Manim场景类
- 动画时长控制在10-20秒
- 使用 self.play() 和 self.wait() 控制动画节奏

输出格式：
只输出Python代码，不要包含任何解释说明。
代码必须用 ```python 和 ``` 包裹。

示例：
```python
from manim import *

class AnimationScene(Scene):
    def construct(self):
        # 创建坐标系
        axes = Axes(x_range=[-5, 5], y_range=[-5, 5])
        
        # 绘制函数
        graph = axes.plot(lambda x: 2*x + 1, color=BLUE)
        
        # 添加标签
        label = axes.get_graph_label(graph, "y=2x+1")
        
        # 动画展示
        self.play(Create(axes))
        self.play(Create(graph), Write(label))
        self.wait(2)
```
"""

# Animation templates for common scenarios
ANIMATION_TEMPLATES = {
    "linear_function": """
from manim import *

class AnimationScene(Scene):
    def construct(self):
        # 创建坐标系
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            axis_config={"color": GREY, "stroke_width": 2},
        )
        
        # 添加坐标轴标签
        labels = axes.get_axis_labels(x_label="x", y_label="y")
        
        # 绘制一次函数 y = kx + b
        k = {k}
        b = {b}
        graph = axes.plot(lambda x: k*x + b, color=BLUE, use_vectorized=True)
        
        # 添加函数标签
        if b >= 0:
            label_text = f"y = {k}x + {b}"
        else:
            label_text = f"y = {k}x - {abs(b)}"
        label = axes.get_graph_label(graph, label_text)
        
        # 动画展示
        self.play(Create(axes), Write(labels), run_time=1)
        self.play(Create(graph), Write(label), run_time=2)
        self.wait(2)
""",
    "coordinate_system": """
from manim import *

class AnimationScene(Scene):
    def construct(self):
        # 创建坐标系
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            axis_config={"include_numbers": True},
        )
        
        # 添加标签
        labels = axes.get_axis_labels(x_label="x", y_label="y")
        
        # 动画展示
        self.play(Create(axes), Write(labels))
        self.wait(2)
""",
    "point_on_graph": """
from manim import *

class AnimationScene(Scene):
    def construct(self):
        # 创建坐标系
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            axis_config={"color": GREY},
        )
        labels = axes.get_axis_labels(x_label="x", y_label="y")
        
        # 绘制函数
        graph = axes.plot(lambda x: {k}*x + {b}, color=BLUE)
        
        # 标注特定点
        x_val = {x}
        y_val = {k}*x_val + {b}
        point = axes.c2p(x_val, y_val)
        dot = Dot(point, color=RED)
        coord_label = MathTex(f"({x_val}, {y_val})").next_to(dot, UP)
        
        # 动画展示
        self.play(Create(axes), Write(labels))
        self.play(Create(graph))
        self.play(FadeIn(dot), Write(coord_label))
        self.wait(2)
""",
}


class AnimationGenerator:
    """Generate Manim animations using OpenSandbox.
    
    This class handles the complete workflow:
    1. Generate Manim code using LLM
    2. Execute code in OpenSandbox sandbox
    3. Retrieve generated video
    4. Store and return video URL
    
    Attributes:
        output_dir: Directory to store generated videos
        timeout: Maximum execution time in seconds
        use_cache: Whether to enable caching
    """
    
    def __init__(
        self,
        output_dir: str = "./generated_media",
        timeout: int = None,
        use_cache: bool = True,
    ):
        """Initialize animation generator.
        
        Args:
            output_dir: Directory to store generated videos
            timeout: Maximum execution time (defaults to config value)
            use_cache: Whether to enable caching
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout or settings.sandbox_timeout
        self.use_cache = use_cache
        
        logger.info(
            f"AnimationGenerator initialized: "
            f"output_dir={output_dir}, timeout={self.timeout}s"
        )
    
    async def generate_animation(
        self,
        animation_type: str,
        params: Dict[str, Any],
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate animation using OpenSandbox.
        
        This is the main entry point for animation generation.
        
        Args:
            animation_type: Type of animation (e.g., "linear_function")
            params: Animation parameters
            trace_id: Optional trace ID for logging
            
        Returns:
            {
                "video_url": "/media/xxx.mp4",
                "file_path": "/path/to/video.mp4",
                "duration": 15.0,
                "cached": False
            }
            
        Raises:
            RuntimeError: If OpenSandbox execution fails
            TimeoutError: If execution exceeds timeout
        """
        trace_id = trace_id or str(uuid.uuid4())
        logger.info(
            f"[{trace_id}] Starting animation generation: "
            f"type={animation_type}, params={params}"
        )
        
        # Check cache
        cache_key = self._build_cache_key(animation_type, params)
        if self.use_cache:
            cached_result = await self._check_cache(cache_key)
            if cached_result:
                logger.info(f"[{trace_id}] Using cached result")
                cached_result["cached"] = True
                return cached_result
        
        # Step 1: Generate Manim code
        manim_code = await self._generate_manim_code(
            animation_type, params, trace_id
        )
        
        # Step 2: Execute in OpenSandbox
        video_data = await self._execute_in_sandbox(
            manim_code, trace_id
        )
        
        # Step 3: Save video
        video_path = self.output_dir / f"{cache_key}.mp4"
        video_path.write_bytes(video_data)
        
        logger.info(f"[{trace_id}] Video saved: {video_path}")
        
        # Step 4: Return result
        result = {
            "video_url": f"/media/{cache_key}.mp4",
            "file_path": str(video_path),
            "duration": self._estimate_duration(manim_code),
            "cached": False,
        }
        
        return result
    
    async def _generate_manim_code(
        self,
        animation_type: str,
        params: Dict[str, Any],
        trace_id: str,
    ) -> str:
        """Generate Manim code using LLM.
        
        Args:
            animation_type: Type of animation
            params: Animation parameters
            trace_id: Trace ID for logging
            
        Returns:
            Manim Python code
        """
        logger.info(f"[{trace_id}] Generating Manim code")
        
        # Use template if available
        if animation_type in ANIMATION_TEMPLATES:
            template = ANIMATION_TEMPLATES[animation_type]
            try:
                manim_code = template.format(**params)
                logger.info(f"[{trace_id}] Using template for {animation_type}")
                return manim_code
            except KeyError as e:
                logger.warning(
                    f"[{trace_id}] Missing parameter for template: {e}, "
                    f"falling back to LLM generation"
                )
        
        # Generate using LLM
        prompt = self._build_manim_prompt(animation_type, params)
        
        response = llm_service.chat(
            system_prompt=MANIM_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
        
        # Extract code from response
        manim_code = self._extract_code_from_response(response)
        
        logger.info(
            f"[{trace_id}] Manim code generated, length={len(manim_code)}"
        )
        
        return manim_code
    
    def _build_manim_prompt(
        self,
        animation_type: str,
        params: Dict[str, Any],
    ) -> str:
        """Build prompt for LLM to generate Manim code.
        
        Args:
            animation_type: Type of animation
            params: Animation parameters
            
        Returns:
            Prompt string
        """
        prompt = f"""
请生成一个Manim动画场景，要求如下：

【动画类型】
{animation_type}

【参数】
{params}

【示例】
```python
from manim import *

class AnimationScene(Scene):
    def construct(self):
        # 你的代码...
        pass
```

【输出要求】
1. 只输出Python代码
2. 类名必须是 AnimationScene
3. 代码必须可以直接运行
4. 动画时长控制在10-20秒

请输出代码：
"""
        return prompt
    
    async def _execute_in_sandbox(
        self,
        manim_code: str,
        trace_id: str,
    ) -> bytes:
        """Execute Manim code in OpenSandbox.
        
        Args:
            manim_code: Manim Python code
            trace_id: Trace ID for logging
            
        Returns:
            Video file bytes
            
        Raises:
            RuntimeError: If execution fails
            TimeoutError: If execution times out
        """
        logger.info(f"[{trace_id}] Executing in OpenSandbox")
        
        try:
            # Import OpenSandbox (lazy import)
            from opensandbox import Sandbox
            from opensandbox.models import WriteEntry
            
            # Create sandbox
            sandbox = await Sandbox.create(
                settings.sandbox_image,
                env={
                    "MANIM_QUALITY": "medium_quality",
                    "PYTHON_VERSION": "3.11",
                },
                timeout=timedelta(seconds=self.timeout),
            )
            
            try:
                async with sandbox:
                    # Write Manim code to sandbox
                    await sandbox.files.write_files([
                        WriteEntry(
                            path="/workspace/animation.py",
                            data=manim_code,
                            mode=0o644,
                        )
                    ])
                    
                    logger.info(f"[{trace_id}] Code written to sandbox")
                    
                    # Execute Manim render
                    execution = await sandbox.commands.run(
                        "cd /workspace && "
                        "manim -qh --format mp4 animation.py AnimationScene",
                        timeout=timedelta(seconds=self.timeout - 10),
                    )
                    
                    if execution.exit_code != 0:
                        error_msg = (
                            execution.logs.stderr[0].text
                            if execution.logs.stderr
                            else "Unknown error"
                        )
                        logger.error(
                            f"[{trace_id}] Manim execution failed: {error_msg}"
                        )
                        raise RuntimeError(f"Manim execution failed: {error_msg}")
                    
                    logger.info(f"[{trace_id}] Manim rendering completed")
                    
                    # Find generated video file
                    video_files = await sandbox.files.list_dir(
                        "/workspace/media/videos/animation/1080p60"
                    )
                    mp4_files = [f for f in video_files if f.endswith(".mp4")]
                    
                    if not mp4_files:
                        raise FileNotFoundError("No video file generated")
                    
                    # Read video file
                    video_path = mp4_files[0]
                    video_data = await sandbox.files.read_file(video_path)
                    
                    logger.info(
                        f"[{trace_id}] Video retrieved, size={len(video_data)} bytes"
                    )
                    
                    return video_data
                    
            finally:
                # Cleanup sandbox
                await sandbox.kill()
                
        except asyncio.TimeoutError as e:
            logger.error(f"[{trace_id}] Sandbox execution timeout")
            raise TimeoutError(
                f"Animation generation timed out after {self.timeout}s"
            ) from e
            
        except Exception as e:
            logger.error(
                f"[{trace_id}] Sandbox execution error: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Failed to execute animation: {e}") from e
    
    def _build_cache_key(
        self,
        animation_type: str,
        params: Dict[str, Any],
    ) -> str:
        """Build cache key for animation.
        
        Args:
            animation_type: Type of animation
            params: Animation parameters
            
        Returns:
            Unique cache key
        """
        import hashlib
        import json
        
        params_str = json.dumps(params, sort_keys=True)
        hash_str = hashlib.md5(
            f"{animation_type}:{params_str}".encode()
        ).hexdigest()
        
        return f"{animation_type}_{hash_str}"
    
    async def _check_cache(
        self,
        cache_key: str,
    ) -> Optional[Dict[str, Any]]:
        """Check if animation exists in cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached result if exists, None otherwise
        """
        video_path = self.output_dir / f"{cache_key}.mp4"
        
        if video_path.exists():
            return {
                "video_url": f"/media/{cache_key}.mp4",
                "file_path": str(video_path),
                "duration": self._get_video_duration(video_path),
            }
        
        return None
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract code block from LLM response.
        
        Args:
            response: LLM response text
            
        Returns:
            Extracted Python code
        """
        # Try to find code block
        pattern = r"```python\n(.*?)\n```"
        match = re.search(pattern, response, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        # If no code block, return entire response
        return response.strip()
    
    def _estimate_duration(self, manim_code: str) -> float:
        """Estimate animation duration from code.
        
        Args:
            manim_code: Manim Python code
            
        Returns:
            Estimated duration in seconds
        """
        # Count self.wait() calls
        wait_pattern = r"self\.wait\((\d+(?:\.\d+)?)\)"
        wait_times = re.findall(wait_pattern, manim_code)
        wait_duration = sum(float(t) for t in wait_times)
        
        # Estimate play duration (rough heuristic)
        play_count = manim_code.count("self.play(")
        play_duration = play_count * 1.5  # Average 1.5s per play
        
        return wait_duration + play_duration
    
    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration using ffprobe.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds
        """
        try:
            import subprocess
            
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            return float(result.stdout.strip())
            
        except Exception as e:
            logger.warning(f"Failed to get video duration: {e}")
            return 15.0  # Default fallback


# Global instance
animation_generator = AnimationGenerator()
