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

- ✅ Self-led interview execution (reusable study links, interview lifecycle, artifact management)

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
- `/specs/002-self-led-interview/` - Self-led interview feature specification and implementation

## Self-Led Interview Feature

The self-led interview feature enables researchers to share reusable study links with participants who complete interviews via an AI interviewer (pipecat).

### Key Models

**Interview Model** (`backend/src/models.py`):
- `access_token` (UUID v4) - Single-use token for interview access
- `status` - Interview state: `pending` or `completed`
- `external_participant_id` - Optional ID from recruitment platforms (e.g., Prolific, Respondent)
- `platform_source` - Recruitment platform identifier (inferred from pid prefix)
- `expires_at` - Token expiration timestamp (default: 7 days)
- `transcript_url`, `recording_url` - GCS URLs for artifacts
- `verity_user_id` - Optional link to VerityUser (for participant claim flow)
- `claimed_at` - Timestamp when participant claimed interview
- `pipecat_session_id` - Pipecat session identifier
- `notes` - Additional metadata from pipecat

**Study Model Extensions**:
- `slug` (String(63), unique) - URL-friendly identifier for reusable links
- `participant_identity_flow` - Identity tracking behavior: `anonymous`, `claim_after`, or `allow_pre_signin`

**VerityUser Model** (for participant identity):
- `firebase_uid` (unique) - Firebase Auth UID for participants
- `email` (unique) - Participant email
- `display_name` - Optional display name
- `created_at`, `last_sign_in` - Timestamps

**ParticipantProfile Model** (for cross-platform tracking):
- `verity_user_id` (unique FK) - Link to VerityUser
- `platform_identities` (JSON) - Map of platform → external_participant_id

### Public Endpoints (No Authentication)

**Study Access** - `GET /study/{slug}/start?pid={PARTICIPANT_ID}`:
- Creates interview on-the-fly with deduplication by `external_participant_id`
- Infers `platform_source` from pid prefix (e.g., `prolific_abc123` → `prolific`)
- Returns 302 redirect to pipecat with `access_token` and `verity_api` parameters
- Returns HTML error page for completed interviews

**Interview Data** - `GET /api/interview/{access_token}`:
- Called by pipecat after participant redirect
- Returns study title and interview guide (markdown) for conducting interview
- Returns 410 Gone if interview completed or token expired
- Returns 404 if interview not found

**Completion Callback** - `POST /api/interview/{access_token}/complete`:
- Called by pipecat after interview completion
- Updates interview status to `completed` and stores artifact URLs
- Idempotent (safe for pipecat to retry)
- Accepts: `transcript_url` (GCS URL), `recording_url` (GCS URL), `notes` (optional metadata)

**Claim Interview** - `POST /api/interview/{access_token}/claim`:
- Called by participants who sign in after completing anonymous interviews
- Links interview to VerityUser via `verity_user_id`
- Updates `platform_identities` in ParticipantProfile
- Requires Firebase Auth with `tenant: "interviewee"` claim

### Authenticated Endpoints (Organization Users)

**List Interviews** - `GET /api/orgs/{org_id}/studies/{study_id}/interviews`:
- Returns completed interviews only with metadata (external_participant_id, platform_source, artifact flags)
- Server-side org verification (multi-tenancy security)

**Download Artifact** - `GET /api/orgs/{org_id}/interviews/{interview_id}/artifacts/{filename}`:
- Streams interview artifacts from GCS (API proxy pattern)
- Supports `transcript.txt` and `recording.wav`
- Server-side org verification (multi-tenancy security)
- Returns StreamingResponse with appropriate Content-Type

### Logging Events

Structured logging is added for all interview lifecycle events:
- `interview_created` - New interview created via reusable link
- `interview_access_existing` - Existing interview found (deduplication)
- `interview_access_denied` - Access denied (completed interview)
- `interview_completed` - Interview marked completed by pipecat
- `interview_completion_idempotent` - Completion callback for already-completed interview
- `interview_claimed` - Interview claimed by participant

All log entries include relevant context: `interview_id`, `study_id`, `study_slug`, `external_participant_id`, `platform_source`, `access_token`, `event`.

### Security Considerations

- **Multi-tenancy**: All authenticated endpoints verify org_id server-side (never trust client)
- **Access tokens**: UUID v4 tokens are cryptographically secure single-use identifiers
- **Artifact access**: Proxied through backend with org-level authorization
- **Token expiration**: Interviews expire after 7 days by default
- **Deduplication**: Same `external_participant_id` cannot create multiple pending interviews

### Integration with Pipecat

1. **Participant clicks reusable link**: `GET /study/{slug}/start?pid={PARTICIPANT_ID}`
2. **Verity creates interview** and redirects to: `{PIPECAT_URL}/?access_token={TOKEN}&verity_api={VERITY_API_BASE}`
3. **Pipecat fetches interview data**: `GET {VERITY_API_BASE}/interview/{TOKEN}`
4. **Pipecat conducts interview** using study title and interview guide
5. **Pipecat uploads artifacts to GCS** and stores URLs
6. **Pipecat notifies completion**: `POST {VERITY_API_BASE}/interview/{TOKEN}/complete` with artifact URLs

### Environment Variables

- `PIPECAT_URL` - Pipecat frontend URL (default: `http://localhost:8080`)
- `VERITY_API_BASE` - Verity API base URL (default: `http://localhost:8000/api`)
- `GCS_BUCKET_NAME` - GCS bucket for interview artifacts (set by Pulumi output)

### Database Indexes

Composite indexes for performance:
- `(study_id, external_participant_id)` - Fast deduplication lookups
- `(study_id, status, completed_at)` - Fast interview list queries

See `/specs/002-self-led-interview/` for complete feature specification, implementation plan, and tasks breakdown.
