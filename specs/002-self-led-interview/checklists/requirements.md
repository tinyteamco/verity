# Specification Quality Checklist: Self-Led Interview Execution

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2025-10-10
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Validation Results

### ✅ All Items Passed

**Content Quality**: Specification focuses on user needs and business value. No technical implementation details (frameworks, databases, etc.). Written in plain language suitable for stakeholders.

**Requirements**: 46 functional requirements (FR-001 through FR-046), all testable and unambiguous. No [NEEDS CLARIFICATION] markers - all decisions made using industry standards, existing backend implementation, pipecat-momtest codebase analysis, and recruitment platform integration patterns.

Requirement categories:
- Infrastructure: FR-001 (1 requirement - shared GCS bucket via Pulumi)
- Participant Access (Reusable Links): FR-002 to FR-005 (4 requirements)
- Interview Completion (Callback): FR-006 to FR-010 (5 requirements)
- Artifact Management: FR-011 to FR-014 (4 requirements)
- Interview Tracking: FR-015 to FR-018 (4 requirements)
- Optional Participant Sign-In: FR-019 to FR-021 (3 requirements)
- Security & Privacy: FR-022 to FR-024 (3 requirements)
- Pipecat Integration: FR-025 to FR-031 (7 requirements)
- Recruitment Platform (On-the-Fly): FR-032 to FR-036 (5 requirements)
- Participant Identity & Sign-In: FR-037 to FR-046 (10 requirements)

**Success Criteria**: 3 core measurable outcomes (removed speculative timing targets and aspirational metrics):
- Automatic artifact upload (proves pipecat integration works)
- Researchers can view artifacts (proves results collection works)
- On-the-fly interview creation (proves architecture works)

**Acceptance Scenarios**: 9 user stories with complete Given/When/Then scenarios. Each story is independently testable and prioritized (P1-P3).
- US1-US4: Core interview flow (P1-P2)
- US5-US6: Recruitment platform integration (P2)
- US7-US9: Participant identity and profiles (P2-P3)

**Edge Cases**: 12 edge cases identified with clear handling strategies (includes recruitment platform scenarios, identity reconciliation, storage failures).

**Scope**: Clear boundaries between in-scope (MVP) and out-of-scope (future) features. Constraints explicitly documented. Webhooks deferred to post-MVP (YAGNI).

**Dependencies**: 3 dependencies identified (Study Management with slugs, Firebase Auth, Pipecat-momtest). 5 reasonable assumptions documented (includes recruitment platform trust model, external ID uniqueness, pipecat callback reachability).

**Infrastructure**: Shared GCS bucket now in-scope (created via Pulumi IAC in this repo), not a dependency.

## Notes

**Spec is ready for `/speckit.plan`.**

No clarifications needed - all critical decisions were made based on:
- Existing backend implementation (share links, interviews, recordings endpoints already exist)
- Industry standard practices (100MB file size limit, common audio formats)
- Project architecture patterns (Firebase Auth, multi-tenancy)
- URL-passing integration pattern for loose coupling with separate interview component

**Integration Architecture Documented**:

**Pipecat-momtest Integration**:
- Interactive interview component is pipecat-momtest (https://github.com/tinyteamco/pipecat-momtest) - separate application, out of scope
- Uses "pull" pattern: pipecat fetches interview data from Verity, posts completion back
- Concrete API contracts defined for both directions (Verity ↔ Pipecat)
- Pipecat codebase analyzed to identify integration points:
  - Hardcoded scripts need to be replaced with dynamic guide injection
  - Completion handler needs webhook to POST back to Verity
  - Download endpoints already exist for artifacts
- Requires CORS support for cross-origin requests

**Recruitment Platform Integration** (NEW):
- **Reusable slug-based links**: `https://verity.com/study/{slug}/start?pid={{PARTICIPANT_ID}}`
  - Creates interviews on-the-fly when accessed
  - Simple integration, no API auth required
  - Works with Prolific, UserTesting, Respondent, UserInterviews, etc.
  - pid parameter is optional (supports both platform tracking and direct distribution)
- **Webhooks**: Deferred to post-MVP (YAGNI - most platforms track completion themselves)

**Participant Identity & Sign-In** (NEW):
- Optional pre-interview sign-in (interstitial page)
- Post-interview claim flow (thank-you page)
- Cross-platform identity reconciliation (verity_user_id + external_participant_id)
- Participant profile dashboard (view history across platforms)

**Required Changes**:
- **Infrastructure (Pulumi)**:
  - Create shared GCS bucket for interview artifacts
  - Configure IAM permissions: Verity service account (read/write) + Pipecat service account (read/write)

- **Verity Backend**:
  - Add `GET /interview/{token}` (public) - pipecat data fetch
  - Add `POST /interview/{token}/complete` (callback) - pipecat completion
  - Add `GET /study/{slug}/start?pid={external_id}` (public) - reusable links (creates interviews on-the-fly)
  - Add VerityUser account creation and management (Firebase)
  - Add participant profile dashboard and claim flow
  - Artifact proxy endpoints for researchers (stream from GCS)
  - CORS configuration for public endpoints

- **Verity Frontend**:
  - Study settings page with reusable link template display (copy-to-clipboard)
  - Interview list/detail views (transcripts inline, audio download)
  - Interstitial page for pre-interview sign-in
  - Thank-you page with claim flow
  - Participant profile dashboard

- **Pipecat-momtest**:
  - Add dynamic guide endpoint (replace hardcoded prompts)
  - Add completion callback to POST back to Verity
  - Support Verity access tokens in WebSocket flow

The backend already has most required endpoints per the OpenAPI spec, so implementation will primarily focus on:
1. Infrastructure setup (shared GCS bucket with IAM via Pulumi)
2. Frontend UI for all new flows (reusable link template, dashboards, sign-in)
3. Integration orchestration (redirects, callbacks)
4. Participant identity system (VerityUser, claim flow)
5. On-the-fly interview creation from reusable links
