# OpenSandbox 集成指南

> **版本**: v1.0  
> **日期**: 2026年4月13日  
> **状态**: 已完成集成

---

## 📋 集成概览

### 已完成的工作

✅ **核心服务**
- `animation_generator.py` - OpenSandbox动画生成服务
- `animation.py` - API端点
- 配置文件更新

✅ **工具和脚本**
- `start_opensandbox.sh` - OpenSandbox启动脚本
- `test_animation_generator.py` - 单元测试
- `.env.example` - 环境变量示例

✅ **文档**
- API文档自动生成
- 集成指南

---

## 🚀 快速开始

### 第一步：安装依赖

```bash
cd /Users/zhaoyang/iFlow/aiteacher-2/ai-teacher-backend

# 安装Python依赖
pip install -r requirements.txt
```

### 第二步：启动OpenSandbox服务

```bash
# 方式1：使用启动脚本（推荐）
bash scripts/start_opensandbox.sh

# 方式2：手动启动
# 1. 启动Docker Desktop（如果还没启动）
open -a Docker

# 2. 安装OpenSandbox（如果还没安装）
pip install opensandbox-server opensandbox

# 3. 初始化配置
opensandbox-server init-config ~/.sandbox.toml --example docker

# 4. 启动服务
opensandbox-server
```

### 第三步：配置环境变量

```bash
# 复制环境变量示例
cp .env.example .env

# 编辑.env文件
# 确保包含以下配置：
OPENSANDBOX_SERVER_URL=http://localhost:8080
OPENSANDBOX_API_KEY=
SANDBOX_IMAGE=opensandbox/code-interpreter:latest
SANDBOX_TIMEOUT=60
```

### 第四步：启动应用

```bash
# 启动FastAPI应用
uvicorn app.main:app --reload

# 或者使用Python
python -m uvicorn app.main:app --reload
```

### 第五步：测试API

```bash
# 1. 检查服务健康
curl http://localhost:8000/health

# 2. 检查OpenSandbox连接
curl http://localhost:8000/api/v1/animations/health

# 3. 获取支持的动画类型
curl http://localhost:8000/api/v1/animations/types

# 4. 生成动画
curl -X POST http://localhost:8000/api/v1/animations/generate \
  -H "Content-Type: application/json" \
  -d '{
    "animation_type": "linear_function",
    "params": {"k": 2, "b": 1}
  }'
```

---

## 📚 API文档

### 1. 生成动画

**POST** `/api/v1/animations/generate`

**请求体：**
```json
{
  "animation_type": "linear_function",
  "params": {
    "k": 2,
    "b": 1
  },
  "use_cache": true
}
```

**响应：**
```json
{
  "video_url": "/media/linear_function_abc123.mp4",
  "file_path": "/path/to/video.mp4",
  "duration": 15.0,
  "cached": false
}
```

### 2. 获取动画类型

**GET** `/api/v1/animations/types`

**响应：**
```json
{
  "types": [
    {
      "name": "linear_function",
      "description": "一次函数图像",
      "params": {
        "k": "斜率",
        "b": "截距"
      }
    }
  ]
}
```

### 3. 健康检查

**GET** `/api/v1/animations/health`

**响应：**
```json
{
  "status": "healthy",
  "opensandbox": "connected"
}
```

---

## 🎯 使用示例

### 示例1：生成一次函数动画

```python
import httpx
import asyncio

async def generate_linear_function():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/animations/generate",
            json={
                "animation_type": "linear_function",
                "params": {"k": 2, "b": 1}
            }
        )
        
        result = response.json()
        print(f"视频URL: {result['video_url']}")
        print(f"时长: {result['duration']}秒")

asyncio.run(generate_linear_function())
```

### 示例2：直接使用AnimationGenerator

```python
from app.services.animation_generator import animation_generator
import asyncio

async def main():
    result = await animation_generator.generate_animation(
        animation_type="linear_function",
        params={"k": 3, "b": -2},
        trace_id="test-001"
    )
    
    print(f"视频已生成: {result['video_url']}")

asyncio.run(main())
```

---

## 🧪 测试

### 运行单元测试

```bash
# 运行所有测试
pytest tests/test_animation_generator.py -v

# 运行特定测试
pytest tests/test_animation_generator.py::test_manim_code_template -v

# 运行集成测试（需要OpenSandbox运行）
pytest tests/test_animation_generator.py::test_openSandbox_connection -v
```

### 测试覆盖范围

- ✅ 代码生成测试
- ✅ 模板格式化测试
- ✅ 代码提取测试
- ✅ 时长估算测试
- ✅ 缓存键生成测试
- ✅ OpenSandbox连接测试

---

## 🔧 故障排查

### 问题1：OpenSandbox连接失败

**症状：**
```
RuntimeError: Failed to connect to OpenSandbox server
```

**解决方案：**
```bash
# 1. 检查OpenSandbox Server是否运行
lsof -i:8080

# 2. 检查日志
opensandbox-server --log-level debug

# 3. 重启服务
pkill -f opensandbox-server
opensandbox-server
```

### 问题2：Docker未运行

**症状：**
```
Error: Cannot connect to Docker daemon
```

**解决方案：**
```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker

# 等待Docker完全启动
sleep 10
docker info
```

### 问题3：动画生成超时

**症状：**
```
TimeoutError: Animation generation timed out after 60s
```

**解决方案：**
```bash
# 增加超时时间
# .env
SANDBOX_TIMEOUT=120

# 或在代码中设置
generator = AnimationGenerator(timeout=120)
```

### 问题4：视频文件未找到

**症状：**
```
FileNotFoundError: No video file generated
```

**解决方案：**
```bash
# 检查Manim是否正确安装
docker run --rm opensandbox/code-interpreter:latest \
  python -c "from manim import *; print('Manim OK')"

# 检查沙箱日志
# 在animation_generator.py中添加更多日志
```

---

## 📊 性能优化

### 1. 启用缓存

```python
# 默认已启用，如需禁用：
result = await animation_generator.generate_animation(
    animation_type="linear_function",
    params={"k": 2, "b": 1},
    use_cache=False  # 禁用缓存
)
```

### 2. 调整资源限制

```env
# .env
SANDBOX_MAX_MEMORY_MB=1024  # 增加内存限制
SANDBOX_MAX_CPUS=2.0        # 增加CPU限制
```

### 3. 并发生成

```python
import asyncio

async def generate_multiple():
    tasks = [
        animation_generator.generate_animation(
            "linear_function", {"k": k, "b": 0}
        )
        for k in range(1, 4)
    ]
    
    results = await asyncio.gather(*tasks)
    return results
```

---

## 🔐 安全配置

### 生产环境安全建议

```toml
# ~/.sandbox.toml

[server]
host = "0.0.0.0"
port = 8080
api_key = "your-strong-secret-key-here"  # ⚠️ 必须设置

[security]
network_disabled = true  # 禁用网络
read_only_rootfs = true  # 只读文件系统
```

```env
# .env (生产环境)
OPENSANDBOX_API_KEY=your-strong-secret-key-here
SANDBOX_TIMEOUT=60
SANDBOX_MAX_MEMORY_MB=512
SANDBOX_MAX_CPUS=1.0
```

---

## 📈 监控和日志

### 查看日志

```bash
# OpenSandbox Server日志
# 默认输出到标准输出

# 应用日志
tail -f logs/app.log

# 过滤动画相关日志
tail -f logs/app.log | grep "AnimationGenerator"
```

### 监控指标

```python
# 在代码中添加监控
import logging

logger.info(
    "Animation generated",
    extra={
        "animation_type": "linear_function",
        "duration": 15.0,
        "cached": False,
        "file_size": 1024000,
    }
)
```

---

## 🎓 进阶使用

### 自定义动画模板

```python
# 在animation_generator.py中添加新模板

ANIMATION_TEMPLATES["quadratic_function"] = """
from manim import *

class AnimationScene(Scene):
    def construct(self):
        # 二次函数动画
        axes = Axes(x_range=[-3, 3], y_range=[-5, 5])
        graph = axes.plot(lambda x: {a}*x**2 + {b}*x + {c})
        self.play(Create(graph))
"""
```

### 集成到教学流程

```python
# 在teaching_flow.py中使用

from app.services.animation_generator import animation_generator

async def enhance_teaching_with_animation(kp_info):
    if kp_info["type"] == "函数图像":
        result = await animation_generator.generate_animation(
            animation_type="linear_function",
            params=kp_info["params"]
        )
        
        # 将视频URL添加到教学内容
        return {
            "video_url": result["video_url"],
            "duration": result["duration"]
        }
```

---

## ✅ 检查清单

部署前检查：

- [ ] Docker Desktop运行正常
- [ ] OpenSandbox Server启动成功
- [ ] 环境变量配置正确
- [ ] API健康检查通过
- [ ] 测试动画生成成功
- [ ] 视频文件可访问
- [ ] 日志记录正常

---

## 📞 获取帮助

### 相关文档

- [OpenSandbox官方文档](https://open-sandbox.ai/zh/)
- [Manim文档](https://docs.manim.community/)
- [项目API文档](http://localhost:8000/docs)

### 问题反馈

如遇到问题，请检查：
1. 日志输出
2. OpenSandbox Server状态
3. Docker运行状态
4. 网络连接

---

**集成完成！🎉**

下一步：
1. 启动OpenSandbox服务
2. 运行测试验证
3. 开始使用API生成动画
