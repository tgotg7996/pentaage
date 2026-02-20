.PHONY: init dev test lint

PYTHON ?= python

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

test:
	@$(PYTHON) -c "import pytest" >/dev/null 2>&1 || (echo "Missing pytest. Run: make init" && exit 1)
	@$(PYTHON) -m pytest backend/tests

lint:
	@$(PYTHON) -c "import ruff" >/dev/null 2>&1 || (echo "Missing ruff. Run: make init" && exit 1)
	@$(PYTHON) -m ruff check backend && npm --prefix frontend run build
