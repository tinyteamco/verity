SHELL := /bin/bash

# Automatically use mise environment for all commands
SHELL := mise exec -- bash

.PHONY: setup dev test test-ci build lint format clean help

setup: ## Install dependencies
	@command -v mise >/dev/null 2>&1 || (echo "Installing mise..." && curl https://mise.run | sh)
	@mise install  # Ensures Python 3.12, uv, etc.
	uv sync --locked

dev: ## Start development server
	docker compose -f ../docker-compose.yml up -d postgres minio
	$(MAKE) start-firebase
	$(MAKE) seed-admin
	uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests (with services)
	docker compose -f ../docker-compose.yml up -d postgres minio
	$(MAKE) start-firebase
	$(MAKE) seed-admin
	APP_ENV=local uv run pytest

test-ci: .docker-services .firebase-stub-seeded ## Run tests in CI (uses lightweight stub, isolated from dev)
	APP_ENV=local FIREBASE_AUTH_EMULATOR_HOST=localhost:9199 uv run pytest

.PHONY: .docker-services
.docker-services: ## Ensure Docker services (postgres, minio) are running
	@echo "🐳 Ensuring Docker services are running..."
	@docker compose -f ../docker-compose.yml up -d postgres minio minio-setup
	@echo "✅ Docker services ready"

.PHONY: .firebase-seeded
.firebase-seeded: scripts/seed_firebase.py
	@echo "🌱 Ensuring Firebase is seeded..."
	@if ! curl -s http://localhost:9099 >/dev/null 2>&1; then \
		echo "⚠️  Firebase emulator not running, starting it..."; \
		$(MAKE) start-firebase; \
	fi
	@uv run python scripts/seed_firebase.py
	@echo "✅ Firebase seeded"

.PHONY: .firebase-stub-seeded
.firebase-stub-seeded: scripts/firebase_auth_stub.py
	@echo "🌱 Ensuring Firebase stub is running and seeded..."
	@if ! curl -s http://localhost:9199 >/dev/null 2>&1; then \
		echo "⚠️  Firebase stub not running, starting it..."; \
		$(MAKE) start-firebase-stub; \
	fi
	@echo "🧹 Clearing Firebase stub state..."
	@curl -s -X POST http://localhost:9199/emulator/v1/projects/verity-local/accounts:delete >/dev/null 2>&1 || true
	@FIREBASE_AUTH_EMULATOR_HOST=localhost:9199 uv run python scripts/seed_firebase.py
	@echo "✅ Firebase stub seeded"

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

# Aliases for hk integration
check-format: ## Check formatting only
	uv run ruff format . --check

check-lint: ## Check linting only
	uv run ruff check .

check-types: ## Check types only
	uv run ty check

fix-format: ## Fix formatting
	uv run ruff format .

fix-lint: ## Fix linting issues
	uv run ruff check . --fix

# Firebase emulator management
start-firebase: ## Start Firebase emulator
	@echo "🔥 Starting Firebase emulator..."
	@command -v firebase >/dev/null 2>&1 || (echo "Installing Firebase CLI..." && npm install -g firebase-tools)
	@if ! curl -s http://localhost:9099 >/dev/null 2>&1; then \
		echo "Starting Firebase Auth emulator..."; \
		firebase emulators:start --only auth --project verity-local & \
		echo "Waiting for Firebase emulator to be ready..."; \
		for i in {1..30}; do \
			if curl -s http://localhost:9099 >/dev/null 2>&1; then \
				echo "✅ Firebase emulator is ready!"; \
				break; \
			fi; \
			echo "Attempt $$i/30: Emulator not ready yet, waiting 2 seconds..."; \
			sleep 2; \
		done; \
		if ! curl -s http://localhost:9099 >/dev/null 2>&1; then \
			echo "❌ Firebase emulator failed to start after 60 seconds"; \
			exit 1; \
		fi; \
	else \
		echo "✅ Firebase emulator is already running"; \
	fi

stop-firebase: ## Stop Firebase emulator
	@echo "🔥 Stopping Firebase emulator..."
	@pkill -f "firebase emulators:start" || echo "No Firebase emulator process found"
	@echo "✅ Firebase emulator stopped"

# Firebase Auth stub management (lightweight, for tests)
start-firebase-stub: ## Start Firebase Auth stub (port 9199, <1s startup)
	@echo "🔥 Starting Firebase Auth stub..."
	@if ! curl -s http://localhost:9199 >/dev/null 2>&1; then \
		echo "Starting Firebase Auth stub on port 9199..."; \
		STUB_PORT=9199 uv run python scripts/firebase_auth_stub.py > /tmp/firebase-stub.log 2>&1 & \
		echo "Waiting for Firebase stub to be ready..."; \
		for i in {1..10}; do \
			if curl -s http://localhost:9199 >/dev/null 2>&1; then \
				echo "✅ Firebase stub is ready!"; \
				break; \
			fi; \
			echo "Attempt $$i/10: Stub not ready yet, waiting 0.5 seconds..."; \
			sleep 0.5; \
		done; \
		if ! curl -s http://localhost:9199 >/dev/null 2>&1; then \
			echo "❌ Firebase stub failed to start after 5 seconds"; \
			cat /tmp/firebase-stub.log; \
			exit 1; \
		fi; \
	else \
		echo "✅ Firebase stub is already running"; \
	fi

stop-firebase-stub: ## Stop Firebase Auth stub
	@echo "🔥 Stopping Firebase stub..."
	@pkill -f "firebase_auth_stub.py" || echo "No Firebase stub process found"
	@echo "✅ Firebase stub stopped"

seed-admin: start-firebase ## Seed super admin user in Firebase emulator
	@echo "🌱 Seeding super admin user..."
	uv run python scripts/seed_firebase.py
	@echo "✅ Super admin user seeded"

clean: ## Clean up
	$(MAKE) stop-firebase
	$(MAKE) stop-firebase-stub
	docker compose -f ../docker-compose.yml down -v
	rm -rf .venv/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -f .firebase-seeded

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help