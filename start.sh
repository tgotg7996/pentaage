#!/usr/bin/env bash
#
# 一键启动脚本 - 中医小程序
# 启动顺序: PostgreSQL → Redis → Backend → Frontend
#
set -e

# ── 颜色定义 ──────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── 项目根目录（脚本所在目录）──────────────────────────
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# ── 配置 ──────────────────────────────────────────────
PG_DATA_DIR="infra/local/postgres"
PG_LOG_FILE="infra/local/logs/postgres.log"
REDIS_DIR="infra/local/redis"
REDIS_LOG_FILE="infra/local/logs/redis.log"
REDIS_PID_FILE="infra/local/redis/redis.pid"
PID_DIR="infra/local/pids"

BACKEND_PORT=8000
FRONTEND_PORT=5173

# ── 辅助函数 ──────────────────────────────────────────
log_info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[  OK]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_err()   { echo -e "${RED}[FAIL]${NC}  $1"; }

check_command() {
    if ! command -v "$1" &>/dev/null; then
        log_err "未找到命令: $1，请先安装。"
        exit 1
    fi
}

# ── 前置检查 ──────────────────────────────────────────
log_info "正在检查依赖..."
check_command pg_ctl
check_command redis-server
check_command python
check_command npm

# ── 创建必要目录 ──────────────────────────────────────
mkdir -p "$PG_DATA_DIR" "infra/local/logs" "$REDIS_DIR" "$PID_DIR"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         中医小程序 · 一键启动            ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

# ── 1. 启动 PostgreSQL ────────────────────────────────
log_info "启动 PostgreSQL..."
if [ ! -f "$PG_DATA_DIR/PG_VERSION" ]; then
    log_info "首次运行，初始化数据库..."
    initdb -D "$PG_DATA_DIR" -A trust -U postgres >/dev/null
fi

if pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
    log_ok "PostgreSQL 已在运行 (端口 5432)"
else
    pg_ctl -D "$PG_DATA_DIR" -l "$PG_LOG_FILE" -o "-p 5432" start >/dev/null 2>&1
    sleep 1
    if pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
        log_ok "PostgreSQL 启动成功 (端口 5432)"
    else
        log_err "PostgreSQL 启动失败，请检查日志: $PG_LOG_FILE"
        exit 1
    fi
fi

# 创建用户和数据库（忽略已存在的错误）
psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -c "CREATE ROLE pentaage LOGIN PASSWORD 'pentaage';" >/dev/null 2>&1 || true
psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -c "CREATE DATABASE pentaage OWNER pentaage;" >/dev/null 2>&1 || true

# ── 2. 启动 Redis ─────────────────────────────────────
log_info "启动 Redis..."
if python -c "import socket; s=socket.socket(); r=s.connect_ex(('127.0.0.1',6379)); s.close(); raise SystemExit(0 if r==0 else 1)" >/dev/null 2>&1; then
    log_ok "Redis 已在运行 (端口 6379)"
else
    redis-server \
        --port 6379 \
        --bind 127.0.0.1 \
        --daemonize yes \
        --dir "$(cd "$REDIS_DIR" && pwd)" \
        --pidfile "$(cd "$REDIS_DIR" && pwd)/redis.pid" \
        --logfile "$(cd "infra/local/logs" && pwd)/redis.log" \
        >/dev/null 2>&1
    sleep 1
    if python -c "import socket; s=socket.socket(); r=s.connect_ex(('127.0.0.1',6379)); s.close(); raise SystemExit(0 if r==0 else 1)" >/dev/null 2>&1; then
        log_ok "Redis 启动成功 (端口 6379)"
    else
        log_err "Redis 启动失败，请检查日志: $REDIS_LOG_FILE"
        exit 1
    fi
fi

# ── 3. 启动 Backend (uvicorn) ─────────────────────────
log_info "启动 Backend (uvicorn)..."
if lsof -i :"$BACKEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    log_warn "端口 $BACKEND_PORT 已被占用，跳过 Backend 启动"
else
    nohup python -m uvicorn app.main:app --reload --port "$BACKEND_PORT" --app-dir backend \
        > infra/local/logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "$BACKEND_PID" > "$PID_DIR/backend.pid"
    sleep 2
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        log_ok "Backend 启动成功 (PID: $BACKEND_PID, 端口 $BACKEND_PORT)"
    else
        log_err "Backend 启动失败，请检查日志: infra/local/logs/backend.log"
        exit 1
    fi
fi

# ── 4. 启动 Frontend (Vite) ──────────────────────────
log_info "启动 Frontend (Vite)..."
if lsof -i :"$FRONTEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    log_warn "端口 $FRONTEND_PORT 已被占用，跳过 Frontend 启动"
else
    nohup npm --prefix frontend run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" \
        > infra/local/logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "$FRONTEND_PID" > "$PID_DIR/frontend.pid"
    sleep 3
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        log_ok "Frontend 启动成功 (PID: $FRONTEND_PID, 端口 $FRONTEND_PORT)"
    else
        log_err "Frontend 启动失败，请检查日志: infra/local/logs/frontend.log"
        exit 1
    fi
fi

# ── 完成 ──────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            所有服务已启动！              ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}  PostgreSQL  : ${CYAN}127.0.0.1:5432${NC}            ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Redis       : ${CYAN}127.0.0.1:6379${NC}            ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Backend API : ${CYAN}http://localhost:${BACKEND_PORT}${NC}     ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Frontend    : ${CYAN}http://localhost:${FRONTEND_PORT}${NC}     ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "💡 使用 ${YELLOW}./stop.sh${NC} 一键关闭所有服务"
