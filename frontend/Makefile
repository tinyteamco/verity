.PHONY: setup dev test test-e2e clean

# Install dependencies
setup:
	mise exec -- npm install

# Development server
dev:
	mise exec -- npm run dev

# Run all tests (E2E with dynamic backend/stub orchestration)
test:
	mise exec -- npx playwright test

# Alias for consistency
test-e2e: test

# Clean generated files
clean:
	rm -rf node_modules
	rm -rf .features-gen
	rm -rf playwright-report
	rm -rf test-results
