<!--
Sync Impact Report:
Version: 1.2.0 → 1.3.0 (MINOR - added E2E error testing guidance)
Modified Principles:
  - Testing Strategy section expanded with network-level error mocking guidance
Added Sections:
  - E2E Error Testing subsection under Testing Strategy
Removed Sections: N/A
Templates Requiring Updates:
  ✅ plan-template.md - Constitution Check compatible (no changes needed)
  ✅ spec-template.md - No changes needed (user scenarios unaffected)
  ✅ tasks-template.md - Test task patterns align with error testing principle
Follow-up TODOs: None
-->

# Verity Platform Constitution

## Core Principles

### I. BDD-First Development (NON-NEGOTIABLE)

**MUST** write BDD tests before implementation. The development cycle is:
1. Write Gherkin scenarios in `tests/features/*.feature`
2. Run tests to confirm they fail
3. Implement minimal code to pass tests
4. Run tests to confirm success
5. Refactor while keeping tests green

**Rationale**: Tests define the contract, prevent regressions, and serve as executable documentation. This is the foundation of quality in the Verity platform.

### II. Zero Warnings Policy (NON-NEGOTIABLE)

All code **MUST** pass these checks with zero warnings or errors:
- `ruff format .` - Code formatting
- `ruff check .` - Comprehensive linting with type annotation rules
- `ty src` - Static type checking in strict mode

All functions **MUST** have:
- Return type annotations
- Parameter type annotations
- No `Any` types except when absolutely necessary with explicit justification

**Rationale**: Type safety catches bugs at development time, not runtime. Clean code is maintainable code.

### III. Multi-Tenancy Security (NON-NEGOTIABLE)

**Golden Rule**: Never trust client-provided tenant context (headers, query params, request body fields).

Every multi-tenant endpoint **MUST**:
1. Extract user identity from JWT token (server-side)
2. Verify user belongs to target organization via database lookup
3. Include cross-organization access denial tests (403 responses)

**Rationale**: Security vulnerabilities in multi-tenant systems can expose all customer data. Server-side authorization is mandatory. See `/docs/002-architecture/004-security-guidelines.md` for implementation patterns.

### IV. Transparent Tool Management

Developers use `make` commands; mise manages tool versions invisibly.

Standard commands **MUST** work across all environments:
- `make bootstrap` - Complete setup (CI/fresh machines)
- `make dev` - Start development server
- `make test` - Run full test suite
- `make check` - Run all quality checks (format + lint + types)

**Rationale**: Consistent developer experience across machines and CI. No "works on my machine" problems.

### V. Outside-In Development

Build features from the user-facing layer inward, creating only what's needed to satisfy user requirements.

Start with user behavior (BDD scenarios), work inward through UI/API to implementation. Each feature **MUST**:
- Begin with user-facing BDD tests
- Build minimal implementation to pass tests
- Be independently deployable
- Meet all quality gates

**Rationale**: Building from user needs prevents over-engineering and ensures every line of code delivers user value.

### VI. Deployment-Complete Commits

Commits are not complete until successfully deployed to the target environment.

When pushing commits, agents **MUST**:
- Push changes to repository
- Monitor CI/CD pipeline execution
- Verify successful deployment
- Confirm deployment health checks pass

**Rationale**: Deployment failures caught immediately prevent broken production states and enable rapid feedback.

### VII. Infrastructure as Code

All infrastructure changes **MUST** go through GitHub Actions CI/CD.

Local infrastructure operations are **read-only** (preview only). Deployment requires:
- Pulumi configuration in `infra/`
- GitHub Actions workflow approval
- Workload Identity Federation (no JSON keys)

**Rationale**: Reproducible infrastructure, audit trail, and security (no local credentials).

### VIII. Observability & Debugging

All operations **MUST** be observable through:
- Structured logging with context (user, org, request ID)
- Clear error messages with actionable guidance
- Text-based protocols (stdin/stdout) for CLI tools

**Rationale**: Debug-ability is critical for production operations and incident response.

### IX. Stub Services Over Mocking

When testing code that depends on external services, **PREFER** stub services over code-level mocking.

Implementation requirements:
- Stub services **MUST** conform to the real API contract
- Stub services **MUST** respond over TCP (HTTP/gRPC/etc.)
- Stub services **MUST** support dynamic port allocation for parallel test execution
- Test fixtures **MUST** manage stub lifecycle (auto start/stop)

**Rationale**: Stub services provide superior test realism by exercising the full network stack, serialization, and client code paths. They enable true parallel test execution without port conflicts and catch integration issues that mocks miss (e.g., serialization errors, HTTP header handling, timeout behavior).

**Examples**:
- Firebase Auth: `scripts/firebase_auth_stub.py` (JWT token generation, user management)
- LLM API: `scripts/llm_stub.py` (Claude API-compatible endpoint)

**When mocking is acceptable**:
- Pure functions with no I/O
- Testing error handling for specific exception types
- Unit tests of business logic isolated from I/O

## Security Requirements

### Authentication & Authorization
- Firebase Auth with JWT tokens (stateless API)
- Two tenant types: `organization` and `interviewee`
- Path-based routes: `/orgs/{org_id}/resources` with server-side permission checks
- Super admin "god-mode" access explicitly handled

### Data Isolation
- PostgreSQL row-level organization filtering
- All queries **MUST** include `org_id` filter matching user's organization
- Cross-organization access attempts **MUST** return 403

### Pre-Deployment Checklist
Before deploying endpoints touching organization-scoped data:
- [ ] User identity from JWT token (not client input)
- [ ] Database lookup verifies user belongs to target organization
- [ ] No client-provided headers/params for authorization
- [ ] Resource queries include org_id filter
- [ ] Tests include cross-org access denial (403)
- [ ] Super admin access explicitly handled

## Development Workflow

### Daily Development Cycle
1. `make dev` - Start local development (services in Docker, Python local)
2. Write BDD feature → Ensure tests fail → Implement → Tests pass
3. `make test` - Run full test suite
4. `make format && make check` - Code quality gates
5. Commit with conventional commit messages
6. Pre-commit hooks enforce quality automatically (via hk)
7. Push to repository and monitor CI/CD until successful deployment

### Testing Strategy (BDD-Driven)

**Current Testing Approach**:
- **Frontend BDD**: Playwright-based behavior tests for UI flows
- **Backend BDD**: pytest-bdd for API behavior and business logic
- BDD tests at both layers express requirements as executable specifications

**External Service Testing**:
- **Stub Services** (PREFERRED): TCP-based API-compatible stubs for external services
  - Firebase Auth stub (`scripts/firebase_auth_stub.py`)
  - LLM API stub (`scripts/llm_stub.py`)
  - Dynamic port allocation for parallel execution
  - Managed by test fixtures (pytest/Playwright)
- **Mocking** (LIMITED USE): Only for pure functions and specific error conditions

**E2E Error Testing**:
When testing error conditions (timeouts, server errors, network failures) in E2E tests, **PREFER** network-level mocking over application-level mocks:

- **Frontend E2E** (Playwright): Use `page.route()` to intercept and control network requests
  - `route.abort('timedout')` - Simulate network timeout
  - `route.fulfill({ status: 500, ... })` - Simulate server errors
  - `route.fulfill({ status: 429, ... })` - Simulate rate limiting
- **Backend E2E** (pytest-bdd): Use stub service response configuration or `monkeypatch` at service boundaries

**Rationale**: Network-level mocking provides superior test realism by exercising the full client error handling path including fetch/retry logic, error message extraction, and UI error states. This catches issues that application-level mocks miss (e.g., timeout detection, network error messages, retry behavior).

**Future Considerations** (not currently implemented):
- **Contract Tests**: OpenAPI spec validation (could add if needed)
- **Unit Tests**: Isolated component tests (could add if needed)

**NOT USED**: Traditional integration tests - BDD tests cover end-to-end flows

### Git Hooks (hk)
Pre-commit hooks **MUST** pass before commit:
- Format checks (`make check-format`)
- Lint checks (`make check-lint`)
- Type checks (`make check-types`)

Pre-push hooks **MUST** pass before push:
- All BDD tests (frontend Playwright + backend pytest-bdd)

### Technology Stack
- **Backend**: Python 3.12, FastAPI, Pydantic, SQLAlchemy
- **Database**: PostgreSQL 16 (Cloud SQL in production)
- **Auth**: Firebase Auth with multi-tenancy
- **Storage**: MinIO (local), GCS (production)
- **Infrastructure**: Pulumi (Python), GCP Cloud Run
- **Testing**: pytest-bdd, Playwright, stub services (FastAPI-based)
- **Quality**: ruff (format/lint), ty (type check), hk (git hooks)
- **CI/CD**: GitHub Actions with act for local testing

## Governance

### Amendment Process
1. Proposed changes documented with rationale
2. Impact assessment on existing templates and workflows
3. Team approval required for MAJOR/MINOR changes
4. PATCH changes (clarifications) may proceed with documentation

### Versioning Policy
Constitution follows semantic versioning:
- **MAJOR**: Backward incompatible governance/principle changes
- **MINOR**: New principles or materially expanded guidance
- **PATCH**: Clarifications, wording, typo fixes

### Compliance Review
All pull requests **MUST** verify compliance with:
- BDD-First Development (tests before code)
- Zero Warnings Policy (all checks pass)
- Multi-Tenancy Security (authorization checks present)
- Code quality standards (ruff + ty clean)
- Testing approach (stub services preferred over mocks)

Complexity that violates simplicity principles **MUST** be justified with:
- Clear business need
- Documentation of why simpler alternatives were rejected
- Approval from technical lead

### Runtime Guidance
For detailed implementation guidance and examples, developers should reference:
- `CLAUDE.md` - Agent-specific development guidance
- `/docs/002-architecture/` - Architecture decision records
- `/docs/002-architecture/004-security-guidelines.md` - Security patterns and anti-patterns
- `/backend/docs/test-isolation.md` - Stub service implementation patterns

**Version**: 1.3.0 | **Ratified**: 2025-10-07 | **Last Amended**: 2025-10-10
