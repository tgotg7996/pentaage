.PHONY: init dev test lint

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
	@python -m pytest backend/tests

lint:
	@python -m ruff check backend && npm --prefix frontend run build
