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
from app.services.tools.protocols import AnimationGeneratorProtocol

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
            axis_config={{"color": GREY, "stroke_width": 2}},
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
            label_text = f"y = {k}x - {{abs(b)}}"
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
            axis_config={{"include_numbers": True}},
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
            axis_config={{"color": GREY}},
        )
        labels = axes.get_axis_labels(x_label="x", y_label="y")
        
        # 绘制函数
        graph = axes.plot(lambda x: {k}*x + {b}, color=BLUE)
        
        # 标注特定点
        x_val = {x}
        y_val = {k}*x_val + {b}
        point = axes.c2p(x_val, y_val)
        dot = Dot(point, color=RED)
        coord_label = MathTex(f"({{x_val}}, {{y_val}})").next_to(dot, UP)
        
        # 动画展示
        self.play(Create(axes), Write(labels))
        self.play(Create(graph))
        self.play(FadeIn(dot), Write(coord_label))
        self.wait(2)
""",
}


class AnimationGenerator(AnimationGeneratorProtocol):
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
        output_format: str = "image",
    ) -> Dict[str, Any]:
        """Generate animation using OpenSandbox.
        
        This is the main entry point for animation generation.
        
        Args:
            animation_type: Type of animation (e.g., "linear_function", "auto")
            params: Animation parameters
            trace_id: Optional trace ID for logging
            output_format: Output format - "video" or "image"
            
        Returns:
            {
                "video_url": "/media/xxx.mp4",  # or "image_url" for image
                "file_path": "/path/to/video.mp4",
                "duration": 15.0,  # only for video
                "cached": False,
                "type": "video" or "image"
            }
            
        Raises:
            RuntimeError: If OpenSandbox execution fails
            TimeoutError: If execution exceeds timeout
        """
        trace_id = trace_id or str(uuid.uuid4())
        logger.info(
            f"[{trace_id}] Starting animation generation: "
            f"type={animation_type}, output_format={output_format}"
        )
        
        # Check cache
        cache_key = self._build_cache_key(animation_type, params, output_format)
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
        media_data = await self._execute_in_sandbox(
            manim_code, trace_id, output_format
        )
        
        # Step 3: Save media file
        file_extension = "mp4" if output_format == "video" else "png"
        media_path = self.output_dir / f"{cache_key}.{file_extension}"
        media_path.write_bytes(media_data)
        
        logger.info(f"[{trace_id}] Media saved: {media_path}")
        
        # Step 4: Return result
        if output_format == "video":
            result = {
                "video_url": f"/media/{cache_key}.mp4",
                "file_path": str(media_path),
                "duration": self._estimate_duration(manim_code),
                "cached": False,
                "type": "video",
                "concept": params.get("concept", ""),
                "cache_key": cache_key,
            }
        else:
            result = {
                "image_url": f"/media/{cache_key}.png",
                "file_path": str(media_path),
                "cached": False,
                "type": "image",
                "concept": params.get("concept", ""),
                "cache_key": cache_key,
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
            animation_type: Type of animation (or "auto" for LLM to decide)
            params: Animation parameters
            trace_id: Trace ID for logging
            
        Returns:
            Manim Python code
        """
        logger.info(f"[{trace_id}] Generating Manim code for type: {animation_type}")
        
        # Use template if available and not "auto"
        if animation_type != "auto" and animation_type in ANIMATION_TEMPLATES:
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
        
        # Generate using LLM (for "auto" or missing template)
        prompt = self._build_manim_prompt(animation_type, params)

        response = await asyncio.to_thread(
            llm_service.chat,
            system_prompt=MANIM_SYSTEM_PROMPT,
            user_message=prompt,
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
            animation_type: Type of animation (or "auto")
            params: Animation parameters
            
        Returns:
            Prompt string
        """
        concept = params.get("concept", "")
        
        if animation_type == "auto":
            # Auto mode: let LLM decide what to generate
            prompt = f"""
请生成一个Manim动画场景，要求如下：

【概念描述】
{concept}

【参数】
{params}

【要求】
1. 根据概念描述，自主决定最适合的动画类型
2. 可以绘制：函数图像、几何图形、数学证明、公式推导、数据可视化等
3. 只输出Python代码，不要包含任何解释说明
4. 类名必须是 AnimationScene
5. 继承自 Scene 或其他Manim场景类
6. 代码必须可以直接运行
7. 动画时长控制在10-20秒（视频输出时）或静态展示（图片输出时）

【示例】
```python
from manim import *

class AnimationScene(Scene):
    def construct(self):
        # 你的代码...
        pass
```

请输出代码：
"""
        else:
            # Specified type
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
        output_format: str = "video",
    ) -> bytes:
        """Execute Manim code in OpenSandbox.
        
        Args:
            manim_code: Manim Python code
            trace_id: Trace ID for logging
            output_format: Output format - "video" or "image"
            
        Returns:
            Video or image file bytes
            
        Raises:
            RuntimeError: If execution fails
            TimeoutError: If execution times out
        """
        logger.info(f"[{trace_id}] Executing in OpenSandbox, output_format={output_format}")
        
        try:
            # Import OpenSandbox (lazy import)
            from opensandbox import Sandbox
            from opensandbox.models import WriteEntry, SearchEntry
            from opensandbox.models.execd import RunCommandOpts

            # Create sandbox
            sandbox = await Sandbox.create(
                settings.sandbox_image,
                env={
                    "MANIM_QUALITY": "medium_quality",
                },
                timeout=timedelta(seconds=self.timeout),
            )

            # Manim CLI path in the custom image
            MANIM_BIN = "/opt/python/versions/cpython-3.12.12-linux-aarch64-gnu/bin/manim"

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
                    
                    if output_format == "video":
                        manim_cmd = f"cd /workspace && {MANIM_BIN} -qm --format mp4 animation.py AnimationScene"
                    else:
                        manim_cmd = f"cd /workspace && {MANIM_BIN} -qm -s animation.py AnimationScene"

                    # Execute Manim render
                    execution = await sandbox.commands.run(
                        manim_cmd,
                        opts=RunCommandOpts(
                            timeout=timedelta(seconds=self.timeout - 10),
                        ),
                    )
                    
                    if execution.exit_code != 0:
                        stderr_text = "\n".join(
                            log.text for log in execution.logs.stderr
                        ) if execution.logs.stderr else ""
                        stdout_text = "\n".join(
                            log.text for log in execution.logs.stdout
                        ) if execution.logs.stdout else ""
                        error_msg = stderr_text or stdout_text or "Unknown error"
                        logger.error(
                            f"[{trace_id}] Manim execution failed:\n{error_msg}"
                        )
                        raise RuntimeError(f"Manim execution failed: {error_msg[-2000:]}")
                    
                    logger.info(f"[{trace_id}] Manim rendering completed")
                    
                    # Find generated media file
                    if output_format == "video":
                        # Search for mp4 files under media/videos (quality dir varies)
                        find_result = await sandbox.commands.run(
                            "find /workspace/media/videos -name '*.mp4' -type f 2>/dev/null",
                        )
                        if find_result.exit_code == 0 and find_result.logs.stdout:
                            mp4_files = [
                                line.strip()
                                for line in find_result.logs.stdout[0].text.strip().split('\n')
                                if line.strip()
                            ]
                        else:
                            mp4_files = []

                        if not mp4_files:
                            raise FileNotFoundError("No video file generated")

                        # Read video file as bytes
                        media_path = mp4_files[0]
                        media_data = await sandbox.files.read_bytes(media_path)

                        logger.info(
                            f"[{trace_id}] Video retrieved, size={len(media_data)} bytes"
                        )
                    else:
                        # Find image files via search
                        image_entries = await sandbox.files.search(
                            SearchEntry(path="/workspace/media/images/animation", pattern="*.png")
                        )
                        png_files = [e.path for e in image_entries]

                        if not png_files:
                            raise FileNotFoundError("No image file generated")

                        # Read image file as bytes
                        media_path = png_files[0]
                        media_data = await sandbox.files.read_bytes(media_path)

                        logger.info(
                            f"[{trace_id}] Image retrieved, size={len(media_data)} bytes"
                        )
                    
                    return media_data
                    
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
        output_format: str = "video",
    ) -> str:
        """Build cache key for animation.
        
        Args:
            animation_type: Type of animation
            params: Animation parameters
            output_format: Output format - "video" or "image"
            
        Returns:
            Unique cache key
        """
        import hashlib
        import json
        
        # Use concept as part of cache key for meaningful file names
        concept = params.get("concept", "")
        if concept:
            # Normalize concept for filename: remove special chars, truncate
            safe_concept = re.sub(r'[^\w\u4e00-\u9fff]', '_', concept)[:30]
            params_str = json.dumps(params, sort_keys=True)
            hash_str = hashlib.md5(
                f"{animation_type}:{output_format}:{params_str}".encode()
            ).hexdigest()[:8]
            return f"{safe_concept}_{output_format}_{hash_str}"
        
        params_str = json.dumps(params, sort_keys=True)
        hash_str = hashlib.md5(
            f"{animation_type}:{output_format}:{params_str}".encode()
        ).hexdigest()
        
        return f"{animation_type}_{output_format}_{hash_str}"
    
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
        # Try video cache
        video_path = self.output_dir / f"{cache_key}.mp4"
        if video_path.exists():
            return {
                "video_url": f"/media/{cache_key}.mp4",
                "file_path": str(video_path),
                "duration": self._get_video_duration(video_path),
                "type": "video",
                "cached": True,
                "cache_key": cache_key,
            }
        
        # Try image cache
        image_path = self.output_dir / f"{cache_key}.png"
        if image_path.exists():
            return {
                "image_url": f"/media/{cache_key}.png",
                "file_path": str(image_path),
                "type": "image",
                "cached": True,
                "cache_key": cache_key,
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
