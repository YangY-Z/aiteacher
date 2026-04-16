"""Tests for AnimationGenerator."""

import pytest
from app.services.tools.animation_generator import AnimationGenerator, ANIMATION_TEMPLATES


@pytest.mark.asyncio
async def test_generate_animation_linear_function():
    """Test generating a linear function animation."""
    
    generator = AnimationGenerator(
        output_dir="./test_media",
        use_cache=False,
    )
    
    result = await generator.generate_animation(
        animation_type="linear_function",
        params={"k": 2, "b": 1},
    )
    
    assert "video_url" in result
    assert "file_path" in result
    assert "duration" in result
    assert result["cached"] == False


def test_manim_code_template():
    """Test Manim code template formatting."""
    
    template = ANIMATION_TEMPLATES["linear_function"]
    code = template.format(k=2, b=1)
    
    assert "class AnimationScene" in code
    assert "k = 2" in code
    assert "b = 1" in code
    assert "from manim import *" in code


def test_extract_code_from_response():
    """Test extracting code from LLM response."""
    
    generator = AnimationGenerator()
    
    response = """
Here's the Manim code for your animation:

```python
from manim import *

class AnimationScene(Scene):
    def construct(self):
        text = Text("Hello!")
        self.play(Write(text))
```

Hope this helps!
"""
    
    code = generator._extract_code_from_response(response)
    
    assert "from manim import *" in code
    assert "class AnimationScene" in code
    assert "```" not in code


def test_estimate_duration():
    """Test estimating animation duration."""
    
    generator = AnimationGenerator()
    
    code = """
from manim import *

class AnimationScene(Scene):
    def construct(self):
        self.play(Create(axes))
        self.wait(2)
        self.play(Create(graph))
        self.wait(3)
"""
    
    duration = generator._estimate_duration(code)
    
    # 2 waits (2s + 3s) + 2 plays (1.5s each)
    assert duration == pytest.approx(8.0, rel=0.1)


def test_build_cache_key():
    """Test cache key generation."""
    
    generator = AnimationGenerator()
    
    key1 = generator._build_cache_key("linear_function", {"k": 2, "b": 1})
    key2 = generator._build_cache_key("linear_function", {"k": 2, "b": 1})
    key3 = generator._build_cache_key("linear_function", {"k": 3, "b": 1})
    
    # Same params should produce same key
    assert key1 == key2
    
    # Different params should produce different key
    assert key1 != key3
    
    # Key should start with animation type
    assert key1.startswith("linear_function_")


@pytest.mark.asyncio
async def test_openSandbox_connection():
    """Test OpenSandbox server connection.
    
    This test requires OpenSandbox server to be running.
    """
    
    try:
        from opensandbox import Sandbox
        
        # Try to create a minimal sandbox
        sandbox = await Sandbox.create("python:3.11-slim")
        
        # Execute a simple command
        result = await sandbox.commands.run("echo 'Hello OpenSandbox!'")
        
        assert result.exit_code == 0
        assert "Hello OpenSandbox!" in result.logs.stdout[0].text
        
        # Cleanup
        await sandbox.kill()
        
    except Exception as e:
        pytest.skip(f"OpenSandbox server not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
