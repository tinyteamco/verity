# Implementation Plan: Self-Led Interview Execution

**Branch**: `002-self-led-interview` | **Date**: 2025-10-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-self-led-interview/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature enables researchers to create reusable study links that participants can access to complete voice-based interviews powered by pipecat-momtest. The system automatically creates interview records on-the-fly, redirects participants to the interview interface, and collects artifacts (audio recordings and transcripts) in a shared GCS bucket. Researchers can view completed interviews and access artifacts through the Verity UI. Optional participant identity features support recruitment platform integration (external participant IDs) and cross-platform profile tracking (participant sign-in and claim flows).

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
- Pipecat Integration: NEEDS CLARIFICATION (webhook URL format, CORS requirements, session token lifetime)
- Participant Identity Flows: NEEDS CLARIFICATION (Firebase Auth patterns for optional sign-in, profile dashboard design)
- Shared GCS Bucket IAM: NEEDS CLARIFICATION (service account configuration, IAM roles for pipecat-momtest)

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

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

No violations - all constitution requirements satisfied.
