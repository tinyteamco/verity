# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a UXR (User Experience Research) platform MVP. The codebase currently contains:
- OpenAPI specification (`openapi.yaml`) defining the API contract
- Working FastAPI backend with health check endpoint
- Docker Compose configuration for local services
- Architecture and planning documentation
- BDD testing infrastructure

## Development Environment & Workflow

### Tools & Version Management
- **mise**: Manages tool versions (Python 3.12, uv, node, gcloud) transparently
- **uv**: Python package manager and virtual environment (faster than pip/poetry)
- **make**: Standard interface for all workflow commands (hides mise complexity)

### Project Structure (Monorepo)
```
verity/
├── .mise.toml                # Global tool versions
├── Makefile                  # Root-level commands
├── backend/
│   ├── .mise.toml           # Backend-specific env vars and tools
│   ├── Makefile             # Backend workflow commands
│   ├── pyproject.toml       # Python dependencies (uv managed)
│   ├── uv.lock             # Lockfile for reproducible builds
│   ├── src/                # Python source code
│   │   └── api/
│   │       └── main.py     # FastAPI application
│   └── tests/              # BDD tests with pytest-bdd
│       ├── features/       # Gherkin feature files
│       └── step_defs/      # Step implementations
├── frontend/               # (future)
└── docs/                   # Architecture & planning docs
```

### Development Commands
All commands use `make` (which transparently uses mise for tool management):

```bash
# From backend/ directory:
make setup      # Install tools & dependencies
make dev        # Start dev server with hot-reload
make test       # Run BDD tests
make test-ci    # Run tests without services
make lint       # Run linters
make format     # Format code
make clean      # Clean up temp files

# From root directory:
make backend-dev    # Start backend dev
make backend-test   # Run backend tests
```

### Key Architectural Decisions

1. **BDD Testing**: Using pytest-bdd for behavior-driven development
2. **Transparent Tool Management**: mise works invisibly behind make commands
3. **Inside-Out Development**: Start with health check, build full slices incrementally
4. **Container-First Deployment**: Target Cloud Run for serverless container hosting
5. **Local Development**: Python runs locally for speed, services in Docker
6. **Zero Warnings Policy**: All code must pass ruff + ty with zero warnings/errors

### Code Quality Standards

**ZERO WARNINGS POLICY**: All code must pass these checks with no warnings or errors:
- `ruff format .` - Code formatting
- `ruff check .` - Linting (comprehensive rule set including type annotations)
- `ty src` - Static type checking (strict mode)

**Type Hint Requirements**:
- All functions must have return type annotations
- All function parameters must have type annotations
- Use strict type checking with `ty` (Astral's fast type checker)
- No `Any` types except when absolutely necessary

**Tool Choices**:
- **ruff**: Linting and formatting (10-100x faster than flake8/black)
- **ty**: Static type checking (Astral's replacement for mypy, faster and more accurate)
- **pytest-bdd**: BDD testing with Gherkin scenarios

## Current Implementation Status

### Completed
- ✅ Health check endpoint (`GET /healthz`) returning JSON status
- ✅ BDD test infrastructure with working health check test
- ✅ mise + uv + make workflow fully integrated
- ✅ Project structure with src/tests layout

### API Specification
The `openapi.yaml` file defines:
- Authentication using Firebase JWT tokens with bearer auth
- Two tenant types: `company` and `interviewee`
- Endpoints for studies, interviews, recordings, transcripts, and summaries
- Role-based access with roles: owner|admin|member

### Infrastructure
`docker-compose.yml` defines these services:
- PostgreSQL 16 (port 5432)
- MinIO object storage (ports 9000/9001)
- Firebase Auth emulator (port 9099)
- API service (port 8000) - needs Dockerfile implementation

### Documentation Structure
- `/docs/001-overview/` - MVP information architecture and UXR project details
- `/docs/002-architecture/` - Technical architecture decisions and patterns
- `/docs/003-plans/` - Implementation plans and roadmaps