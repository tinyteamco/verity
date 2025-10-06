.PHONY: setup dev build test test-e2e clean check-types pre-commit pre-push

# Install dependencies
setup:
	mise exec -- npm install

# Development server
dev:
	mise exec -- npm run dev

# Build production bundle
build:
	mise exec -- npm run build

# Run all tests (E2E with dynamic backend/stub orchestration)
test:
	mise exec -- npx playwright test

# Alias for consistency
test-e2e: test

# Type checking
check-types:
	mise exec -- npx tsc --noEmit

# Pre-commit checks (fast, local-only)
pre-commit: check-types
	@echo "✅ Frontend pre-commit checks passed"

# Pre-push checks (comprehensive, includes tests)
pre-push: check-types test
	@echo "✅ Frontend pre-push checks passed"

# Clean generated files
clean:
	rm -rf node_modules
	rm -rf .features-gen
	rm -rf playwright-report
	rm -rf test-results
	rm -rf dist
