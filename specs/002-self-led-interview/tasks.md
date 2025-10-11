# Tasks: Self-Led Interview Execution

**Input**: Design documents from `/specs/002-self-led-interview/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: This feature follows BDD-First development (Constitution I). All tests MUST be written before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/src/api/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Infrastructure**: `infra/`

---

## Phase 1: Infrastructure (Shared GCS Bucket)

**Purpose**: Provision shared storage for interview artifacts (blocking prerequisite for all user stories)

- [X] T001 [Infra] Add GCS bucket resource to infra/__main__.py with uniform bucket-level access and public access prevention
- [X] T002 [Infra] Add IAM binding for Verity backend service account (roles/storage.objectAdmin) in infra/__main__.py
- [X] T003 [Infra] Export bucket name and URL as Pulumi outputs in infra/__main__.py
- [X] T004 [Infra] Deploy infrastructure via GitHub Actions (stack: dev, action: up)
- [X] T005 [Infra] Add GCS_BUCKET_NAME environment variable to backend/.mise.toml from Pulumi outputs

**Checkpoint**: GCS bucket provisioned and accessible from backend - ready for database model phase

---

## Phase 2: Foundational (Database Models & Schema)

**Purpose**: Core database schema that ALL user stories depend on (BLOCKS all feature work)

**⚠️ CRITICAL**: No user story implementation can begin until this phase is complete

### Study Model Modifications

- [X] T006 [P] [Foundation] Add slug field (String(63), unique, indexed) to backend/src/models.py
- [X] T007 [P] [Foundation] Add participant_identity_flow enum field to backend/src/models.py
- [X] T008 [Foundation] Generate Alembic migration for Study model changes using `alembic revision --autogenerate -m "add study slug and participant_identity_flow"`

### Interview Model

- [X] T009 [P] [Foundation] Update Interview model in backend/src/models.py with fields: expires_at, external_participant_id, platform_source, verity_user_id, claimed_at, pipecat_session_id (existing fields already present)
- [X] T010 [P] [Foundation] Add relationship Interview.verity_user in models (Study.interviews already exists)
- [X] T011 [Foundation] Generate Alembic migration for Interview model using `alembic revision --autogenerate -m "add interview model"`

### VerityUser & ParticipantProfile Models

- [X] T012 [P] [Foundation] Create VerityUser model in backend/src/models.py with fields: id, firebase_uid (unique), email (unique), display_name, created_at, last_sign_in
- [X] T013 [P] [Foundation] Create ParticipantProfile model in backend/src/models.py with fields: id, verity_user_id (unique FK), platform_identities (JSON)
- [X] T014 [P] [Foundation] Add relationships VerityUser.interviews, VerityUser.profile, Interview.verity_user
- [X] T015 [Foundation] Generate Alembic migration for VerityUser and ParticipantProfile models using `alembic revision --autogenerate -m "add verity_user and participant_profile models"`

### Database Migration Execution

- [X] T016 [Foundation] Run all migrations using `alembic upgrade head` in local dev environment
- [X] T017 [Foundation] Verify database schema matches data-model.md using database inspection

**Checkpoint**: Foundation ready - all models exist, all user stories can now be implemented in parallel

---

## Phase 3: User Story 1 - Share Reusable Study Link (Priority: P1) 🎯 MVP

**Goal**: Researchers can copy reusable study link template that creates interviews on-the-fly when participants access it

**Independent Test**: Create a study, copy the reusable link template from study settings, access it with/without pid, verify interview is created on-the-fly

### BDD Tests for User Story 1 (WRITE FIRST, ENSURE THEY FAIL) ⚠️

- [X] T018 [P] [US1] Write Gherkin scenario "Researcher views reusable link template" in backend/tests/features/study_settings.feature
- [X] T019 [P] [US1] Write Gherkin scenario "Participant accesses reusable link with pid" in backend/tests/features/interview_access.feature
- [X] T020 [P] [US1] Write Gherkin scenario "Participant accesses reusable link without pid" in backend/tests/features/interview_access.feature
- [X] T021 [P] [US1] Write Gherkin scenario "Deduplication prevents duplicate interview for same external_participant_id" in backend/tests/features/interview_access.feature
- [X] T022 [US1] Implement step definitions for interview_access.feature in backend/tests/step_defs/test_interview_access.py
- [X] T023 [US1] Run tests to verify they FAIL (expected behavior before implementation)

### Backend Implementation for User Story 1

- [X] T024 [P] [US1] Create GET /study/{slug}/start endpoint in backend/src/api/main.py (creates interview on-the-fly, redirects to pipecat)
- [X] T025 [P] [US1] Add deduplication logic for external_participant_id + study_id in main.py
- [X] T026 [P] [US1] Add PIPECAT_URL and VERITY_API_BASE environment variables to backend/.mise.toml
- [X] T027 [US1] Add CORS configuration for pipecat domain in backend/src/api/main.py
- [X] T028 [US1] Run BDD tests to verify US1 backend implementation passes

### Frontend Implementation for User Story 1

- [ ] T029 [P] [US1] Write E2E test "Researcher views reusable link template in study settings" in frontend/tests/features/study_settings.feature
- [ ] T030 [P] [US1] Create StudySettings component with reusable link display and copy button in frontend/src/components/StudySettings.tsx
- [ ] T031 [P] [US1] Create StudySettingsPage in frontend/src/pages/StudySettingsPage.tsx
- [ ] T032 [US1] Add recruitment platform usage instructions to StudySettings component
- [ ] T033 [US1] Run E2E tests to verify US1 frontend implementation passes

**Checkpoint**: At this point, researchers can share reusable links and participants can access them to create interviews on-the-fly (P1 core value delivered)

---

## Phase 4: User Story 2 - Participant Access & Redirect (Priority: P1) 🎯 MVP

**Goal**: Participants click interview links and are redirected to pipecat interview interface with unique access tokens

**Independent Test**: Access an interview link, verify 302 redirect to pipecat with access_token parameter, test error cases (completed, invalid token)

### BDD Tests for User Story 2 (WRITE FIRST, ENSURE THEY FAIL) ⚠️

- [X] T034 [P] [US2] Write Gherkin scenario "Participant accesses valid interview link and receives redirect" in backend/tests/features/interview_access.feature
- [X] T035 [P] [US2] Write Gherkin scenario "Participant tries to access completed interview shows error page" in backend/tests/features/interview_access.feature
- [X] T036 [P] [US2] Write Gherkin scenario "Participant accesses invalid/expired token shows error page" in backend/tests/features/interview_access.feature (removed - out of scope for US2, belongs to US2.5)
- [X] T037 [P] [US2] Write Gherkin scenario "Participant accesses link for deleted study shows error message" in backend/tests/features/interview_access.feature (removed - Study model doesn't support soft delete)
- [X] T038 [US2] Implement step definitions for redirect scenarios in backend/tests/step_defs/test_interview_access.py
- [X] T039 [US2] Run tests to verify they FAIL (expected behavior before implementation)

### Backend Implementation for User Story 2

- [X] T040 [US2] Verify GET /study/{slug}/start endpoint from US1 properly handles redirect logic (302 response with Location header)
- [X] T041 [P] [US2] Add error handling for completed interviews in GET /study/{slug}/start (return HTML error page, not redirect)
- [X] T042 [P] [US2] Add error handling for expired tokens in GET /study/{slug}/start (return HTML error page)
- [X] T043 [P] [US2] Add error handling for deleted studies in GET /study/{slug}/start (return HTML error page)
- [X] T044 [US2] Run BDD tests to verify US2 backend implementation passes

**Checkpoint**: At this point, participants can be redirected to pipecat interview interface with proper error handling (P1 core value delivered)

---

## Phase 5: User Story 2.5 - Interview Data API Contract (Priority: P1) 🎯 MVP

**Goal**: Pipecat can fetch interview data via Verity's public API to conduct interviews

**Independent Test**: Call GET /interview/{access_token} with various tokens, verify responses match contract (200 for valid, 410 for completed, 404 for invalid)

### BDD Tests for User Story 2.5 (WRITE FIRST, ENSURE THEY FAIL) ⚠️

- [X] T045 [P] [US2.5] Write Gherkin scenario "Pipecat fetches interview data with valid token returns 200 with study guide" in backend/tests/features/interview_data_api.feature
- [X] T046 [P] [US2.5] Write Gherkin scenario "Pipecat calls with completed interview token returns 410 Gone" in backend/tests/features/interview_data_api.feature
- [X] T047 [P] [US2.5] Write Gherkin scenario "Pipecat calls with invalid token returns 404" in backend/tests/features/interview_data_api.feature
- [X] T048 [P] [US2.5] Write Gherkin scenario "Pipecat calls with expired token returns 410 Gone" in backend/tests/features/interview_data_api.feature (updated from "deleted study" to "expired token")
- [X] T049 [US2.5] Implement step definitions for interview_data_api.feature in backend/tests/step_defs/test_interview_data_api.py
- [X] T050 [US2.5] Run tests to verify they FAIL (expected behavior before implementation)

### Backend Implementation for User Story 2.5

- [X] T051 [US2.5] Update GET /interview/{access_token} endpoint in backend/src/api/main.py (returns study title and interview guide)
- [X] T052 [P] [US2.5] Add validation for access_token format (UUID) in GET /interview/{access_token}
- [X] T053 [P] [US2.5] Add check for interview status (return 410 if completed) in GET /interview/{access_token}
- [X] T054 [P] [US2.5] Add check for token expiration (return 410 if expires_at passed) in GET /interview/{access_token}
- [X] T055 [US2.5] Run BDD tests to verify US2.5 backend implementation passes

**Checkpoint**: At this point, pipecat can fetch interview data to conduct interviews (P1 core value delivered)

---

## Phase 6: User Story 3 - Completion Callback Handling (Priority: P2)

**Goal**: Verity accepts completion callbacks from pipecat, marks interviews complete, and stores artifact references

**Independent Test**: Send mock completion callback with storage paths, verify interview is marked complete and artifacts are accessible

### BDD Tests for User Story 3 (WRITE FIRST, ENSURE THEY FAIL) ⚠️

- [X] T056 [P] [US3] Write Gherkin scenario "Verity receives completion callback with storage paths marks interview completed" in backend/tests/features/interview_completion.feature
- [X] T057 [P] [US3] Write Gherkin scenario "Completion callback includes streaming transcript makes it viewable" in backend/tests/features/interview_completion.feature
- [X] T058 [P] [US3] Write Gherkin scenario "Completion callback includes audio storage path makes audio downloadable" in backend/tests/features/interview_completion.feature
- [X] T059 [P] [US3] Write Gherkin scenario "Pipecat retries completion callback for already complete interview returns 200 idempotent" in backend/tests/features/interview_completion.feature
- [X] T060 [US3] Implement step definitions for interview_completion.feature in backend/tests/step_defs/test_interview_completion.py
- [X] T061 [US3] Run tests to verify they FAIL (expected behavior before implementation)

### Backend Implementation for User Story 3

- [X] T062 [US3] Create POST /interview/{access_token}/complete endpoint in backend/src/api/main.py (accepts transcript_url, recording_url, notes)
- [X] T063 [P] [US3] Add interview status update logic (pending → completed) in POST /interview/{access_token}/complete
- [X] T064 [P] [US3] Add artifact reference storage (transcript_url, recording_url) in POST /interview/{access_token}/complete
- [X] T065 [P] [US3] Add idempotent check (return 200 if already completed) in POST /interview/{access_token}/complete
- [X] T066 [US3] Run BDD tests to verify US3 backend implementation passes

**Checkpoint**: At this point, pipecat can complete interviews and Verity stores artifact references (P2 value delivered)

---

## Phase 7: User Story 4 - View Interview Submissions (Priority: P2)

**Goal**: Researchers view all interview submissions for their studies to track participation and access recordings/transcripts

**Independent Test**: Create completed interviews, log in as researcher, verify all interviews appear in list with transcript inline and audio download

### BDD Tests for User Story 4 (WRITE FIRST, ENSURE THEY FAIL) ⚠️

- [X] T067 [P] [US4] Write Gherkin scenario "Researcher views list of completed interviews for study" in backend/tests/features/researcher_interview_list.feature
- [X] T068 [P] [US4] Write Gherkin scenario "Researcher clicks interview to view transcript inline" in backend/tests/features/researcher_interview_list.feature
- [X] T069 [P] [US4] Write Gherkin scenario "Researcher downloads audio file from interview" in backend/tests/features/researcher_interview_list.feature
- [X] T070 [P] [US4] Write Gherkin scenario "Researcher cannot access interviews from other organization returns 403" in backend/tests/features/researcher_interview_list.feature
- [X] T071 [US4] Implement step definitions for researcher_interview_list.feature in backend/tests/step_defs/test_researcher_interview_list.py
- [X] T072 [US4] Run tests to verify they FAIL (expected behavior before implementation)

### Backend Implementation for User Story 4

- [X] T073 [P] [US4] Create GCSService class in backend/src/api/services/gcs_service.py with stream_artifact method (API proxy pattern)
- [X] T074 [P] [US4] Create GET /api/orgs/{org_id}/studies/{study_id}/interviews endpoint in backend/src/api/routers/org_interviews.py
- [X] T075 [P] [US4] Add org-level access control check in org_interviews.py (server-side verification)
- [X] T076 [P] [US4] Create GET /api/orgs/{org_id}/interviews/{interview_id}/artifacts/{filename} endpoint in backend/src/api/routers/org_interviews.py
- [X] T077 [US4] Add cross-org 403 denial tests in backend/tests/features/researcher_interview_list.feature
- [X] T078 [US4] Run BDD tests to verify US4 backend implementation passes

### Frontend Implementation for User Story 4

- [ ] T079 [P] [US4] Write E2E test "Researcher views interview list with completion status" in frontend/tests/features/interview_list.feature
- [ ] T080 [P] [US4] Write E2E test "Researcher views transcript inline in interview detail" in frontend/tests/features/interview_list.feature
- [ ] T081 [P] [US4] Create API client for listStudyInterviews and downloadArtifact in frontend/src/api/interviews.ts
- [ ] T082 [P] [US4] Create InterviewList component displaying interviews with metadata in frontend/src/components/InterviewList.tsx
- [ ] T083 [P] [US4] Create InterviewDetail component with transcript inline and audio download button in frontend/src/components/InterviewDetail.tsx
- [ ] T084 [P] [US4] Create InterviewsPage in frontend/src/pages/InterviewsPage.tsx
- [ ] T085 [US4] Run E2E tests to verify US4 frontend implementation passes

**Checkpoint**: At this point, researchers can view completed interviews and access artifacts (P2 value delivered)

---

## Phase 8: User Story 5 - Reusable Study Link for Recruitment Platforms (Priority: P2)

**Goal**: Researchers generate reusable study links that recruitment platforms can use to dynamically send participants

**Independent Test**: Configure study with slug, substitute participant ID into template, access it, verify interview created on-the-fly with external_participant_id

**Note**: This story's backend functionality is largely covered by US1 (reusable links). This phase focuses on recruitment platform-specific features.

### BDD Tests for User Story 5 (WRITE FIRST, ENSURE THEY FAIL) ⚠️

- [X] T086 [P] [US5] Write Gherkin scenario "Study settings displays reusable link with slug format" in backend/tests/features/study_settings.feature (already covered by US1 scenarios)
- [X] T087 [P] [US5] Write Gherkin scenario "Recruitment platform accesses link with pid creates interview with external_participant_id" in backend/tests/features/interview_access.feature (already covered by US1 scenario "Participant accesses reusable link with pid")
- [X] T088 [P] [US5] Write Gherkin scenario "Same pid accesses link twice shows 'Interview already completed'" in backend/tests/features/interview_access.feature (already covered by US1 scenario "Deduplication prevents duplicate interview for same external_participant_id")
- [X] T089 [P] [US5] Write Gherkin scenario "Researcher views external participant ID in interview list" in backend/tests/features/researcher_interview_list.feature
- [X] T090 [US5] Run tests to verify they FAIL (expected behavior before implementation)

### Backend Implementation for User Story 5

- [X] T091 [US5] Verify deduplication logic from US1 properly prevents duplicate interviews for same pid (covered in T025 - lines 1484-1521 in main.py)
- [X] T092 [US5] Verify external_participant_id is stored and displayed in interview list endpoint (covered in T074 - line 881 in main.py includes external_participant_id and platform_source)
- [X] T093 [US5] Run BDD tests to verify US5 backend implementation passes

### Frontend Implementation for User Story 5

- [ ] T094 [P] [US5] Add recruitment platform substitution examples (Prolific, Respondent, UserTesting) to StudySettings component (enhance T030) - DEFERRED to frontend phase
- [ ] T095 [P] [US5] Display external_participant_id column in InterviewList component (enhance T082) - DEFERRED to frontend phase
- [ ] T096 [US5] Run E2E tests to verify US5 frontend implementation passes - DEFERRED to frontend phase

**Checkpoint**: Backend verification complete - reusable links work with recruitment platforms and track external participant IDs (P2 value delivered). Frontend enhancements deferred.

---

## Phase 9: User Story 6 - Pre-Interview Optional Sign-In (Priority: P2) **OPTIONAL FOR MVP**

**Goal**: Participants accessing direct links can optionally sign in before starting interviews when study allows pre-sign-in

**Independent Test**: Access direct link (no pid) for study with "allow_pre_signin" setting, verify interstitial appears with sign-in option

**Note**: This phase can be DEFERRED to post-MVP. Core P1 flow (US1-US5) works without participant sign-in.

### BDD Tests for User Story 6 (WRITE FIRST, ENSURE THEY FAIL) ⚠️

- [ ] T097 [P] [US6] Write Gherkin scenario "Direct link with allow_pre_signin shows interstitial with Continue as Guest or Sign In options" in backend/tests/features/participant_identity.feature
- [ ] T098 [P] [US6] Write Gherkin scenario "Recruitment platform link with pid skips interstitial redirects directly to pipecat" in backend/tests/features/participant_identity.feature
- [ ] T099 [P] [US6] Write Gherkin scenario "Participant signs in on interstitial auto-links interview to VerityUser" in backend/tests/features/participant_identity.feature
- [ ] T100 [P] [US6] Write Gherkin scenario "Already signed in participant accessing direct link auto-links interview no interstitial" in backend/tests/features/participant_identity.feature
- [ ] T101 [US6] Implement step definitions for participant_identity.feature in backend/tests/step_defs/test_participant_identity.py
- [ ] T102 [US6] Run tests to verify they FAIL (expected behavior before implementation)

### Backend Implementation for User Story 6

- [ ] T103 [US6] Add optional Firebase Auth dependency for participants in backend/src/api/dependencies.py (get_current_participant_user)
- [ ] T104 [P] [US6] Add pre-interview sign-in logic to GET /study/{slug}/start endpoint (check participant_identity_flow setting and pid presence)
- [ ] T105 [P] [US6] Add auto-link logic for signed-in participants in GET /study/{slug}/start (populate verity_user_id on Interview creation)
- [ ] T106 [US6] Run BDD tests to verify US6 backend implementation passes

### Frontend Implementation for User Story 6

- [ ] T107 [P] [US6] Write E2E test "Interstitial page shows Continue as Guest and Sign In options for direct link" in frontend/tests/features/participant_flows.feature
- [ ] T108 [P] [US6] Create ParticipantInterstitial component with Continue as Guest and Sign In buttons in frontend/src/components/ParticipantInterstitial.tsx
- [ ] T109 [P] [US6] Add Firebase Auth integration for participant sign-in in ParticipantInterstitial component
- [ ] T110 [US6] Run E2E tests to verify US6 frontend implementation passes

**Checkpoint**: At this point, participants can optionally sign in before interviews for direct links (P2 value delivered)

---

## Phase 10: User Story 7 - Post-Interview Claim and Cross-Platform Identity (Priority: P3) **OPTIONAL FOR MVP**

**Goal**: Participants can sign in after completing anonymous interviews to claim them and view participation history across platforms

**Independent Test**: Complete multiple anonymous interviews from different sources, sign in once, verify all interviews appear in unified dashboard

**Note**: This phase can be DEFERRED to post-MVP. Core P1 flow works without participant claim.

### BDD Tests for User Story 7 (WRITE FIRST, ENSURE THEY FAIL) ⚠️

- [ ] T111 [P] [US7] Write Gherkin scenario "Participant sees Sign In to Track My Interviews option on thank-you page for claim_after study" in backend/tests/features/participant_identity.feature
- [ ] T112 [P] [US7] Write Gherkin scenario "Participant clicks Sign In and claims completed interview links to VerityUser" in backend/tests/features/participant_identity.feature
- [ ] T113 [P] [US7] Write Gherkin scenario "Signed in participant completes Respondent interview sees both Prolific and Respondent in dashboard" in backend/tests/features/participant_identity.feature
- [ ] T114 [P] [US7] Write Gherkin scenario "Participant completes interview for anonymous study sees no claim option" in backend/tests/features/participant_identity.feature
- [ ] T115 [US7] Implement step definitions for claim scenarios in backend/tests/step_defs/test_participant_identity.py
- [ ] T116 [US7] Run tests to verify they FAIL (expected behavior before implementation)

### Backend Implementation for User Story 7

- [ ] T117 [US7] Create POST /interview/{access_token}/claim endpoint in backend/src/api/routers/participant_profile.py
- [ ] T118 [P] [US7] Add VerityUser get-or-create logic in claim endpoint (by firebase_uid)
- [ ] T119 [P] [US7] Add ParticipantProfile creation on first VerityUser sign-in
- [ ] T120 [P] [US7] Add interview linking logic (set verity_user_id, claimed_at) in claim endpoint
- [ ] T121 [P] [US7] Add platform_identities JSON update logic in claim endpoint (map platform to external_participant_id)
- [ ] T122 [US7] Run BDD tests to verify US7 backend implementation passes

### Frontend Implementation for User Story 7

- [ ] T123 [P] [US7] Write E2E test "Thank-you page shows Sign In to Track My Interviews button for claim_after study" in frontend/tests/features/participant_flows.feature
- [ ] T124 [P] [US7] Create ThankYouPage component with claim button in frontend/src/components/ThankYouPage.tsx
- [ ] T125 [P] [US7] Add Firebase Auth integration for claim flow in ThankYouPage component
- [ ] T126 [US7] Run E2E tests to verify US7 frontend implementation passes

**Checkpoint**: At this point, participants can claim anonymous interviews and link them to their accounts (P3 value delivered)

---

## Phase 11: User Story 8 - Participant Profile Dashboard (Priority: P3) **OPTIONAL FOR MVP**

**Goal**: Signed-in participants view complete participation history across all studies and platforms

**Independent Test**: Sign in as participant with completed interviews across multiple platforms, verify all participation data visible

**Note**: This phase can be DEFERRED to post-MVP. Depends on US7 (claim flow).

### BDD Tests for User Story 8 (WRITE FIRST, ENSURE THEY FAIL) ⚠️

- [ ] T127 [P] [US8] Write Gherkin scenario "Signed in participant views list of all completed interviews with study titles and dates" in backend/tests/features/participant_dashboard.feature
- [ ] T128 [P] [US8] Write Gherkin scenario "Participant sees platform source for each interview in dashboard" in backend/tests/features/participant_dashboard.feature
- [ ] T129 [P] [US8] Write Gherkin scenario "Participant with interviews from 3 platforms sees aggregated total participation count" in backend/tests/features/participant_dashboard.feature
- [ ] T130 [US8] Implement step definitions for participant_dashboard.feature in backend/tests/step_defs/test_participant_dashboard.py
- [ ] T131 [US8] Run tests to verify they FAIL (expected behavior before implementation)

### Backend Implementation for User Story 8

- [ ] T132 [US8] Create GET /api/participant/dashboard endpoint in backend/src/api/routers/participant_profile.py
- [ ] T133 [P] [US8] Add query for all claimed interviews by verity_user_id in dashboard endpoint
- [ ] T134 [P] [US8] Add stats calculation (total interviews, platforms connected) in dashboard endpoint
- [ ] T135 [US8] Run BDD tests to verify US8 backend implementation passes

### Frontend Implementation for User Story 8

- [ ] T136 [P] [US8] Write E2E test "Participant dashboard displays interview history with platform sources" in frontend/tests/features/participant_flows.feature
- [ ] T137 [P] [US8] Create ParticipantDashboard component displaying interview cards with metadata in frontend/src/components/ParticipantDashboard.tsx
- [ ] T138 [P] [US8] Create ParticipantProfilePage in frontend/src/pages/ParticipantProfilePage.tsx
- [ ] T139 [P] [US8] Add API client for getParticipantDashboard in frontend/src/api/interviews.ts
- [ ] T140 [US8] Run E2E tests to verify US8 frontend implementation passes

**Checkpoint**: At this point, participants have a complete dashboard showing all participation history (P3 value delivered)

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T141 [P] [Polish] Add structured logging for interview lifecycle events (creation, access, completion, claim) in backend
- [ ] T142 [P] [Polish] Add error handling and user-friendly error pages for interview access errors
- [ ] T143 [P] [Polish] Update CLAUDE.md with feature implementation notes (new models, endpoints, frontend components)
- [ ] T144 [P] [Polish] Add API documentation comments to all new endpoints
- [ ] T145 [P] [Polish] Run quickstart.md validation against implemented code
- [ ] T146 [P] [Polish] Code cleanup and refactoring for consistency
- [ ] T147 [P] [Polish] Performance optimization for interview list queries (add composite indexes if needed)
- [ ] T148 [Polish] Run full test suite (backend BDD + frontend E2E) and verify zero warnings

---

## Dependencies & Execution Order

### Phase Dependencies

- **Infrastructure (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Infrastructure completion - BLOCKS all user stories
- **User Stories (Phases 3-11)**: All depend on Foundational phase completion
  - P1 stories (US1-US5): Can proceed sequentially or in parallel (if staffed)
  - P2/P3 stories (US6-US8): Can be deferred to post-MVP
- **Polish (Phase 12)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (Share Reusable Link)**: Can start after Foundational - No dependencies on other stories
- **US2 (Participant Redirect)**: Can start after Foundational - No dependencies on other stories
- **US2.5 (Interview Data API)**: Can start after Foundational - No dependencies on other stories
- **US3 (Completion Callback)**: Can start after Foundational - No dependencies on other stories
- **US4 (View Submissions)**: Depends on US3 (needs completed interviews) - Can integrate after US3
- **US5 (Recruitment Platforms)**: Depends on US1 (reuses reusable link logic) - Can start after US1
- **US6 (Pre-Interview Sign-In)**: Can start after Foundational - Optional for MVP
- **US7 (Post-Interview Claim)**: Can start after Foundational - Optional for MVP
- **US8 (Participant Dashboard)**: Depends on US7 (needs claim flow) - Optional for MVP

### MVP Critical Path (P1 Only)

**Recommended sequence for fastest MVP delivery:**

1. Phase 1: Infrastructure (GCS bucket) → ~2 hours
2. Phase 2: Foundational (Database models) → ~3 hours
3. Phase 3: User Story 1 (Reusable links) → ~4 hours
4. Phase 4: User Story 2 (Redirect) → ~2 hours
5. Phase 5: User Story 2.5 (Interview API) → ~2 hours
6. Phase 6: User Story 3 (Completion callback) → ~3 hours
7. Phase 7: User Story 4 (Researcher view submissions) → ~4 hours

**MVP Total**: ~20 hours (complete P1 flow: researchers can distribute links, participants complete interviews, researchers view results)

### Parallel Opportunities

- **Infrastructure Phase**: All tasks can run sequentially (pulumi deployment)
- **Foundational Phase**: T006-T007 (Study model) || T009-T011 (Interview model) || T012-T015 (VerityUser models)
- **User Story Tests**: All BDD tests within a story marked [P] can run in parallel
- **User Story Models/Services**: All models within a story marked [P] can run in parallel
- **Different User Stories**: US1-US5 can be worked on in parallel by different developers after Foundational phase

---

## Parallel Example: User Story 1

```bash
# Launch all BDD tests for User Story 1 together:
Task: "Write Gherkin scenario 'Researcher views reusable link template' in backend/tests/features/study_settings.feature"
Task: "Write Gherkin scenario 'Participant accesses reusable link with pid' in backend/tests/features/interview_access.feature"
Task: "Write Gherkin scenario 'Participant accesses reusable link without pid' in backend/tests/features/interview_access.feature"

# After tests fail, launch backend implementation tasks in parallel:
Task: "Create GET /study/{slug}/start endpoint in backend/src/api/routers/interviews.py"
Task: "Add deduplication logic for external_participant_id in interviews.py"
Task: "Add CORS configuration for pipecat in main.py"
```

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Infrastructure (~2 hours)
2. Complete Phase 2: Foundational (~3 hours) - CRITICAL - blocks all stories
3. Complete Phase 3-7: User Stories 1-4 (~15 hours)
4. **STOP and VALIDATE**: Test complete P1 flow end-to-end
5. Deploy/demo if ready

**MVP Deliverables**:
- ✅ Researchers can generate and share reusable study links
- ✅ Participants can access interviews via links (with/without pid)
- ✅ Pipecat can fetch interview data and conduct interviews
- ✅ Pipecat can complete interviews via callback
- ✅ Researchers can view completed interviews and download artifacts

### Incremental Delivery

1. Complete Infrastructure + Foundational → Foundation ready (~5 hours)
2. Add US1 → Test independently → Deploy/Demo (Reusable links work!)
3. Add US2 + US2.5 → Test independently → Deploy/Demo (Participant access works!)
4. Add US3 → Test independently → Deploy/Demo (Completion callback works!)
5. Add US4 → Test independently → Deploy/Demo (Researcher artifact access works! - MVP complete)
6. Add US5 → Test independently → Deploy/Demo (Recruitment platform integration!)
7. Optionally add US6-US8 → Test independently → Deploy/Demo (Participant identity!)

### Parallel Team Strategy

With multiple developers:

1. Team completes Infrastructure + Foundational together (~5 hours)
2. Once Foundational is done:
   - Developer A: User Story 1 + 2 (Participant access flow)
   - Developer B: User Story 2.5 + 3 (Pipecat integration)
   - Developer C: User Story 4 (Researcher artifact access)
3. Stories complete and integrate independently
4. Team validates complete P1 flow together

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **BDD-First**: Verify tests fail before implementing (Constitution I)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Multi-Tenancy**: Server-side org_id validation required (Constitution III)
- **MVP-First**: Defer P2/P3 stories (US6-US8) until P1 validated (Constitution X)
- Run `make check` (format + lint + types) after each implementation task (Constitution II)
