# Verity

UXR (User Experience Research) platform for conducting and managing user interviews.

## Project Status

### Phase 1: Core Infrastructure ✅ COMPLETE
- ✅ Backend API with FastAPI
- ✅ PostgreSQL database with Cloud SQL
- ✅ Firebase Auth integration (multi-tenancy: organization + interviewee)
- ✅ MinIO object storage for audio files
- ✅ BDD testing infrastructure (pytest-bdd + Playwright)
- ✅ Git hooks with hk (pre-commit + pre-push validation)
- ✅ GitHub Actions CI/CD
- ✅ Infrastructure as Code with Pulumi
- ✅ Deployment to GCP (Cloud Run + Cloud SQL)

### Phase 2: Organization Management ✅ COMPLETE
- ✅ Super admin can create organizations
- ✅ Organization users (owner/admin/member roles)
- ✅ Cross-organization security isolation
- ✅ Study management (CRUD with org-level access control)
- ✅ Interview guide management (markdown-based)
- ✅ Interview link generation
- ✅ Audio recording upload/download
- ✅ Transcript finalization with segments
- ✅ Multi-tenancy security audit and fixes (server-side authorization)

### Phase 3: Study Management UI 🚧 IN PROGRESS
**Next task**: Build frontend UI for study management
- 🚧 Study list page
- 🚧 Create/edit study flow
- 🚧 Study detail page
- ⏳ Interview guide editor
- ⏳ Interview session management UI

### Phase 4: Interview Experience (Future)
- ⏳ Interviewee self-led interview flow
- ⏳ Audio recording in browser
- ⏳ Real-time transcription
- ⏳ AI-powered interview insights

## Recent Work

### Security Fix (Oct 5, 2025)
- **Critical vulnerability**: Fixed multi-tenancy security issue where client-controlled `X-Organization-ID` header allowed cross-org data access
- **Solution**: Changed routes from `/studies` to `/orgs/{org_id}/studies` with server-side permission verification
- **Documentation**: Added comprehensive security guidelines in `docs/002-architecture/004-security-guidelines.md`
- **Testing**: All 107 backend tests + 14 frontend E2E tests passing

### CI/CD Optimization (Oct 5, 2025)
- Merged 3 deployment jobs into 1 (deploy-infra + deploy-infra-run + deploy → single deploy job)
- Pulumi now runs `pulumi up` directly (decides what to change)
- Removed mise from deploy job (was breaking gcloud)
- Faster deployments, simpler workflow

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development instructions including:
- Tool management (mise, uv, make)
- BDD-first workflow
- Code quality standards
- Git hooks and CI/CD

## Quick Start

```bash
# One-time setup
make bootstrap

# Start backend dev server
make backend-dev

# Run tests
make backend-test
make frontend-test

# Code quality
make backend-check
make frontend-check
```

## Architecture

- **Backend**: FastAPI + PostgreSQL + Firebase Auth
- **Frontend**: React + TypeScript + Vite + Playwright
- **Infrastructure**: Pulumi (GCP Cloud Run + Cloud SQL)
- **Testing**: pytest-bdd + Playwright (BDD approach)
- **CI/CD**: GitHub Actions with workload identity federation