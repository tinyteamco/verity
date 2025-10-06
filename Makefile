# Root Makefile for verity monorepo
SHELL := /bin/bash

.PHONY: bootstrap setup backend-setup backend-dev backend-test backend-check frontend-setup frontend-test frontend-pre-commit frontend-pre-push pre-commit pre-push help

bootstrap: ## One-shot setup for CI/fresh machines (tools + deps + hooks)
	@echo "🚀 Bootstrapping Verity development environment..."
	@command -v mise >/dev/null 2>&1 || (echo "Installing mise..." && curl https://mise.run | sh)
	@mise install  # Install global tools (hk, pkl, gcloud, etc.)
	$(MAKE) backend-setup
	@echo "🔗 Installing git hooks with mise integration..."
	@HK_MISE=true mise exec -- hk install
	@echo "✅ Bootstrap complete! Ready for development."

setup: ## Setup entire monorepo (no git hooks)
	@command -v mise >/dev/null 2>&1 || (echo "Installing mise..." && curl https://mise.run | sh)
	@mise install  # Install global tools
	$(MAKE) backend-setup

install-hooks: ## Install git hooks with mise integration
	@HK_MISE=true mise exec -- hk install

backend-setup: ## Setup backend
	cd backend && $(MAKE) setup

backend-dev: ## Run backend in development mode
	cd backend && $(MAKE) dev

backend-test: ## Run backend tests
	cd backend && $(MAKE) test

backend-check: ## Run backend code quality checks
	cd backend && $(MAKE) check

backend-clean: ## Clean backend
	cd backend && $(MAKE) clean

frontend-setup: ## Setup frontend
	cd frontend && npm ci

frontend-test: ## Run frontend E2E tests
	cd frontend && npm run test:e2e:real

frontend-pre-commit: ## Run frontend pre-commit checks
	cd frontend && $(MAKE) pre-commit

frontend-pre-push: ## Run frontend pre-push checks
	cd frontend && $(MAKE) pre-push

pre-commit: backend-check frontend-pre-commit ## Run all pre-commit checks
	@echo "✅ All pre-commit checks passed"

pre-push: backend-test frontend-pre-push ## Run all pre-push checks
	@echo "✅ All pre-push checks passed"

help: ## Show this help
	@echo "Verity Monorepo Commands:"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make bootstrap    # One-shot setup (recommended for new machines)"
	@echo ""
	@echo "📋 Other Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help