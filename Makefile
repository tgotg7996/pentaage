.PHONY: init dev infra-up infra-down test test-regression-live lint

PYTHON ?= python

PG_DATA_DIR ?= infra/local/postgres
PG_LOG_FILE ?= infra/local/logs/postgres.log
REDIS_DIR ?= infra/local/redis
REDIS_LOG_FILE ?= infra/local/logs/redis.log
REDIS_PID_FILE ?= infra/local/redis/redis.pid

init:
	@if [ -d frontend ]; then \
		npm --prefix frontend install; \
	fi
	@if [ -d backend ] && [ -f backend/requirements-dev.txt ]; then \
		python -m pip install -r backend/requirements-dev.txt; \
	fi

dev:
	@echo "Starting backend (8000) and frontend (5173)..."
	@python -m uvicorn app.main:app --reload --port 8000 --app-dir backend & npm --prefix frontend run dev -- --host 0.0.0.0 --port 5173

infra-up:
	@mkdir -p "$(PG_DATA_DIR)" "infra/local/logs" "$(REDIS_DIR)"
	@if [ ! -f "$(PG_DATA_DIR)/PG_VERSION" ]; then initdb -D "$(PG_DATA_DIR)" -A trust -U postgres >/dev/null; fi
	@if ! pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then pg_ctl -D "$(PG_DATA_DIR)" -l "$(PG_LOG_FILE)" -o "-p 5432" start; fi
	@psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -c "CREATE ROLE pentaage LOGIN PASSWORD 'pentaage';" >/dev/null 2>&1 || true
	@psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -c "CREATE DATABASE pentaage OWNER pentaage;" >/dev/null 2>&1 || true
	@if ! python -c "import socket; s=socket.socket(); r=s.connect_ex(('127.0.0.1',6379)); s.close(); raise SystemExit(0 if r==0 else 1)" >/dev/null 2>&1; then redis-server --port 6379 --bind 127.0.0.1 --daemonize yes --dir "$(abspath $(REDIS_DIR))" --pidfile "$(abspath $(REDIS_PID_FILE))" --logfile "$(abspath $(REDIS_LOG_FILE))"; fi
	@echo "Infra ready: PostgreSQL(5432) + Redis(6379)"

infra-down:
	@if [ -f "$(PG_DATA_DIR)/postmaster.pid" ]; then pg_ctl -D "$(PG_DATA_DIR)" stop -m fast >/dev/null 2>&1 || true; fi
	@if [ -f "$(REDIS_PID_FILE)" ]; then redis-cli -h 127.0.0.1 -p 6379 shutdown >/dev/null 2>&1 || true; fi
	@echo "Infra stopped"

test:
	@$(PYTHON) -c "import pytest" >/dev/null 2>&1 || (echo "Missing pytest. Run: make init" && exit 1)
	@$(PYTHON) -m pytest backend/tests

test-regression-live:
	@$(PYTHON) -c "import pytest" >/dev/null 2>&1 || (echo "Missing pytest. Run: make init" && exit 1)
	@[ -n "$${DATABASE_URL}" ] || (echo "Missing DATABASE_URL. Example: postgresql+psycopg://pentaage:pentaage@127.0.0.1:5432/pentaage" && exit 1)
	@[ -n "$${REDIS_URL}" ] || (echo "Missing REDIS_URL. Example: redis://127.0.0.1:6379/0" && exit 1)
	@DATABASE_URL=$${DATABASE_URL} REDIS_URL=$${REDIS_URL} COMPOUND_CACHE_BACKEND=redis $(PYTHON) -m pytest backend/tests/integration/test_compound_api_live_backends.py

lint:
	@$(PYTHON) -c "import ruff" >/dev/null 2>&1 || (echo "Missing ruff. Run: make init" && exit 1)
	@$(PYTHON) -m ruff check backend && npm --prefix frontend run build
