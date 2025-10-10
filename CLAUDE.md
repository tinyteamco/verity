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
├── infra/                  # Infrastructure as Code (Pulumi)
│   ├── .mise.toml         # Pulumi CLI + Python 3.12
│   ├── Pulumi.yaml        # Pulumi project config
│   ├── Pulumi.dev.yaml    # Dev stack config
│   ├── Pulumi.prod.yaml   # Prod stack config
│   ├── __main__.py        # Infrastructure definition
│   └── pyproject.toml     # Pulumi dependencies
├── frontend/               # (future)
├── docs/                   # Architecture & planning docs
└── scripts/                # Bootstrap and utility scripts
    └── bootstrap-gcp-pulumi.sh  # One-time GCP setup
```

### Development Commands
All commands use `make` (which transparently uses mise for tool management):

```bash
# 🚀 One-time setup (CI/fresh machines):
make bootstrap       # Install tools + deps + git hooks (complete setup)

# From backend/ directory:
make setup          # Install tools & dependencies
make dev            # Start dev server with hot-reload
make test           # Run BDD tests
make test-ci        # Run tests without services (CI-friendly)
make check          # Run all checks (format + lint + types)
make lint           # Run linters and type checking
make format         # Format code and fix auto-fixable issues
make clean          # Clean up temp files

# Individual checks (for hk integration):
make check-format   # Check formatting only
make check-lint     # Check linting only
make check-types    # Check types only
make fix-format     # Fix formatting
make fix-lint       # Fix linting issues

# From root directory:
make backend-dev    # Start backend dev
make backend-test   # Run backend tests
make install-hooks  # Install git hooks with mise integration

# CI/Local testing:
act --container-architecture linux/amd64  # Test GitHub Actions locally
```

### Key Architectural Decisions

1. **BDD Testing**: Using pytest-bdd for behavior-driven development
2. **Transparent Tool Management**: mise works invisibly behind make commands
3. **Inside-Out Development**: Start with health check, build full slices incrementally
4. **Container-First Deployment**: Target Cloud Run for serverless container hosting
5. **Local Development**: Python runs locally for speed, services in Docker
6. **Zero Warnings Policy**: All code must pass ruff + ty with zero warnings/errors
7. **Git Hooks with hk**: Pre-commit hooks enforce code quality automatically using hk + mise
8. **CI/CD with GitHub Actions**: Automated validation on every push/PR with local testing via act
9. **Infrastructure as Code**: Pulumi in Python for GCP infrastructure management
10. **CI-Only Deployments**: Infrastructure changes only via GitHub Actions (no local deployments)
11. **Workload Identity**: GitHub authenticates to GCP without JSON keys (OIDC)
12. **Multi-Tenancy Security**: Never trust client-provided tenant context - see `/docs/002-architecture/004-security-guidelines.md`

### BDD-First Development Workflow

**CRITICAL**: This project follows strict BDD/TDD practices. Always follow this workflow:

1. **Write BDD tests first** - Before implementing any feature:
   - **Backend**: Add Gherkin scenarios to `backend/tests/features/*.feature`
   - **Frontend**: Add Gherkin scenarios to `frontend/tests/features/*.feature`
   - Write step implementations that call the API/UI

2. **Run tests to confirm they fail** - Verify the test correctly detects missing functionality

3. **Implement the feature** - Write minimal code to make tests pass:
   - Backend: API endpoints, models, business logic
   - Frontend: UI components, API calls, state management

4. **Run tests to confirm they pass** - Verify implementation meets requirements

5. **Refactor if needed** - Improve code while keeping tests green

**Never skip writing tests first.** Tests define the contract and prevent regressions.

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
- **hk**: Git hooks management (integrates with mise for consistent environments)
- **act**: Local GitHub Actions testing (validates CI before pushing)

## Current Implementation Status

### Completed
- ✅ Health check endpoint (`GET /healthz`) returning JSON status
- ✅ BDD test infrastructure with working health check test
- ✅ mise + uv + make workflow fully integrated
- ✅ Project structure with src/tests layout
- ✅ Git hooks with hk (pre-commit validation)
- ✅ GitHub Actions CI workflow with local testing via act
- ✅ Zero warnings policy enforcement (ruff + ty)
- ✅ Complete bootstrap command for CI/fresh machines
- ✅ Organization management (create org, list users)
- ✅ Study management (CRUD operations with org-level access control)
- ✅ Interview guide management (markdown-based guides for studies)
- ✅ Firebase Auth integration with multi-tenancy
- ✅ Google Cloud SQL deployment with automatic migrations
- ✅ Infrastructure as Code with Pulumi (Cloud SQL, Cloud Run, VPC, Secrets)
- ✅ CI/CD for infrastructure via GitHub Actions
- ✅ Workload Identity Federation (no JSON keys)

### In Progress
- 🔄 Infrastructure deployment to GCP (Pulumi setup complete, awaiting bootstrap)

### API Specification
The `openapi.yaml` file defines:
- Authentication using Firebase JWT tokens with bearer auth
- Two tenant types: `organization` and `interviewee`
- Self-led interviews with unique access tokens (no auth required)
- Organization endpoints for interview link generation and management
- Public endpoints for interviewee access to interviews
- Role-based access with roles: owner|admin|member

### Infrastructure

**Local Development** (`docker-compose.yml`):
- PostgreSQL 16 (port 5432)
- MinIO object storage (ports 9000/9001)
- Firebase Auth emulator (port 9099)

**Production** (Pulumi-managed GCP resources):
- Cloud SQL PostgreSQL 16 (private IP, automated backups)
- Cloud Run service (backend API, auto-scaling)
- VPC with private networking
- Secret Manager (database credentials, API keys)
- Service accounts with least-privilege IAM
- Workload Identity Federation for GitHub Actions

See `/infra/README.md` for deployment instructions.

### Infrastructure as Code

**Bootstrap (one-time, manual):**
```bash
# Set GitHub repo for Workload Identity
export GITHUB_REPO="username/verity"

# Run bootstrap script
./scripts/bootstrap-gcp-pulumi.sh
```

**Local Preview (read-only):**
```bash
cd infra
mise exec -- pulumi preview  # View planned changes
```

**Deploy (CI only):**
- Go to Actions → Deploy Infrastructure workflow
- Select stack (dev/prod) and action (preview/up)
- Manual approval required for `up`

### Documentation Structure
- `/docs/001-overview/` - MVP information architecture and UXR project details
- `/docs/002-architecture/` - Technical architecture decisions and patterns
- `/docs/003-plans/` - Implementation plans and roadmaps
  - `/docs/003-plans/002-infrastructure-as-code/` - IaC design decisions
