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
