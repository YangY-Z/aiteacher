#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/ai-teacher-backend"
FRONTEND_DIR="$ROOT_DIR/ai-teacher-frontend"
LOG_DIR="$ROOT_DIR/logs/dev"

BACKEND_PORT="${BACKEND_PORT:-8008}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
SANDBOX_PORT="${SANDBOX_PORT:-8080}"

BACKEND_VENV="${BACKEND_VENV:-$BACKEND_DIR/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

BACKEND_PID=""
FRONTEND_PID=""
SANDBOX_PID=""

mkdir -p "$LOG_DIR"

info() {
  printf "\033[1;34m==>\033[0m %s\n" "$1"
}

success() {
  printf "\033[0;32m✓\033[0m %s\n" "$1"
}

warn() {
  printf "\033[1;33m!\033[0m %s\n" "$1"
}

fail() {
  printf "\033[0;31m✗\033[0m %s\n" "$1" >&2
  exit 1
}

cleanup() {
  local exit_code=$?

  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  if [[ -n "$SANDBOX_PID" ]] && kill -0 "$SANDBOX_PID" 2>/dev/null; then
    kill "$SANDBOX_PID" 2>/dev/null || true
  fi

  exit "$exit_code"
}

trap cleanup EXIT INT TERM

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

port_in_use() {
  lsof -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

wait_for_url() {
  local name="$1"
  local url="$2"
  local attempts="${3:-60}"
  local pid="${4:-}"

  for ((i = 1; i <= attempts; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      success "$name 已就绪: $url"
      return 0
    fi
    if [[ -n "$pid" ]] && ! kill -0 "$pid" 2>/dev/null; then
      warn "$name 进程已退出，请查看对应日志"
      return 1
    fi
    sleep 1
  done

  warn "$name 尚未通过健康检查: $url"
  return 1
}

ensure_backend_venv() {
  if [[ ! -x "$BACKEND_VENV/bin/python" ]]; then
    info "创建后端虚拟环境: $BACKEND_VENV"
    "$PYTHON_BIN" -m venv "$BACKEND_VENV"
  fi

  if [[ ! -f "$BACKEND_VENV/.requirements-installed" ]] || [[ "$BACKEND_DIR/requirements.txt" -nt "$BACKEND_VENV/.requirements-installed" ]]; then
    info "安装/更新后端依赖"
    "$BACKEND_VENV/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"
    touch "$BACKEND_VENV/.requirements-installed"
  else
    success "后端依赖已就绪"
  fi
}

ensure_frontend_deps() {
  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    info "安装前端依赖"
    if [[ -f "$FRONTEND_DIR/package-lock.json" ]]; then
      (cd "$FRONTEND_DIR" && npm ci)
    else
      (cd "$FRONTEND_DIR" && npm install)
    fi
  else
    success "前端依赖已就绪"
  fi
}

ensure_docker() {
  if docker info >/dev/null 2>&1; then
    success "Docker 已运行"
    return 0
  fi

  if [[ "$(uname -s)" == "Darwin" ]]; then
    warn "Docker 未运行，正在尝试启动 Docker Desktop"
    open -a Docker || true
    for ((i = 1; i <= 60; i++)); do
      if docker info >/dev/null 2>&1; then
        success "Docker 已运行"
        return 0
      fi
      sleep 2
    done
  fi

  fail "Docker 未运行，请先启动 Docker Desktop 后重试"
}

start_sandbox() {
  info "启动 OpenSandbox"
  ensure_docker

  if port_in_use "$SANDBOX_PORT"; then
    if pgrep -f "opensandbox-server" >/dev/null 2>&1; then
      success "OpenSandbox 已在运行: http://localhost:$SANDBOX_PORT"
      return 0
    fi
    fail "端口 $SANDBOX_PORT 已被其他程序占用"
  fi

  local opensandbox_bin="$BACKEND_VENV/bin/opensandbox-server"
  [[ -x "$opensandbox_bin" ]] || fail "未找到 opensandbox-server，请检查后端依赖安装"

  if [[ ! -f "$HOME/.sandbox.toml" ]]; then
    info "初始化 OpenSandbox 配置: $HOME/.sandbox.toml"
    "$opensandbox_bin" init-config "$HOME/.sandbox.toml" --example docker
  fi

  OPENSANDBOX_INSECURE_SERVER="${OPENSANDBOX_INSECURE_SERVER:-YES}" \
    "$opensandbox_bin" --config "$HOME/.sandbox.toml" >"$LOG_DIR/sandbox.log" 2>&1 &
  SANDBOX_PID=$!
  wait_for_url "OpenSandbox" "http://localhost:$SANDBOX_PORT/health" 60 "$SANDBOX_PID" || {
    tail -40 "$LOG_DIR/sandbox.log" 2>/dev/null || true
    fail "OpenSandbox 启动失败"
  }
}

start_backend() {
  info "启动后端"

  if port_in_use "$BACKEND_PORT"; then
    warn "后端端口 $BACKEND_PORT 已被占用，将复用现有服务"
    wait_for_url "后端" "http://localhost:$BACKEND_PORT/health" 10 || true
    return 0
  fi

  (
    cd "$BACKEND_DIR"
    OPENSANDBOX_SERVER_URL="http://localhost:$SANDBOX_PORT" \
      "$BACKEND_VENV/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload
  ) >"$LOG_DIR/backend.log" 2>&1 &
  BACKEND_PID=$!
  wait_for_url "后端" "http://localhost:$BACKEND_PORT/health" 60 "$BACKEND_PID" || {
    tail -60 "$LOG_DIR/backend.log" 2>/dev/null || true
    fail "后端启动失败"
  }
}

start_frontend() {
  info "启动前端"

  if port_in_use "$FRONTEND_PORT"; then
    warn "前端端口 $FRONTEND_PORT 已被占用，将复用现有服务"
    wait_for_url "前端" "http://localhost:$FRONTEND_PORT" 10 || true
    return 0
  fi

  (
    cd "$FRONTEND_DIR"
    BACKEND_PORT="$BACKEND_PORT" \
      VITE_API_PROXY_TARGET="http://localhost:$BACKEND_PORT" \
      VITE_API_BASE_URL="http://localhost:$BACKEND_PORT/api/v1" \
      npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" --strictPort
  ) >"$LOG_DIR/frontend.log" 2>&1 &
  FRONTEND_PID=$!
  wait_for_url "前端" "http://localhost:$FRONTEND_PORT" 60 "$FRONTEND_PID" || {
    tail -40 "$LOG_DIR/frontend.log" 2>/dev/null || true
    fail "前端启动失败"
  }
}

main() {
  command_exists "$PYTHON_BIN" || fail "未找到 $PYTHON_BIN"
  command_exists npm || fail "未找到 npm"
  command_exists docker || fail "未找到 docker"
  command_exists lsof || fail "未找到 lsof"
  command_exists curl || fail "未找到 curl"

  ensure_backend_venv
  ensure_frontend_deps
  start_sandbox
  start_backend
  start_frontend

  echo ""
  success "全部服务已启动"
  echo "前端:        http://localhost:$FRONTEND_PORT"
  echo "后端:        http://localhost:$BACKEND_PORT"
  echo "后端文档:    http://localhost:$BACKEND_PORT/docs"
  echo "OpenSandbox: http://localhost:$SANDBOX_PORT"
  echo "日志目录:    $LOG_DIR"
  echo ""
  echo "按 Ctrl+C 停止本脚本启动的服务。"

  wait
}

main "$@"
