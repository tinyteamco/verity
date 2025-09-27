# Root Makefile for verity monorepo
SHELL := /bin/bash

.PHONY: setup backend-setup backend-dev backend-test help

setup: ## Setup entire monorepo
	@command -v mise >/dev/null 2>&1 || (echo "Installing mise..." && curl https://mise.run | sh)
	@mise install  # Install global tools
	$(MAKE) backend-setup

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
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help