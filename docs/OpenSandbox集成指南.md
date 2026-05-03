# OpenSandbox 集成指南

> **版本**: v2.0  
> **日期**: 2026年5月3日  
> **状态**: 已完成集成（含自定义镜像）

---

## 目录

1. [集成概览](#-集成概览)
2. [自定义镜像构建](#-自定义镜像构建)
3. [镜像分享与仓库](#-镜像分享与仓库)
4. [生产环境部署](#-生产环境部署)
5. [快速开始（开发环境）](#-快速开始开发环境)
6. [API文档](#-api文档)
7. [使用示例](#-使用示例)
8. [测试](#-测试)
9. [故障排查](#-故障排查)
10. [性能优化](#-性能优化)

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

## 🐳 自定义镜像构建

OpenSandbox 官方镜像 `code-interpreter` 不包含 Manim 及其依赖。由于沙箱容器默认有网络出口限制（egress = dns），无法在运行时安装依赖，因此需要构建预装依赖的自定义镜像。

### 为什么需要自定义镜像？

| 方案 | 是否可行 | 原因 |
|------|----------|------|
| 官方镜像 + 运行时 pip install | ❌ | 沙箱容器无网络出口，pip install 超时 |
| 自定义镜像预装依赖 | ✅ | 所有依赖打包进镜像，无需网络 |

### 依赖清单

自定义镜像在官方镜像基础上新增以下依赖：

| 类别 | 包 | 用途 |
|------|---|------|
| 构建工具 | `build-essential`, `pkg-config` | C 扩展编译 |
| 渲染引擎 | `libcairo2-dev`, `libpango1.0-dev`, `libglib2.0-dev` | Manim 画面渲染核心 |
| 图片格式 | `libjpeg-dev`, `libgif-dev` | 图片编解码 |
| OpenGL | `libgl1-mesa-dev` | GPU 渲染 |
| 视频处理 | `ffmpeg` | MP4 导出 |
| LaTeX 基础 | `texlive-latex-base`, `texlive-latex-extra`, `texlive-latex-recommended` | 数学公式排版 |
| LaTeX 字体 | `texlive-fonts-recommended`, `texlive-fonts-extra` | 额外字体 |
| LaTeX 科学 | `texlive-science`, `texlive-publishers` | 科学/数学宏包 |
| 中文字体 | `texlive-lang-chinese` | 教学场景中文显示 |
| TikZ/pgfplots | `texlive-pictures` | 几何图形、图表 |
| 转换工具 | `dvipng`, `dvisvgm`, `ghostscript`, `poppler-utils`, `inkscape` | DVI/SVG/PDF 处理 |
| Python 包 | `manim` | 动画引擎 |

### Dockerfile

```dockerfile
# /tmp/manim-sandbox/Dockerfile
FROM sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:v1.0.2

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config \
    libcairo2-dev libpango1.0-dev libglib2.0-dev \
    libjpeg-dev libgif-dev \
    libgl1-mesa-dev \
    ffmpeg \
    texlive-latex-base texlive-latex-extra texlive-latex-recommended \
    texlive-fonts-recommended texlive-fonts-extra \
    texlive-science texlive-publishers \
    texlive-lang-chinese \
    texlive-pictures \
    dvipng dvisvgm ghostscript poppler-utils inkscape \
    && rm -rf /var/lib/apt/lists/*

# 安装 manim（使用镜像内自带的 Python）
RUN /opt/python/versions/cpython-3.12.12-linux-aarch64-gnu/bin/python3 -m pip install \
    --break-system-packages \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    manim
```

> **注意**: `--break-system-packages` 是因为 Ubuntu 24.04 的 PEP 668 限制。`-i` 指定阿里云 pip 镜像加速下载。

### 构建步骤

```bash
# 1. 创建构建目录
mkdir -p /tmp/manim-sandbox && cd /tmp/manim-sandbox

# 2. 将上面的 Dockerfile 保存到该目录

# 3. 构建镜像（首次约 3-5 分钟，texlive 包较大）
docker build -t opensandbox/code-interpreter-manim:v1.0.2 .

# 4. 验证镜像
docker run --rm opensandbox/code-interpreter-manim:v1.0.2 \
  /opt/python/versions/cpython-3.12.12-linux-aarch64-gnu/bin/manim --version
```

### 镜像大小

- 基础镜像 `code-interpreter:v1.0.2`: ~800MB
- 新增依赖后: ~3-4GB（主要是 texlive）

---

## 📤 镜像分享与仓库

构建好的镜像需要推送到镜像仓库，供其他开发者和生产服务器使用。

### 方式一：推送到阿里云 ACR（推荐）

阿里云 ACR 已有官方 OpenSandbox 镜像，国内访问速度快。

```bash
# 1. 登录阿里云 ACR（需要先在阿里云控制台创建命名空间）
docker login --username=你的阿里云账号 registry.cn-zhangjiakou.cr.aliyuncs.com

# 2. 给镜像打 tag（替换 <namespace> 为你的命名空间）
docker tag opensandbox/code-interpreter-manim:v1.0.2 \
  registry.cn-zhangjiakou.cr.aliyuncs.com/<namespace>/code-interpreter-manim:v1.0.2

# 3. 推送
docker push registry.cn-zhangjiakou.cr.aliyuncs.com/<namespace>/code-interpreter-manim:v1.0.2

# 4. 其他机器拉取
docker pull registry.cn-zhangjiakou.cr.aliyuncs.com/<namespace>/code-interpreter-manim:v1.0.2
```

### 方式二：推送到 Docker Hub

```bash
# 1. 登录 Docker Hub
docker login

# 2. 打 tag 并推送
docker tag opensandbox/code-interpreter-manim:v1.0.2 <username>/code-interpreter-manim:v1.0.2
docker push <username>/code-interpreter-manim:v1.0.2
```

### 方式三：导出为文件（离线传输）

适用于无法联网的服务器或安全要求高的内网环境。

```bash
# 导出（压缩后约 1-2GB）
docker save opensandbox/code-interpreter-manim:v1.0.2 | gzip > manim-sandbox.tar.gz

# 目标机器导入
docker load < manim-sandbox.tar.gz

# 验证
docker images | grep manim
```

### 方式对比

| 方式 | 适用场景 | 传输速度 | 需要联网 |
|------|----------|----------|----------|
| 阿里云 ACR | 国内服务器、团队协作 | 快 | 是 |
| Docker Hub | 开源项目、国际协作 | 国内较慢 | 是 |
| 文件导出 | 离线环境、内网部署 | 取决于介质 | 否 |

---

## 🚢 生产环境部署

### 架构图

```
┌─────────────────────────────────────────┐
│              生产服务器                   │
│                                         │
│  ┌──────────────┐   ┌────────────────┐  │
│  │  FastAPI App  │───│  OpenSandbox   │  │
│  │  (uvicorn)   │   │  Server :8080  │  │
│  └──────────────┘   └───────┬────────┘  │
│                              │           │
│                      ┌───────▼────────┐  │
│                      │  Docker Engine │  │
│                      └───────┬────────┘  │
│                              │           │
│                     从镜像仓库拉取:       │
│                     ACR / Docker Hub     │
└─────────────────────────────────────────┘
```

### 前置要求

- Docker Engine 20.10+
- Python 3.11+（后端运行）
- 服务器至少 8GB 内存、20GB 磁盘空间（texlive 较大）
- 网络可访问镜像仓库

### 部署步骤

#### Step 1: 拉取自定义镜像

```bash
# 方式 A：从阿里云 ACR 拉取
docker pull registry.cn-zhangjiakou.cr.aliyuncs.com/<namespace>/code-interpreter-manim:v1.0.2

# 方式 B：从文件导入
docker load < manim-sandbox.tar.gz

# 验证镜像存在
docker images | grep manim
```

#### Step 2: 配置 OpenSandbox Server

```bash
# 初始化配置（如果尚未初始化）
opensandbox-server init-config ~/.sandbox.toml --example docker
```

编辑 `~/.sandbox.toml`：

```toml
[server]
host = "0.0.0.0"
port = 8080
api_key = "your-production-api-key"  # 生产环境必须设置

[sandbox]
image = "registry.cn-zhangjiakou.cr.aliyuncs.com/<namespace>/code-interpreter-manim:v1.0.2"
timeout = 600

[security]
network_disabled = true  # 禁用容器网络
```

#### Step 3: 配置后端 .env

```bash
# ai-teacher-backend/.env
OPENSANDBOX_SERVER_URL=http://localhost:8080
OPENSANDBOX_API_KEY=your-production-api-key
SANDBOX_IMAGE=registry.cn-zhangjiakou.cr.aliyuncs.com/<namespace>/code-interpreter-manim:v1.0.2
SANDBOX_TIMEOUT=600
SANDBOX_MAX_MEMORY_MB=512
SANDBOX_MAX_CPUS=1.0
```

#### Step 4: 启动服务

```bash
# 1. 确保 Docker 运行
sudo systemctl start docker
sudo systemctl enable docker

# 2. 启动 OpenSandbox Server（后台运行）
OPENSANDBOX_INSECURE_SERVER=NO opensandbox-server > /var/log/opensandbox.log 2>&1 &

# 3. 等待就绪
sleep 5
curl http://localhost:8080/health
# 期望输出: {"status":"healthy"}

# 4. 启动后端
cd ai-teacher-backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Step 5: 验证部署

```bash
# 1. 健康检查
curl http://localhost:8000/health

# 2. 测试动画生成
curl -X POST http://localhost:8000/api/v1/animations/generate \
  -H "Content-Type: application/json" \
  -d '{
    "animation_type": "linear_function",
    "params": {"k": 2, "b": 1},
    "output_format": "image"
  }'

# 3. 检查生成的文件
ls -la generated_media/
```

### 使用 systemd 管理（推荐生产环境）

创建 OpenSandbox Server 的 systemd 服务文件：

```ini
# /etc/systemd/system/opensandbox.service
[Unit]
Description=OpenSandbox Server
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=root
Environment=OPENSANDBOX_INSECURE_SERVER=NO
ExecStart=/usr/local/bin/opensandbox-server
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable opensandbox
sudo systemctl start opensandbox
sudo systemctl status opensandbox
```

### 使用 Docker Compose（可选）

如果希望将 OpenSandbox Server 本身也容器化：

```yaml
# docker-compose.yml
version: "3.8"

services:
  opensandbox-server:
    image: opensandbox-server:latest
    ports:
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - OPENSANDBOX_INSECURE_SERVER=YES
    depends_on:
      - docker

  ai-teacher-backend:
    build: ./ai-teacher-backend
    ports:
      - "8000:8000"
    environment:
      - OPENSANDBOX_SERVER_URL=http://opensandbox-server:8080
      - SANDBOX_IMAGE=registry.cn-zhangjiakou.cr.aliyuncs.com/<namespace>/code-interpreter-manim:v1.0.2
    depends_on:
      - opensandbox-server
```

### 更新镜像流程

当需要更新自定义镜像时：

```bash
# 1. 重新构建（在开发机上）
cd /tmp/manim-sandbox
docker build -t opensandbox/code-interpreter-manim:v1.0.3 .

# 2. 推送到仓库
docker push registry.cn-zhangjiakou.cr.aliyuncs.com/<namespace>/code-interpreter-manim:v1.0.3

# 3. 在生产服务器上拉取新镜像
docker pull registry.cn-zhangjiakou.cr.aliyuncs.com/<namespace>/code-interpreter-manim:v1.0.3

# 4. 更新 .env 和 sandbox.toml 中的镜像版本

# 5. 重启服务
sudo systemctl restart opensandbox
# 重启后端会自动使用新镜像
```

### 部署检查清单

- [ ] Docker Engine 已安装并运行
- [ ] 自定义镜像已拉取/导入
- [ ] `~/.sandbox.toml` 已配置（api_key、image）
- [ ] `.env` 已配置（SANDBOX_IMAGE 指向自定义镜像）
- [ ] OpenSandbox Server 健康检查通过 (`/health`)
- [ ] 后端健康检查通过
- [ ] 动画生成测试通过
- [ ] 生产安全配置（api_key 已设置、network_disabled=true）
- [ ] systemd 服务已配置（可选但推荐）

---

## 🚀 快速开始（开发环境）

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
curl http://localhost:8008/api/v1/animations/types

# 4. 生成动画
curl -X POST http://localhost:8008/api/v1/animations/generate \
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
from app.services.tools.animation_generator import animation_generator
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

from app.services.tools.animation_generator import animation_generator


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
