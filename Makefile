.PHONY: help install dev test lint build up down logs clean seed

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	cd backend && pip install -r requirements.txt
	cd frontend && npm ci

dev-backend: ## Run backend in development mode
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run frontend in development mode
	cd frontend && npm run dev

dev: ## Run both backend and frontend (requires tmux or two terminals)
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals"

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing

test-frontend: ## Run frontend tests
	cd frontend && npm test -- --watchAll=false --coverage

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend code
	cd backend && python -m ruff check app/ tests/ && python -m ruff format --check app/ tests/

lint-frontend: ## Lint frontend code
	cd frontend && npm run lint

build: ## Build Docker images
	docker compose build

up: ## Start all services with Docker Compose
	docker compose up -d

down: ## Stop all services
	docker compose down

logs: ## Tail service logs
	docker compose logs -f

clean: ## Clean generated files and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist frontend/build backend/htmlcov
	rm -rf uploads/*.csv uploads/*.json uploads/*.xlsx

seed: ## Generate and load synthetic demo data
	cd backend && python -m scripts.seed_data

format: ## Format all code
	cd backend && python -m ruff format app/ tests/
	cd frontend && npm run format

check: lint test ## Run linting and tests
