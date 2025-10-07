# Implementation Plan: Study Management UI

**Branch**: `001-study-management-ui` | **Date**: 2025-10-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-study-management-ui/spec.md`

## Summary

Add frontend UI for automated study creation and interview guide editing. Users will be able to describe what they want to learn, receive a generated study with interview guide, and edit the guide content. This connects existing backend generation endpoints to a new frontend workflow, replacing manual study creation as the primary path.

## Technical Context

**Language/Version**: TypeScript 5.6, React 18.3, Python 3.12 (backend already complete)
**Primary Dependencies**:
- Frontend: React, Vite, Tanstack Router, Tailwind CSS, Radix UI, Playwright (BDD)
- Backend: FastAPI, Pydantic, SQLAlchemy (existing - no changes needed)
**Storage**: PostgreSQL 16 (existing Study + InterviewGuide tables)
**Testing**: Playwright + playwright-bdd for frontend E2E tests (Gherkin scenarios)
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend + backend monorepo)
**Performance Goals**:
- Study generation response <60s
- Page loads <3s
- Preview rendering <2s
**Constraints**:
- Prefer using existing backend endpoints, but can modify if needed
- Must follow BDD-first workflow (Gherkin → implement)
- Must pass ruff/ty checks (frontend TypeScript strict + backend ruff/ty)
**Scale/Scope**: Small feature - 2-3 new pages, ~5-8 Gherkin scenarios

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. BDD-First Development ✅ PASS
- **Requirement**: Write Gherkin scenarios before implementation
- **Plan**: Will create Gherkin scenarios in `frontend/tests/features/study-generation.feature` before any code
- **Compliance**: Spec already has acceptance scenarios that map to Gherkin

### II. Zero Warnings Policy ✅ PASS
- **Requirement**: TypeScript strict mode, no warnings
- **Plan**: Frontend already configured with TypeScript 5.6 strict mode
- **Compliance**: `tsc` will be run as part of build/check process

### III. Multi-Tenancy Security ✅ PASS
- **Requirement**: Server-side authorization, cross-org denial tests
- **Plan**: Backend already handles multi-tenancy correctly (verified in spec context)
- **Compliance**: Frontend just calls existing secure endpoints, no auth logic changes

### IV. Transparent Tool Management ✅ PASS
- **Requirement**: Use `make` commands
- **Plan**: Will use `make frontend-dev`, `make frontend-test`, `make frontend-check`
- **Compliance**: Existing Makefile already has these targets

### V. Outside-In Development ✅ PASS
- **Requirement**: Start with user-facing BDD tests, work inward
- **Plan**: Write Gherkin for UI flow → implement pages → verify tests pass
- **Compliance**: This is frontend-only work, starts at user-facing layer

### VI. Deployment-Complete Commits ✅ PASS
- **Requirement**: Monitor CI/CD until deployment succeeds
- **Plan**: Will push and verify GitHub Actions deployment completes
- **Compliance**: Standard workflow, no exceptions

### VII. Infrastructure as Code ⚠️ N/A
- **Requirement**: Infrastructure changes via Pulumi
- **Note**: No infrastructure changes needed, frontend code only

### VIII. Observability & Debugging ✅ PASS
- **Requirement**: Clear error messages, logging
- **Plan**: Will show clear error messages for generation failures, save failures
- **Compliance**: Error handling specified in spec edge cases

**GATE RESULT**: ✅ **ALL APPLICABLE PRINCIPLES PASS** - Proceed to Phase 0

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
frontend/
├── src/
│   ├── pages/
│   │   ├── StudyListPage.tsx          # Existing - will add "Generate Study" button
│   │   ├── StudyDetailPage.tsx        # Existing - will add guide display + edit
│   │   └── StudyGeneratePage.tsx      # NEW - topic input → generation flow
│   ├── components/
│   │   ├── ui/                        # Existing Radix UI components
│   │   ├── StudyGuideEditor.tsx       # NEW - markdown editor with preview
│   │   └── StudyGuideViewer.tsx       # NEW - rendered markdown display
│   └── lib/
│       └── api.ts                     # Existing - will add generation endpoint calls
└── tests/
    └── features/
        ├── study-management.feature   # Existing - 5 scenarios passing
        └── study-generation.feature   # NEW - automated creation + guide editing

backend/
├── src/
│   └── api/
│       └── main.py                    # Existing - NO CHANGES (endpoints exist)
└── tests/
    └── features/
        └── study_guides.feature       # Existing - backend generation tests passing
```

**Structure Decision**: Web application (monorepo). Frontend changes only - backend endpoints already exist and are tested. Will add 2-3 new React components and 1 new BDD feature file.

## Complexity Tracking

*No complexity violations - all constitution principles satisfied.*
