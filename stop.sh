#!/usr/bin/env bash
#
# 一键关闭脚本 - 中医小程序
# 关闭顺序: Frontend → Backend → Redis → PostgreSQL
#
set -e

# ── 颜色定义 ──────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── 项目根目录（脚本所在目录）──────────────────────────
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# ── 配置 ──────────────────────────────────────────────
PG_DATA_DIR="infra/local/postgres"
REDIS_PID_FILE="infra/local/redis/redis.pid"
PID_DIR="infra/local/pids"

BACKEND_PORT=8000
FRONTEND_PORT=5173

# ── 辅助函数 ──────────────────────────────────────────
log_info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[  OK]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }

stop_by_pid_file() {
    local name="$1"
    local pid_file="$2"
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            # 等待进程退出（最多 5 秒）
            for i in $(seq 1 10); do
                if ! kill -0 "$pid" 2>/dev/null; then break; fi
                sleep 0.5
            done
            # 如果仍在运行则强制终止
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
            log_ok "$name 已关闭 (PID: $pid)"
        else
            log_warn "$name 进程已不存在 (旧 PID: $pid)"
        fi
        rm -f "$pid_file"
    else
        log_warn "未找到 $name 的 PID 文件，尝试通过端口查找..."
        return 1
    fi
}

stop_by_port() {
    local name="$1"
    local port="$2"
    local pids
    pids=$(lsof -ti :"$port" -sTCP:LISTEN 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill 2>/dev/null || true
        sleep 1
        # 检查是否还有残留进程
        pids=$(lsof -ti :"$port" -sTCP:LISTEN 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null || true
        fi
        log_ok "$name 已关闭 (端口 $port)"
    else
        log_warn "$name 未在端口 $port 上运行"
    fi
}

echo ""
echo -e "${RED}╔══════════════════════════════════════════╗${NC}"
echo -e "${RED}║         中医小程序 · 一键关闭            ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════╝${NC}"
echo ""

# ── 1. 关闭 Frontend ─────────────────────────────────
log_info "关闭 Frontend..."
stop_by_pid_file "Frontend" "$PID_DIR/frontend.pid" || stop_by_port "Frontend" "$FRONTEND_PORT"

# ── 2. 关闭 Backend ──────────────────────────────────
log_info "关闭 Backend..."
stop_by_pid_file "Backend" "$PID_DIR/backend.pid" || stop_by_port "Backend" "$BACKEND_PORT"

# ── 3. 关闭 Redis ────────────────────────────────────
log_info "关闭 Redis..."
if python -c "import socket; s=socket.socket(); r=s.connect_ex(('127.0.0.1',6379)); s.close(); raise SystemExit(0 if r==0 else 1)" >/dev/null 2>&1; then
    redis-cli -h 127.0.0.1 -p 6379 shutdown >/dev/null 2>&1 || true
    rm -f "$REDIS_PID_FILE"
    log_ok "Redis 已关闭"
else
    log_warn "Redis 未在运行"
fi

# ── 4. 关闭 PostgreSQL ───────────────────────────────
log_info "关闭 PostgreSQL..."
if [ -f "$PG_DATA_DIR/postmaster.pid" ]; then
    pg_ctl -D "$PG_DATA_DIR" stop -m fast >/dev/null 2>&1 || true
    log_ok "PostgreSQL 已关闭"
else
    log_warn "PostgreSQL 未在运行"
fi

# ── 清理日志提示 ──────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            所有服务已关闭！              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "💡 日志文件位于: ${CYAN}infra/local/logs/${NC}"
echo -e "💡 使用 ${YELLOW}./start.sh${NC} 重新启动所有服务"
