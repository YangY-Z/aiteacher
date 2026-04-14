#!/bin/bash

# OpenSandbox 服务启动脚本
# 用于快速启动OpenSandbox服务器

set -e

echo "=== OpenSandbox 服务启动脚本 ==="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 函数：打印成功消息
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# 函数：打印警告消息
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 函数：打印错误消息
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Step 1: 检查Docker
echo "Step 1: 检查Docker..."
if docker info &> /dev/null; then
    print_success "Docker运行正常"
else
    print_error "Docker未运行"
    echo ""
    echo "请先启动Docker Desktop:"
    echo "  macOS: open -a Docker"
    echo "  Linux: sudo systemctl start docker"
    exit 1
fi

# Step 2: 检查OpenSandbox Server是否已安装
echo ""
echo "Step 2: 检查OpenSandbox Server..."
if ! command -v opensandbox-server &> /dev/null; then
    print_warning "OpenSandbox Server未安装"
    echo ""
    echo "正在安装 OpenSandbox..."
    pip install opensandbox-server opensandbox
    
    if [ $? -eq 0 ]; then
        print_success "OpenSandbox安装成功"
    else
        print_error "OpenSandbox安装失败"
        exit 1
    fi
else
    print_success "OpenSandbox Server已安装"
fi

# Step 3: 检查OpenSandbox Server是否已运行
echo ""
echo "Step 3: 检查OpenSandbox Server状态..."
if lsof -i:8080 &> /dev/null; then
    print_warning "端口8080已被占用"
    
    # 检查是否是OpenSandbox Server
    if pgrep -f "opensandbox-server" &> /dev/null; then
        print_success "OpenSandbox Server已在运行"
        echo ""
        echo "服务地址: http://localhost:8080"
        echo "健康检查: curl http://localhost:8080/health"
        exit 0
    else
        print_error "其他程序占用了8080端口"
        echo ""
        echo "请先关闭占用端口的程序:"
        echo "  lsof -i:8080  # 查看占用进程"
        exit 1
    fi
fi

# Step 4: 初始化配置
echo ""
echo "Step 4: 初始化OpenSandbox配置..."
if [ ! -f ~/.sandbox.toml ]; then
    print_warning "配置文件不存在，正在创建..."
    opensandbox-server init-config ~/.sandbox.toml --example docker
    print_success "配置文件创建成功: ~/.sandbox.toml"
else
    print_success "配置文件已存在: ~/.sandbox.toml"
fi

# Step 5: 启动OpenSandbox Server
echo ""
echo "Step 5: 启动OpenSandbox Server..."
echo ""
echo "服务即将启动..."
echo "地址: http://localhost:8080"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""
echo "=========================================="
echo ""

# 启动服务
opensandbox-server --config ~/.sandbox.toml
