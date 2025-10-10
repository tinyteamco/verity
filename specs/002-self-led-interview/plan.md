# Implementation Plan: Self-Led Interview Execution

**Branch**: `002-self-led-interview` | **Date**: 2025-10-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-self-led-interview/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature enables researchers to create reusable study links that participants can access to complete voice-based interviews powered by pipecat-momtest. The system automatically creates interview records on-the-fly, redirects participants to the interview interface, and collects artifacts (audio recordings and transcripts) in a shared GCS bucket. Researchers can view completed interviews and access artifacts through the Verity UI. Optional participant identity features support recruitment platform integration (external participant IDs) and cross-platform profile tracking (participant sign-in and claim flows).

## For Developers

**Starting implementation?** Follow this sequence:

1. **Read specifications**: [spec.md](./spec.md) - Understand requirements and user stories
2. **Review technical decisions**: [research.md](./research.md) - Key design choices (pipecat integration, Firebase Auth, GCS IAM)
3. **Understand data model**: [data-model.md](./data-model.md) - Database schema (Interview, VerityUser, ParticipantProfile models)
4. **Check API contracts**: [contracts/](./contracts/) - OpenAPI specs for 7 new endpoints
5. **Follow implementation guide**: [quickstart.md](./quickstart.md) - Step-by-step phases with BDD tests and code examples

**TL;DR**: Most developers should start with **[quickstart.md](./quickstart.md) Phase 1 (Infrastructure)** and follow the phases sequentially.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/React (frontend)

**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy, Pydantic, Firebase Admin SDK, google-cloud-storage, Pulumi (Python)
- Frontend: React, TypeScript, Vite, Playwright (E2E testing)

**Storage**: PostgreSQL 16 (Cloud SQL), Google Cloud Storage (shared bucket for artifacts), MinIO (local dev)

**Testing**: pytest-bdd (backend BDD), Playwright (frontend E2E), stub services (Firebase Auth, LLM)

**Target Platform**: GCP Cloud Run (backend), static hosting (frontend), containerized deployment

**Project Type**: Web application (FastAPI backend + React frontend)

**Performance Goals**: <1s API response time for interview creation, support dozens to hundreds of concurrent participants

**Constraints**:
- MVP-First: Build for current scale (dozens of researchers, hundreds of participants per study)
- API proxy pattern for artifact streaming (simpler than signed URLs for MVP)
- CORS support for public endpoints (pipecat integration)
- Multi-tenancy security (server-side org_id validation)

**Scale/Scope**:
- Organizations: 10-100 research teams
- Studies: 10-100 per organization
- Interviews: Hundreds to thousands per study
- Artifacts: Audio files (up to 100MB each), transcripts (text)

**Technical Decisions** (all resolved - see [research.md](./research.md)):
- **Pipecat Integration**: POST callback to `/interview/{access_token}/complete`, CORS for pipecat domain, 24-hour token lifetime ([research.md § 1](./research.md#1-pipecat-integration))
- **Participant Identity**: Progressive authentication (anonymous → claim → authenticated), VerityUser model separate from Organization users ([research.md § 2](./research.md#2-participant-identity-flows))
- **Shared GCS Bucket IAM**: Pulumi-managed bucket, Verity (Object Admin), Pipecat (Object Creator) ([research.md § 3](./research.md#3-shared-gcs-bucket-iam))

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. BDD-First Development ✅
- **Requirement**: Write Gherkin scenarios before implementation
- **Status**: PASS - Feature specification includes 9 user stories with Given/When/Then acceptance scenarios
- **Action**: Write BDD tests in `backend/tests/features/` and `frontend/tests/features/` before implementation

### II. Zero Warnings Policy ✅
- **Requirement**: All code passes ruff format, ruff check, ty with zero warnings
- **Status**: PASS - Existing project has this enforced via make commands and pre-commit hooks
- **Action**: Continue using existing quality checks

### III. Multi-Tenancy Security ✅
- **Requirement**: Server-side JWT validation, org_id verification, cross-org access denial tests
- **Status**: PASS - Feature includes FR-022 (JWT validation), FR-023 (org-level access control), FR-024 (public endpoint security)
- **Action**: Implement server-side authorization for researcher endpoints, write 403 denial tests

### IV. Transparent Tool Management ✅
- **Requirement**: mise + make workflow
- **Status**: PASS - Existing project uses mise/make/uv
- **Action**: No changes needed

### V. Outside-In Development ✅
- **Requirement**: Start with user-facing BDD tests, build inward
- **Status**: PASS - Will follow BDD-first workflow
- **Action**: Write user scenarios first, implement minimal code to pass tests

### VI. Deployment-Complete Commits ✅
- **Requirement**: Monitor CI/CD until successful deployment
- **Status**: PASS - Existing GitHub Actions workflows
- **Action**: Verify deployments after pushing commits

### VII. Infrastructure as Code ✅
- **Requirement**: All infrastructure via Pulumi + GitHub Actions
- **Status**: PASS - FR-001 requires shared GCS bucket via Pulumi
- **Action**: Add GCS bucket + IAM configuration to `infra/__main__.py`

### VIII. Observability & Debugging ✅
- **Requirement**: Structured logging, clear error messages
- **Status**: PASS - Existing FastAPI logging
- **Action**: Add contextual logging for interview lifecycle events

### IX. Stub Services Over Mocking ✅
- **Requirement**: Use TCP-based stub services for external dependencies
- **Status**: PASS - Existing Firebase Auth stub, LLM stub
- **Action**: No new external services requiring stubs

### X. MVP-First Development ✅
- **Requirement**: Build for current scale, defer optimization
- **Status**: PASS - Feature explicitly defers webhooks, pre-generated links, UI filtering
- **Action**: Use API proxy pattern (not signed URLs), defer advanced features

**GATE RESULT**: ✅ PASS - All constitution requirements satisfied

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
verity/
├── backend/
│   ├── src/
│   │   └── api/
│   │       ├── main.py                    # FastAPI app (add CORS middleware)
│   │       ├── models/
│   │       │   ├── interview.py           # NEW: Interview model
│   │       │   ├── verity_user.py         # NEW: VerityUser model (participant identity)
│   │       │   └── study.py               # MODIFY: Add slug, participant_identity_flow
│   │       ├── routers/
│   │       │   ├── interviews.py          # NEW: Public interview endpoints
│   │       │   ├── org_interviews.py      # NEW: Researcher interview management
│   │       │   └── participant_profile.py # NEW: Participant profile/claim endpoints
│   │       ├── services/
│   │       │   ├── gcs_service.py         # NEW: GCS artifact operations
│   │       │   ├── interview_service.py   # NEW: Interview lifecycle logic
│   │       │   └── auth_service.py        # MODIFY: Add VerityUser creation
│   │       └── dependencies.py            # MODIFY: Add optional auth dependency
│   └── tests/
│       └── features/
│           ├── interview_access.feature       # NEW: Reusable links + on-the-fly creation
│           ├── interview_completion.feature   # NEW: Pipecat callback
│           ├── artifact_management.feature    # NEW: Audio/transcript streaming
│           ├── participant_identity.feature   # NEW: Sign-in + claim flows
│           └── step_defs/                     # NEW: Step implementations
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── InterviewList.tsx          # NEW: Display interviews with artifacts
│   │   │   ├── InterviewDetail.tsx        # NEW: Transcript inline, audio download
│   │   │   ├── StudySettings.tsx          # NEW: Reusable link template display
│   │   │   ├── ParticipantInterstitial.tsx # NEW: Pre-interview sign-in page
│   │   │   ├── ThankYouPage.tsx           # NEW: Post-interview claim flow
│   │   │   └── ParticipantDashboard.tsx   # NEW: Participant profile view
│   │   ├── pages/
│   │   │   ├── StudySettingsPage.tsx      # NEW: Study settings page
│   │   │   ├── InterviewsPage.tsx         # NEW: Interview list page
│   │   │   └── ParticipantProfilePage.tsx # NEW: Participant profile page
│   │   └── api/
│   │       └── interviews.ts              # NEW: API client for interview endpoints
│   └── tests/
│       └── features/
│           ├── study_settings.feature         # NEW: Reusable link display
│           ├── interview_list.feature         # NEW: View interviews + artifacts
│           └── participant_flows.feature      # NEW: Sign-in + claim E2E tests
│
└── infra/
    ├── __main__.py                        # MODIFY: Add GCS bucket + IAM
    └── README.md                          # MODIFY: Document bucket setup
```

**Structure Decision**: Web application (existing monorepo structure). This feature adds new models, routers, services, and UI components to the existing backend/frontend directories. Infrastructure changes are isolated to the `infra/` directory (Pulumi configuration).

## Implementation Roadmap

This section provides a high-level overview of implementation phases. For detailed step-by-step instructions with code examples, see **[quickstart.md](./quickstart.md)**.

### Phase 1: Infrastructure (~2 hours)

**Deliverables**: Shared GCS bucket for interview artifacts with IAM role bindings

**References**:
- [quickstart.md § Phase 1](./quickstart.md#phase-1-infrastructure-pulumi)
- [research.md § GCS Bucket IAM](./research.md#3-shared-gcs-bucket-iam)

**Key Tasks**:
- Create GCS bucket via Pulumi (`infra/__main__.py`)
- Configure IAM roles: Verity (Object Admin), Pipecat (Object Creator)
- Deploy via GitHub Actions
- Configure backend environment variables

**Dependencies**: None (can start immediately)

---

### Phase 2: Database Models (~3 hours)

**Deliverables**: Interview, VerityUser, ParticipantProfile models + Study modifications + Alembic migration

**References**:
- [data-model.md](./data-model.md) - Complete schema definitions
- [quickstart.md § Phase 2](./quickstart.md#phase-2-database-models-backend)

**Key Tasks**:
- Modify Study model (add `slug`, `participant_identity_flow`)
- Create Interview model (access token, status, timestamps, external IDs)
- Create VerityUser model (Firebase UID, email, participant identity)
- Create ParticipantProfile model (platform identities JSON, stats)
- Generate and run Alembic migration
- Write BDD tests for model validations

**Dependencies**: Phase 1 (GCS bucket for artifact URLs)

---

### Phase 3: Backend API - Public Interview Access (~4 hours)

**Deliverables**: 3 public endpoints (no authentication required)

**References**:
- [contracts/api-endpoints.yaml](./contracts/api-endpoints.yaml) - OpenAPI specs
- [quickstart.md § Phase 3](./quickstart.md#phase-3-backend-api-endpoints)
- [research.md § Pipecat Integration Flow](./research.md#14-integration-flow)

**Endpoints**:
- `GET /study/{slug}/start?pid={external_id}` - Reusable link access (creates interview on-the-fly)
- `GET /interview/{access_token}` - Pipecat fetches interview guide
- `POST /interview/{access_token}/complete` - Pipecat completion callback

**Key Tasks**:
- Write BDD tests (`backend/tests/features/interview_access.feature`, `interview_completion.feature`)
- Implement `routers/interviews.py`
- Add CORS configuration for pipecat domain
- Test integration flow end-to-end

**Dependencies**: Phase 2 (Interview model)

---

### Phase 4: Backend API - Participant Identity (~4 hours) **(P2 - Optional for MVP)**

**Deliverables**: 2 participant endpoints (Firebase Auth required)

**Note**: This phase implements P2/P3 user stories (US7-US9: participant identity and dashboard). Can be deferred to second iteration after validating core P1 flow (US1-US2: reusable links + researcher artifact access). Researchers can already track interviews by `external_participant_id` from recruitment platforms without participant sign-in.

**References**:
- [contracts/api-endpoints.yaml](./contracts/api-endpoints.yaml) - OpenAPI specs
- [quickstart.md § Phase 4](./quickstart.md#phase-4-participant-identity-endpoints)
- [research.md § Participant Identity](./research.md#2-participant-identity-flows)
- [data-model.md § Claim Flow](./data-model.md#flow-3-post-interview-claim)

**Endpoints**:
- `POST /interview/{access_token}/claim` - Link interview to VerityUser
- `GET /api/participant/dashboard` - View interview history

**Key Tasks**:
- Write BDD tests (`backend/tests/features/participant_identity.feature`)
- Implement `routers/participant_profile.py`
- Implement Firebase Auth dependency for participants
- Create VerityUser + ParticipantProfile on first sign-in
- Update platform_identities JSON on claim

**Dependencies**: Phase 3 (completed interviews to claim)

---

### Phase 5: Backend API - Researcher Endpoints (~4 hours)

**Deliverables**: 2 researcher endpoints (Firebase Auth + org-level authorization)

**References**:
- [contracts/api-endpoints.yaml](./contracts/api-endpoints.yaml) - OpenAPI specs
- [quickstart.md § Phase 5](./quickstart.md#phase-5-researcher-endpoints--artifact-proxy)
- [data-model.md § Researcher Views Artifacts](./data-model.md#flow-4-researcher-views-interview-artifacts)

**Endpoints**:
- `GET /api/orgs/{org_id}/studies/{study_id}/interviews` - List interviews
- `GET /api/orgs/{org_id}/interviews/{interview_id}/artifacts/{filename}` - Download artifacts (API proxy pattern)

**Key Tasks**:
- Write BDD tests (`backend/tests/features/artifact_management.feature`)
- Implement `routers/org_interviews.py`
- Implement `services/gcs_service.py` (stream artifacts from GCS)
- Write 403 denial tests (cross-org access attempts)

**Dependencies**: Phase 3 (interviews with artifacts)

---

### Phase 6: Frontend UI - Study Settings (~3 hours)

**Deliverables**: Reusable link template display

**References**:
- [quickstart.md § Phase 6](./quickstart.md#phase-6-frontend-ui-components)

**Key Tasks**:
- Write E2E tests (`frontend/tests/features/study_settings.feature`)
- Implement StudySettings component (display link template with copy button)
- Implement StudySettingsPage
- Add recruitment platform usage instructions

**Dependencies**: Phase 2 (Study.slug field)

---

### Phase 7: Frontend UI - Interview List & Artifacts (~4 hours)

**Deliverables**: Researcher views interviews and downloads artifacts

**References**:
- [quickstart.md § Phase 6](./quickstart.md#phase-6-frontend-ui-components)

**Key Tasks**:
- Write E2E tests (`frontend/tests/features/interview_list.feature`)
- Implement API client (`api/interviews.ts`)
- Implement InterviewList component (display interviews with metadata)
- Implement InterviewDetail component (transcript inline, audio download)
- Implement InterviewsPage

**Dependencies**: Phase 5 (researcher endpoints)

---

### Phase 8: Frontend UI - Participant Flows (~3 hours) **(P2 - Optional for MVP)**

**Deliverables**: Participant sign-in and claim flows

**Note**: This phase implements P2/P3 user stories (participant-facing UI). Can be deferred to second iteration. Depends on Phase 4 (participant endpoints).

**References**:
- [quickstart.md § Phase 6](./quickstart.md#phase-6-frontend-ui-components)
- [research.md § Claim Flow](./research.md#23-claim-flow-implementation)

**Key Tasks**:
- Write E2E tests (`frontend/tests/features/participant_flows.feature`)
- Implement ParticipantInterstitial component (pre-interview sign-in)
- Implement ThankYouPage component (post-interview claim button)
- Implement ParticipantDashboard component (interview history)
- Implement ParticipantProfilePage

**Dependencies**: Phase 4 (participant endpoints)

---

### Implementation Dependencies (Visual)

```
Phase 1: Infrastructure
    ↓
Phase 2: Database Models
    ↓
    ├─→ Phase 3: Public Interview Access → Phase 6: Study Settings (Frontend)
    │       ↓
    │   Phase 4: Participant Identity → Phase 8: Participant Flows (Frontend)
    │
    └─→ Phase 5: Researcher Endpoints → Phase 7: Interview List (Frontend)
```

**Critical Path**: Phases 1 → 2 → 3 → 5 → 7 (core researcher workflow - MVP P1)
**Optional Phases**: Phases 4, 8 (participant identity - P2, can defer to second iteration)
**Parallel Work**: After Phase 2, Phases 3-5 can be developed in parallel by different developers

---

### Total Effort Estimate

**MVP P1 (Core Researcher Flow)**:
- **Backend**: ~13 hours (Phases 1, 2, 3, 5)
- **Frontend**: ~7 hours (Phases 6, 7)
- **P1 Total**: ~20 hours

**P2 (Participant Identity - Optional)**:
- **Backend**: ~4 hours (Phase 4)
- **Frontend**: ~3 hours (Phase 8)
- **P2 Total**: ~7 hours

**Complete Feature Total**: ~27 hours (P1 + P2, excluding testing time, code review)

**Note**: These are implementation estimates only. Add time for:
- BDD test writing (included in phase estimates)
- Code review and revisions
- Integration testing
- Documentation updates

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

No violations - all constitution requirements satisfied.
