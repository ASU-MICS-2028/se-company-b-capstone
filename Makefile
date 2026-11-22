PYTHON ?= python3.12
VENV := backend/.venv
BIN := $(VENV)/bin

.PHONY: dev-backend dev-frontend test lint seed install

$(BIN)/activate: backend/requirements.txt backend/requirements-dev.txt
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -r backend/requirements-dev.txt
	touch $(BIN)/activate

frontend/node_modules: frontend/package-lock.json
	cd frontend && npm ci
	touch frontend/node_modules

install: $(BIN)/activate frontend/node_modules

dev-backend: $(BIN)/activate
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

dev-frontend: frontend/node_modules
	cd frontend && npm run dev

test: install
	cd backend && .venv/bin/pytest -m "not pending"
	cd frontend && npm test

lint: install
	cd backend && .venv/bin/ruff check .
	cd frontend && npm run lint && npm run typecheck

seed: $(BIN)/activate
	@echo "Seed loader not implemented yet (Sprint 1, step 6)."
