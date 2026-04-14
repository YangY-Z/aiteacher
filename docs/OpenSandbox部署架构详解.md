# OpenSandbox 部署架构详解

> **文档版本**: v1.0  
> **创建日期**: 2026年4月13日  
> **目标**: 理解OpenSandbox的部署架构和依赖关系

---

## 一、核心问题解答

### Q1: 是否需要单独部署OpenSandbox Server？

**答案：是的，需要部署OpenSandbox Server服务**

### Q2: Docker是否也需要？

**答案：是的，Docker是底层容器运行时（必需）**

---

## 二、OpenSandbox架构全景图

```
┌─────────────────────────────────────────────────────┐
│         你的应用 (AI Teacher Backend)                │
│         from opensandbox import Sandbox              │
└─────────────────────────────────────────────────────┘
                    ↓ HTTP API
┌─────────────────────────────────────────────────────┐
│       OpenSandbox Server (需单独部署)                │
│       • FastAPI应用                                 │
│       • 沙箱生命周期管理                              │
│       • API密钥认证                                  │
│       • 自动过期清理                                 │
│                                                      │
│   启动命令: opensandbox-server                       │
│   默认端口: localhost:8080                           │
└─────────────────────────────────────────────────────┘
                    ↓ Docker API
┌─────────────────────────────────────────────────────┐
│       Docker Engine (必需)                           │
│       • 容器运行时                                    │
│       • 镜像管理                                      │
│       • 网络管理                                      │
│                                                      │
│   本地: Docker Desktop                               │
│   服务器: Docker Engine                              │
└─────────────────────────────────────────────────────┘
                    ↓ 创建容器
┌─────────────────────────────────────────────────────┐
│       沙箱容器实例                                    │
│       ┌─────────────────────────────┐               │
│       │  execd (自动注入)            │               │
│       │  • HTTP守护进程              │               │
│       │  • 代码执行引擎              │               │
│       │  • 文件操作接口              │               │
│       ├─────────────────────────────┤               │
│       │  Jupyter Server (自动启动)   │               │
│       │  • 代码解释器                │               │
│       ├─────────────────────────────┤               │
│       │  你的镜像内容                 │               │
│       │  • Python 3.11               │               │
│       │  • Manim                     │               │
│       └─────────────────────────────┘               │
└─────────────────────────────────────────────────────┘
```

---

## 三、部署方案对比

### 方案A：本地开发环境（推荐）

**架构：**
```
你的电脑
├─ AI Teacher Backend (Python FastAPI)
├─ OpenSandbox Server (Python进程)
└─ Docker Desktop
    └─ 沙箱容器
```

**部署步骤：**

```bash
# Step 1: 安装Docker Desktop（如果还没有）
# macOS: https://docs.docker.com/desktop/install/mac-install/
# Windows: https://docs.docker.com/desktop/install/windows-install/
# Linux: https://docs.docker.com/engine/install/

# Step 2: 启动Docker Desktop
open -a Docker  # macOS

# Step 3: 安装OpenSandbox Server
pip install opensandbox-server

# Step 4: 初始化配置
opensandbox-server init-config ~/.sandbox.toml --example docker

# Step 5: 启动OpenSandbox Server
opensandbox-server

# 输出:
# INFO:     Started server process [12345]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://localhost:8080

# Step 6: 在你的应用中使用
cd ai-teacher-backend
python -m uvicorn app.main:app --reload
```

**资源占用：**
| 组件 | 内存 | CPU |
|------|------|-----|
| Docker Desktop | ~500MB | 低 |
| OpenSandbox Server | ~50MB | 低 |
| 单个沙箱容器 | ~100-200MB | 中 |

**优点：**
- ✅ 部署简单（2个命令）
- ✅ 无需额外服务器
- ✅ 开发调试方便

**缺点：**
- ⚠️ 需要本地有Docker Desktop
- ⚠️ 不适合生产环境

---

### 方案B：单服务器部署（生产）

**架构：**
```
云服务器 (如阿里云ECS)
├─ Docker Engine
├─ OpenSandbox Server (Systemd服务)
├─ AI Teacher Backend (FastAPI)
└─ Nginx (反向代理)
```

**部署步骤：**

```bash
# === 在服务器上执行 ===

# Step 1: 安装Docker Engine
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER

# Step 2: 安装Python和依赖
sudo apt install python3.11 python3-pip
pip3 install opensandbox-server opensandbox

# Step 3: 创建配置文件
mkdir -p ~/.config/opensandbox
opensandbox-server init-config ~/.config/opensandbox/config.toml --example docker

# Step 4: 创建Systemd服务
sudo tee /etc/systemd/system/opensandbox.service <<EOF
[Unit]
Description=OpenSandbox Server
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment="PATH=/home/ubuntu/.local/bin:/usr/bin"
ExecStart=/home/ubuntu/.local/bin/opensandbox-server --config /home/ubuntu/.config/opensandbox/config.toml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Step 5: 启动服务
sudo systemctl daemon-reload
sudo systemctl enable opensandbox
sudo systemctl start opensandbox

# Step 6: 检查状态
sudo systemctl status opensandbox

# Step 7: 配置Nginx反向代理
sudo tee /etc/nginx/sites-available/opensandbox <<EOF
server {
    listen 80;
    server_name sandbox.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/opensandbox /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**配置文件示例：**

```toml
# ~/.config/opensandbox/config.toml

[server]
host = "0.0.0.0"
port = 8080
api_key = "your-secret-api-key"  # 生产环境必须设置

[docker]
network_mode = "bridge"  # 或 "host"

[defaults]
timeout = 3600  # 1小时
max_instances = 100  # 最大沙箱数量

[cleanup]
enabled = true
interval = 300  # 每5分钟清理过期沙箱
```

**优点：**
- ✅ 生产级部署
- ✅ 自动重启
- ✅ 集中管理

**缺点：**
- ⚠️ 需要单独的服务器
- ⚠️ 运维成本较高

---

### 方案C：Kubernetes部署（大规模生产）

**架构：**
```
Kubernetes集群
├─ OpenSandbox Server (Deployment)
├─ Sandbox Router (Ingress)
├─ 沙箱Pod池 (BatchSandbox)
└─ 持久化存储 (PVC)
```

**部署步骤：**

```bash
# Step 1: 安装Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Step 2: 添加OpenSandbox Helm仓库
helm repo add opensandbox https://alibaba.github.io/OpenSandbox/charts
helm repo update

# Step 3: 安装OpenSandbox
helm install opensandbox opensandbox/opensandbox \
  --namespace opensandbox \
  --create-namespace \
  --set server.replicaCount=2 \
  --set server.apiKey="your-secret-key" \
  --set runtime.type=kubernetes

# Step 4: 验证安装
kubectl get pods -n opensandbox
```

**优点：**
- ✅ 高可用
- ✅ 自动扩缩容
- ✅ 支持Firecracker/gVisor

**缺点：**
- ⚠️ 部署复杂
- ⚠️ 需要K8s集群
- ⚠️ 成本较高

---

## 四、三种方案对比

| 维度 | 方案A（本地） | 方案B（单服务器） | 方案C（K8s） |
|------|-------------|----------------|------------|
| **部署难度** | ⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐⭐ 复杂 |
| **运维成本** | ⭐ 极低 | ⭐⭐ 中等 | ⭐⭐⭐⭐ 高 |
| **并发能力** | 10-50 | 50-200 | 200+ |
| **成本** | ¥0 | ¥200-500/月 | ¥1000+/月 |
| **适用场景** | 开发测试 | MVP/小规模生产 | 大规模生产 |

---

## 五、你的项目推荐方案

### **阶段1：开发测试（现在）**

**推荐：方案A - 本地开发环境**

```bash
# 一键启动脚本
cat > start_sandbox.sh << 'EOF'
#!/bin/bash

echo "=== 启动OpenSandbox沙箱服务 ==="

# 检查Docker
if ! docker info &> /dev/null; then
    echo "启动Docker Desktop..."
    open -a Docker
    sleep 10
fi

# 启动OpenSandbox Server
if ! lsof -i:8080 &> /dev/null; then
    echo "启动OpenSandbox Server..."
    opensandbox-server &
    sleep 3
else
    echo "OpenSandbox Server已在运行"
fi

echo "✅ OpenSandbox服务已就绪"
echo "服务地址: http://localhost:8080"
EOF

chmod +x start_sandbox.sh
./start_sandbox.sh
```

**你的应用配置：**

```python
# ai-teacher-backend/app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OpenSandbox配置
    opensandbox_server_url: str = "http://localhost:8080"
    opensandbox_api_key: str = ""  # 本地开发可为空
    
    # 沙箱配置
    sandbox_image: str = "opensandbox/code-interpreter:latest"
    sandbox_timeout: int = 60  # 秒
    
    class Config:
        env_file = ".env"
```

```env
# ai-teacher-backend/.env

# OpenSandbox
OPENSANDBOX_SERVER_URL=http://localhost:8080
OPENSANDBOX_API_KEY=
SANDBOX_IMAGE=opensandbox/code-interpreter:latest
```

---

### **阶段2：MVP生产（3-6个月后）**

**推荐：方案B - 单服务器部署**

```bash
# 在你的云服务器上
# 假设服务器IP: 123.45.67.89

# 1. 安装Docker和OpenSandbox（见上面步骤）

# 2. 配置OpenSandbox Server监听所有接口
# ~/.config/opensandbox/config.toml
[server]
host = "0.0.0.0"
port = 8080
api_key = "sk-your-secret-key-here"

# 3. 启动OpenSandbox Server
sudo systemctl start opensandbox

# 4. 你的应用配置更新
# .env
OPENSANDBOX_SERVER_URL=http://123.45.67.89:8080
OPENSANDBOX_API_KEY=sk-your-secret-key-here
```

---

### **阶段3：大规模生产（1年后）**

**推荐：方案C - Kubernetes部署**

当你有100+并发学生时，考虑迁移到K8s。

---

## 六、关键问题解答

### Q1: OpenSandbox Server是否很重？

**答案：不重**

```bash
# OpenSandbox Server资源占用
内存: ~50MB
CPU: 几乎为0（空闲时）
启动时间: 1-2秒
```

**对比：**
| 服务 | 内存占用 |
|------|---------|
| OpenSandbox Server | 50MB |
| 你的FastAPI后端 | 100-200MB |
| PostgreSQL | 50-100MB |
| Redis | 10-20MB |
| **OpenSandbox相对很轻** | ✅ |

---

### Q2: 能否将OpenSandbox Server集成到我的应用中？

**答案：理论上可以，但不推荐**

**不推荐原因：**
1. **关注点分离** - OpenSandbox管理沙箱生命周期，你的应用关注业务逻辑
2. **独立扩展** - OpenSandbox可以独立扩容
3. **故障隔离** - OpenSandbox崩溃不影响你的应用
4. **官方设计** - OpenSandbox设计为独立服务

**如果一定要集成：**

```python
# 不推荐的方式
from opensandbox.server import create_app
import uvicorn

# 在你的FastAPI应用中挂载
app = FastAPI()

# 挂载OpenSandbox（不推荐）
sandbox_app = create_app()
app.mount("/sandbox", sandbox_app)

# 推荐的方式：独立进程
# 终端1: opensandbox-server
# 终端2: uvicorn app.main:app
```

---

### Q3: Docker Desktop是否必需？

**答案：本地开发必需，生产环境用Docker Engine**

| 环境 | Docker方案 |
|------|-----------|
| macOS开发 | Docker Desktop ✅ |
| Windows开发 | Docker Desktop ✅ |
| Linux开发 | Docker Engine ✅ |
| 生产服务器 | Docker Engine ✅ |

**安装指南：**

```bash
# macOS
brew install --cask docker

# Ubuntu/Debian
curl -fsSL https://get.docker.com | bash

# CentOS/RHEL
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io
```

---

## 七、完整部署清单

### 本地开发环境

```bash
# ✅ 必需组件
[1] Docker Desktop          # 容器运行时
[2] Python 3.10+            # OpenSandbox Server依赖
[3] opensandbox-server      # 沙箱管理服务
[4] opensandbox (Python SDK) # 客户端库

# 安装命令
brew install --cask docker              # macOS
pip install opensandbox-server opensandbox
```

### 生产环境

```bash
# ✅ 必需组件
[1] Docker Engine           # 容器运行时
[2] OpenSandbox Server      # 沙箱管理服务（Systemd）
[3] Nginx                   # 反向代理（可选）
[4] 监控告警                # Prometheus + Grafana（可选）

# ✅ 可选组件
[5] Kubernetes              # 大规模部署
[6] Firecracker             # 高性能运行时
[7] 私有镜像仓库            # 存储自定义镜像
```

---

## 八、快速验证部署

### 验证脚本

```bash
#!/bin/bash

echo "=== OpenSandbox部署验证 ==="

# 1. 检查Docker
echo "1. 检查Docker..."
if docker info &> /dev/null; then
    echo "   ✅ Docker运行正常"
else
    echo "   ❌ Docker未运行"
    exit 1
fi

# 2. 检查OpenSandbox Server
echo "2. 检查OpenSandbox Server..."
if curl -s http://localhost:8080/health &> /dev/null; then
    echo "   ✅ OpenSandbox Server运行正常"
else
    echo "   ❌ OpenSandbox Server未运行"
    echo "   执行: opensandbox-server"
    exit 1
fi

# 3. 测试创建沙箱
echo "3. 测试创建沙箱..."
python3 << 'PYTHON'
import asyncio
from opensandbox import Sandbox

async def test():
    sandbox = await Sandbox.create("python:3.11-slim")
    result = await sandbox.commands.run("echo 'Hello OpenSandbox!'")
    print(f"   ✅ 沙箱创建成功: {result.logs.stdout[0].text}")
    await sandbox.kill()

asyncio.run(test())
PYTHON

echo ""
echo "✅ 所有检查通过！OpenSandbox已就绪"
```

---

## 九、总结

### 核心要点

| 问题 | 答案 | 说明 |
|------|------|------|
| 需要OpenSandbox Server吗？ | ✅ 是 | 必须单独部署 |
| 需要Docker吗？ | ✅ 是 | 作为底层容器运行时 |
| OpenSandbox Server重吗？ | ❌ 不重 | 仅50MB内存 |
| 部署复杂吗？ | ❌ 简单 | 2个命令即可启动 |

### 推荐方案

**当前阶段（开发测试）：**
```bash
# 1. 安装Docker Desktop
# 2. 安装OpenSandbox
pip install opensandbox-server opensandbox

# 3. 启动服务
opensandbox-server

# 4. 在你的应用中使用
from opensandbox import Sandbox
```

**生产阶段：**
- 小规模：单服务器部署（Docker Engine + Systemd）
- 大规模：Kubernetes部署

---

**文档版本**: v1.0  
**最后更新**: 2026年4月13日
