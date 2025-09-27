# Root Makefile for verity monorepo
SHELL := /bin/bash

.PHONY: bootstrap setup backend-setup backend-dev backend-test help

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

backend-clean: ## Clean backend
	cd backend && $(MAKE) clean

help: ## Show this help
	@echo "Verity Monorepo Commands:"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make bootstrap    # One-shot setup (recommended for new machines)"
	@echo ""
	@echo "📋 Other Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help