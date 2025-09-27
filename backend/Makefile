SHELL := /bin/bash

# Automatically use mise environment for all commands
SHELL := mise exec -- bash

.PHONY: setup dev test test-ci build lint format clean help

setup: ## Install dependencies
	@command -v mise >/dev/null 2>&1 || (echo "Installing mise..." && curl https://mise.run | sh)
	@mise install  # Ensures Python 3.12, uv, etc.
	uv sync --locked

dev: ## Start development server
	docker-compose -f ../docker-compose.yml up -d postgres minio firebase
	uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	docker-compose -f ../docker-compose.yml up -d postgres minio firebase
	uv run pytest

test-ci: ## Run tests in CI
	uv run pytest

build: ## Build Docker image
	docker build -t gcr.io/verity-platform/verity-backend:latest .

lint: ## Run linters and type checking
	uv run ruff check .
	uv run ty check

format: ## Format code and fix auto-fixable issues
	uv run ruff format .
	uv run ruff check . --fix

typecheck: ## Run type checking only
	uv run ty check

check: ## Run all checks (read-only validation)
	uv run ruff format . --check
	uv run ruff check .
	uv run ty check

clean: ## Clean up
	docker-compose -f ../docker-compose.yml down -v
	rm -rf .venv/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help