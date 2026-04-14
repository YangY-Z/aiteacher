#!/usr/bin/env python3
"""
OpenSandbox集成快速测试脚本

这个脚本用于快速验证OpenSandbox集成是否成功。

使用方法：
    python test_animation_api.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.animation_generator import animation_generator


async def test_opensandbox_connection():
    """测试OpenSandbox连接"""
    print("=" * 60)
    print("测试1: 检查OpenSandbox连接")
    print("=" * 60)
    
    try:
        from opensandbox import Sandbox
        
        print("✓ OpenSandbox库导入成功")
        
        # 尝试创建一个简单的沙箱
        sandbox = await Sandbox.create("python:3.11-slim")
        print("✓ 沙箱创建成功")
        
        # 执行简单命令
        result = await sandbox.commands.run("echo 'Hello OpenSandbox!'")
        print(f"✓ 命令执行成功: {result.logs.stdout[0].text}")
        
        # 清理
        await sandbox.kill()
        print("✓ 沙箱清理成功")
        
        print("\n✅ OpenSandbox连接测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ OpenSandbox连接失败: {e}\n")
        print("请确保：")
        print("1. Docker Desktop已启动")
        print("2. OpenSandbox Server已启动 (opensandbox-server)")
        return False


async def test_animation_generation():
    """测试动画生成"""
    print("=" * 60)
    print("测试2: 生成一次函数动画")
    print("=" * 60)
    
    try:
        result = await animation_generator.generate_animation(
            animation_type="linear_function",
            params={"k": 2, "b": 1},
            trace_id="test-001"
        )
        
        print(f"✓ 动画生成成功")
        print(f"  视频URL: {result['video_url']}")
        print(f"  文件路径: {result['file_path']}")
        print(f"  时长: {result['duration']}秒")
        print(f"  是否缓存: {result['cached']}")
        
        # 检查文件是否存在
        video_path = Path(result['file_path'])
        if video_path.exists():
            file_size = video_path.stat().st_size
            print(f"  文件大小: {file_size / 1024:.2f} KB")
        
        print("\n✅ 动画生成测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 动画生成失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_template_rendering():
    """测试模板渲染"""
    print("=" * 60)
    print("测试3: 测试模板渲染")
    print("=" * 60)
    
    try:
        from app.services.animation_generator import ANIMATION_TEMPLATES
        
        template = ANIMATION_TEMPLATES["linear_function"]
        code = template.format(k=3, b=-2)
        
        print("✓ 模板渲染成功")
        print("\n生成的代码预览（前10行）:")
        print("-" * 60)
        for i, line in enumerate(code.split('\n')[:10], 1):
            print(f"{i:2d}: {line}")
        print("-" * 60)
        
        print("\n✅ 模板渲染测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 模板渲染失败: {e}\n")
        return False


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🚀 OpenSandbox集成测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 测试1: OpenSandbox连接
    results.append(await test_opensandbox_connection())
    
    # 测试2: 模板渲染（不需要OpenSandbox）
    results.append(await test_template_rendering())
    
    # 测试3: 动画生成（需要OpenSandbox）
    if results[0]:  # 只有连接成功才测试
        results.append(await test_animation_generation())
    else:
        print("跳过动画生成测试（OpenSandbox未连接）")
        results.append(False)
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    total = len(results)
    passed = sum(results)
    
    print(f"\n总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    
    if all(results):
        print("\n✅ 所有测试通过！OpenSandbox集成成功！")
        print("\n下一步:")
        print("1. 启动应用: uvicorn app.main:app --reload")
        print("2. 访问API文档: http://localhost:8000/docs")
        print("3. 测试API端点: POST /api/v1/animations/generate")
    else:
        print("\n❌ 部分测试失败，请检查:")
        print("1. Docker Desktop是否运行")
        print("2. OpenSandbox Server是否启动")
        print("3. 查看错误日志")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
