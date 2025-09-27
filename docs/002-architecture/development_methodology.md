# Development Methodology

This document captures the development workflow and architectural decisions made for the Verity UXR platform.

## Development Philosophy

### BDD (Behavior-Driven Development)
- **Test-First**: Write BDD scenarios before implementation
- **Outside-In**: Start with user behavior, work inward to implementation
- **Living Documentation**: Features files serve as executable documentation

### Inside-Out Architecture
- **Thin Vertical Slices**: Each feature cuts through all layers (API → DB → Tests)
- **Incremental Complexity**: Start simple (health check), add complexity gradually
- **Infrastructure-First**: Ensure testing/deployment pipeline works before adding features

## Tool Chain & Environment

### Core Tools
- **mise**: Tool version management (Python, Node, CLI tools)
- **uv**: Python package management (10-100x faster than pip)
- **make**: Standard interface for all commands
- **Docker**: Containerization for services and deployment

### Design Principles
1. **Transparent Tool Management**: Developers use `make`, mise works invisibly
2. **Reproducible Environments**: Exact tool versions via mise + uv.lock
3. **Standard Interfaces**: `make dev`, `make test` work for any developer/agent
4. **Local Development Speed**: Python runs locally, services in containers

## Project Structure Decisions

### Monorepo Layout
```
verity/
├── backend/           # Python FastAPI service
├── frontend/          # Future React/Next.js app
├── e2e/              # Future full-stack tests
└── docs/             # Architecture documentation
```

**Rationale**: Single repo simplifies coordination between frontend/backend, easier CI/CD

### Backend Structure: src/tests
```
backend/
├── src/              # Source code (not backend/ or app/)
│   └── api/
└── tests/            # BDD tests
    ├── features/     # Gherkin scenarios
    └── step_defs/    # Step implementations
```

**Rationale**: Clear separation, industry standard, works with hatchling packaging

## Development Workflow

### Daily Development
1. `make dev` - Start local development (services in Docker, Python local)
2. Write BDD feature → Implement → Test
3. `make test` - Run full test suite
4. `make format && make lint` - Code quality
5. Commit with conventional commit messages

### Testing Strategy
- **Unit Tests**: Fast, isolated component tests
- **BDD Tests**: Behavior scenarios with pytest-bdd
- **Integration Tests**: Full API → DB → Storage flows
- **Contract Tests**: OpenAPI spec validation

### Deployment Strategy
- **Target**: Google Cloud Run (serverless containers)
- **Philosophy**: What runs locally runs in prod
- **CI/CD**: Container-based builds, BDD tests must pass

## Architecture Decisions

### 1. FastAPI + Pydantic
**Decision**: Use FastAPI with Pydantic models
**Rationale**:
- Auto-generated OpenAPI docs
- Type safety with Python 3.12
- High performance async/await
- Great DX with hot reload

### 2. Firebase Auth with Tenants
**Decision**: Firebase Auth with separate company/interviewee tenants
**Rationale**:
- Managed auth service (Google reliability)
- Built-in tenant isolation
- JWT tokens for stateless API
- Local emulator for development

### 3. PostgreSQL + MinIO
**Decision**: PostgreSQL for relational data, MinIO for object storage
**Rationale**:
- PostgreSQL: ACID compliance, JSON support, mature ecosystem
- MinIO: S3-compatible, runs locally, cloud-agnostic

### 4. BDD with pytest-bdd
**Decision**: pytest-bdd over alternatives (behave, cucumber)
**Rationale**:
- Integrates with existing pytest ecosystem
- Better Python tooling integration
- Shared fixtures with unit tests

## Next Implementation Steps

Based on the BDD features in `/docs/003-plans/001-initial-plan/features/`:

1. **Company Studies** - Create/list/update studies (next logical feature)
2. **Auth & Roles** - Firebase integration + RBAC
3. **Share Links** - Study invitation system
4. **Recordings & Transcripts** - File upload + processing
5. **Summaries** - AI-powered content generation

Each feature follows the pattern:
1. Write BDD scenario
2. Implement minimal API endpoint
3. Add database layer
4. Integrate external services (Firebase, MinIO)
5. End-to-end test passing

## Future Considerations

### Scaling Decisions Deferred
- Database sharding/read replicas
- CDN for static assets
- Background job processing (Redis/Celery)
- Advanced monitoring/observability

### Technology Choices Revisited
- When to introduce React frontend
- GraphQL vs REST for complex queries
- AI/ML pipeline architecture
- Multi-region deployment strategy

---

*This document should be updated as architectural decisions evolve.*