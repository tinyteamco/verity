# Tasks: Study Management UI

**Input**: Design documents from `/specs/001-study-management-ui/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: BDD tests are REQUIRED per Constitution Principle I (BDD-First Development)

**Organization**: Tasks grouped by user story for independent implementation and testing

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- File paths follow monorepo structure: `frontend/` and `backend/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install dependencies needed for implementation

- [X] T001 Install `react-markdown` dependency in frontend for markdown preview rendering

**Checkpoint**: Dependencies installed, ready for BDD test writing ✅

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Create TypeScript types for Study and InterviewGuide in `frontend/src/types/study.ts`
- [X] T003 Add API client functions (`generateStudy`, `getGuide`, `updateGuide`) to `frontend/src/lib/api.ts`
- [X] T004 [P] Create `StudyGuideViewer` component in `frontend/src/components/StudyGuideViewer.tsx` (renders markdown with react-markdown)
- [X] T005 [P] Add routing for study generation page in frontend router configuration

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel ✅

---

## Phase 3: User Story 1 - Automated Study Creation (Priority: P1) 🎯 MVP

**Goal**: Users can enter a research topic and receive a generated study with interview guide

**Independent Test**: Enter topic "How do people shop in supermarkets?", verify new study appears with generated title and guide content

### BDD Tests for User Story 1 (Write FIRST, ensure they FAIL)

- [X] T006 [US1] Create `frontend/tests/features/study-generation.feature` with Scenario: "Generate study from topic"
  - Given logged in and on studies page
  - When click "Generate Study"
  - And enter topic "How do people shop in supermarkets?"
  - And submit
  - Then see loading indicator
  - And after generation completes, see new study with generated title

- [X] T007 [US1] Add Scenario: "Validation error for empty topic" to study-generation.feature
  - Given on generate study modal
  - When enter empty topic and submit
  - Then see validation error "Topic is required"

- [X] T008 [US1] Add Scenario: "Timeout error for slow generation" to study-generation.feature
  - Given generation takes >60 seconds
  - Then see timeout error with retry option

- [X] T009 [US1] Add Scenario: "Server error with retry option" to study-generation.feature
  - Given backend returns 500 error
  - Then see error message with "Retry" and "Create Manually" buttons

- [X] T010 [US1] Create step definitions in `tests/steps/study-generation.steps.ts`
  - Implement all Given/When/Then steps for US1 scenarios

- [X] T011 [US1] Run `make frontend-test` and verify all US1 scenarios FAIL (not implemented yet)
  - Fixed duplicate step definition (`When I click {string}` was defined in both org-management and study-generation)
  - BDD tests generated successfully - all 11 scenarios found
  - Verified tests fail correctly (UI not implemented yet)

### Implementation for User Story 1

- [ ] T012 [US1] Add "Generate Study" button to `frontend/src/pages/StudyListPage.tsx`
  - Button opens generation modal
  - Modal has textarea for topic input + submit/cancel buttons

- [ ] T013 [US1] Implement topic validation in StudyListPage
  - Check topic not empty (trim whitespace)
  - Min length 10 characters
  - Max length 500 characters
  - Show inline error on invalid input

- [ ] T014 [US1] Implement generation API call in StudyListPage
  - Call `generateStudy(orgId, topic)` from api.ts
  - Handle loading state (30-60s wait)
  - Show loading spinner with "Generating your study..." message

- [ ] T015 [US1] Implement client-side timeout (60s) in StudyListPage
  - Use AbortController to cancel request after 60s
  - Show timeout error: "Generation took too long. [Retry] or [Create Manually]"

- [ ] T016 [US1] Implement error handling in StudyListPage
  - Catch API errors (400, 403, 500)
  - Show user-friendly error messages
  - Provide "Retry" button that calls API again
  - Provide "Create Manually" button that falls back to existing manual flow

- [ ] T017 [US1] Implement success navigation in StudyListPage
  - On successful generation, close modal
  - Navigate to `/orgs/{orgId}/studies/{newStudyId}`
  - Show new study in detail page

- [ ] T018 [US1] Run `make frontend-test` and verify all US1 scenarios PASS

- [ ] T019 [US1] Run `make frontend-check` (TypeScript + linting) and fix any issues

**Checkpoint**: User Story 1 fully functional - users can generate studies from topics

---

## Phase 4: User Story 2 - Interview Guide Editing (Priority: P1)

**Goal**: Users can edit the generated interview guide markdown content and save changes

**Independent Test**: Open a study with guide, click "Edit Guide", modify content, save, verify changes persist

### BDD Tests for User Story 2 (Write FIRST, ensure they FAIL)

- [ ] T020 [US2] Add Scenario: "Edit interview guide" to study-generation.feature
  - Given a study with an interview guide exists
  - When navigate to study detail page
  - And click "Edit Guide"
  - And modify the guide content
  - And click "Save"
  - Then see "Guide saved successfully"
  - And updated content is displayed

- [ ] T021 [US2] Add Scenario: "Preview markdown while editing" to study-generation.feature
  - Given editing interview guide
  - When toggle "Preview" mode
  - Then see rendered markdown (not raw text)

- [ ] T022 [US2] Add Scenario: "Warning before navigation with unsaved changes" to study-generation.feature
  - Given editing guide with unsaved changes
  - When attempt to navigate away
  - Then see warning "You have unsaved changes"

- [ ] T023 [US2] Add Scenario: "Save empty guide content" to study-generation.feature
  - Given editing guide
  - When delete all content and save
  - Then save succeeds (empty content is valid)

- [ ] T024 [US2] Update step definitions in `frontend/tests/step_defs/study_generation_steps.ts`
  - Implement steps for US2 scenarios

- [ ] T025 [US2] Run `make frontend-test` and verify US2 scenarios FAIL

### Implementation for User Story 2

- [ ] T026 [P] [US2] Create `StudyGuideEditor` component in `frontend/src/components/StudyGuideEditor.tsx`
  - Props: `guide: InterviewGuide`, `onSave: (guide) => void`, `onCancel: () => void`
  - State: contentMd, isDirty, isSaving, showPreview, error
  - Textarea for markdown editing
  - Save/Cancel buttons
  - Preview toggle button

- [ ] T027 [US2] Implement markdown preview in StudyGuideEditor
  - When showPreview=true, render split view
  - Left pane: textarea (editable)
  - Right pane: `<ReactMarkdown>{contentMd}</ReactMarkdown>`
  - Toggle button switches between edit-only and split view

- [ ] T028 [US2] Implement save functionality in StudyGuideEditor
  - Call `updateGuide(studyId, contentMd)` from api.ts
  - Show saving spinner on save button
  - On success: call onSave callback, show toast "Guide saved"
  - On error: show error message, enable retry

- [ ] T029 [US2] Implement unsaved changes warning in StudyGuideEditor
  - Track isDirty state (content changed from initial)
  - Add beforeunload event listener
  - Show browser warning if isDirty and user navigates away
  - Clean up event listener on unmount

- [ ] T030 [US2] Add "Edit Guide" button to `frontend/src/pages/StudyDetailPage.tsx`
  - Button only shows when guide exists
  - Clicking opens edit mode (render StudyGuideEditor instead of viewer)
  - Pass guide and callbacks to editor

- [ ] T031 [US2] Integrate editor into StudyDetailPage
  - Add `isEditingGuide` state
  - When editing: show StudyGuideEditor
  - When not editing: show StudyGuideViewer
  - onSave: update guide state, exit edit mode, show success message
  - onCancel: exit edit mode without saving

- [ ] T032 [US2] Run `make frontend-test` and verify US2 scenarios PASS

- [ ] T033 [US2] Run `make frontend-check` and fix any issues

**Checkpoint**: User Story 2 fully functional - users can edit and save interview guides

---

## Phase 5: User Story 3 - View Study with Interview Guide (Priority: P2)

**Goal**: Users can view study details including rendered interview guide content

**Independent Test**: Navigate to study with guide, verify guide content is rendered as markdown (not raw text)

### BDD Tests for User Story 3 (Write FIRST, ensure they FAIL)

- [ ] T034 [US3] Add Scenario: "View study with interview guide" to study-generation.feature
  - Given a study with interview guide exists
  - When navigate to study detail page
  - Then see study title and description
  - And see interview guide rendered with sections and questions

- [ ] T035 [US3] Add Scenario: "View study without interview guide" to study-generation.feature
  - Given a study without interview guide
  - When navigate to study detail page
  - Then see "No interview guide yet"
  - And see "Add Guide" or "Generate Guide" button

- [ ] T036 [US3] Update step definitions in `frontend/tests/step_defs/study_generation_steps.ts`
  - Implement steps for US3 scenarios

- [ ] T037 [US3] Run `make frontend-test` and verify US3 scenarios FAIL

### Implementation for User Story 3

- [ ] T038 [US3] Update `frontend/src/pages/StudyDetailPage.tsx` to fetch guide
  - Add `guide` state variable
  - useEffect: call `getGuide(studyId)` on mount
  - Handle 404 (no guide): set guide=null
  - Handle errors: show error message

- [ ] T039 [US3] Render guide in StudyDetailPage (view mode)
  - If guide exists: render `<StudyGuideViewer guide={guide} />`
  - If guide is null: show "No interview guide yet" message
  - Add "Generate Guide" button (calls generate endpoint with empty topic?)
  - Or "Add Guide Manually" button (opens editor with empty content)

- [ ] T040 [US3] Run `make frontend-test` and verify US3 scenarios PASS

- [ ] T041 [US3] Run `make frontend-check` and fix any issues

**Checkpoint**: User Story 3 fully functional - users can view studies with/without guides

---

## Phase 6: User Story 4 - Manual Study Creation Fallback (Priority: P3)

**Goal**: Users can create studies manually (without generation) as a fallback

**Independent Test**: Click "Create Study Manually", fill title/description, submit, verify study created without guide

### BDD Tests for User Story 4 (Write FIRST, ensure they FAIL)

- [ ] T042 [US4] Add Scenario: "Create study manually" to study-generation.feature
  - Given on studies page
  - When click "Create Study Manually"
  - And enter title "Manual Study"
  - And enter description "Testing manual creation"
  - And submit
  - Then see new study in list
  - And study has no interview guide

- [ ] T043 [US4] Update step definitions in `frontend/tests/step_defs/study_generation_steps.ts`
  - Implement steps for US4 scenario

- [ ] T044 [US4] Run `make frontend-test` and verify US4 scenario FAILS

### Implementation for User Story 4

- [ ] T045 [US4] Add "Create Study Manually" button to `frontend/src/pages/StudyListPage.tsx`
  - Separate button from "Generate Study"
  - Opens manual creation modal (existing functionality)
  - Keep existing manual study creation flow

- [ ] T046 [US4] Ensure manual creation is clearly distinct from generation
  - Update button text to clarify difference
  - "Generate Study" (primary) vs "Create Manually" (secondary/fallback)
  - Consider placement: generation prominent, manual less prominent

- [ ] T047 [US4] Update StudyDetailPage to handle manually created studies
  - Manual studies have no guide initially
  - Show "No interview guide yet" with options:
    - "Generate Guide" (calls generation endpoint)
    - "Add Manually" (opens editor with empty content)

- [ ] T048 [US4] Run `make frontend-test` and verify US4 scenario PASSES

- [ ] T049 [US4] Run `make frontend-check` and fix any issues

**Checkpoint**: All 4 user stories complete and independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories

- [ ] T050 [P] Add loading states for all async operations across all components
- [ ] T051 [P] Ensure consistent error message styling across all components
- [ ] T052 Verify all modals close properly (ESC key, click outside)
- [ ] T053 Add keyboard shortcuts (Enter to submit, ESC to cancel) where appropriate
- [ ] T054 [P] Add analytics events for generation, editing, saving (if analytics configured)
- [ ] T055 Test edge case: generation during network disconnect
- [ ] T056 Test edge case: extremely long interview guide content (>10KB)
- [ ] T057 Test edge case: special characters in topic input
- [ ] T058 [P] Run full E2E test suite: `make test`
- [ ] T059 [P] Run full type checking: `make check`
- [ ] T060 Review quickstart.md and verify all examples work
- [ ] T061 Update frontend README if new components/patterns introduced

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (P1): Independent - can start after Foundational
  - US2 (P1): Independent - can start after Foundational (works even if US1 incomplete)
  - US3 (P2): Independent - can start after Foundational (displays existing guides)
  - US4 (P3): Independent - can start after Foundational (uses existing manual flow)
- **Polish (Phase 7)**: Depends on desired user stories being complete

### User Story Dependencies

- **US1 (Automated Study Creation)**: No dependencies on other stories
- **US2 (Interview Guide Editing)**: No dependencies on other stories (can edit any existing guide)
- **US3 (View Study with Guide)**: No dependencies on other stories (views existing data)
- **US4 (Manual Creation Fallback)**: No dependencies on other stories (standalone feature)

**Note**: All user stories are independently testable and can be worked on in parallel after Foundational phase completes.

### Within Each User Story (BDD-First Workflow)

1. Write BDD scenarios in Gherkin
2. Write step definitions
3. Run tests and verify they FAIL
4. Implement components/features
5. Run tests and verify they PASS
6. Run type checking and linting
7. Story complete ✓

### Parallel Opportunities

- **Phase 1**: Single task, completes quickly
- **Phase 2**: T006 and T007 can run in parallel (different files)
- **After Phase 2 completes**: All 4 user stories can be worked on in parallel by different developers
- **Within each story**:
  - BDD scenarios can be written in parallel
  - Components marked [P] can be built in parallel
- **Phase 7**: Tasks T050, T051, T054, T058, T059 can run in parallel

---

## Parallel Example: Foundational Phase

```bash
# Developer A:
Task T006: Create StudyGuideViewer component

# Developer B (parallel):
Task T007: Add routing for study generation page
```

## Parallel Example: After Foundational Complete

```bash
# Developer A: User Story 1
Tasks T008-T021: Automated study creation (full workflow)

# Developer B (parallel): User Story 2
Tasks T022-T033: Interview guide editing (full workflow)

# Developer C (parallel): User Story 3
Tasks T034-T041: View study with guide (full workflow)

# Developer D (parallel): User Story 4
Tasks T042-T049: Manual creation fallback (full workflow)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002-T005) - **CRITICAL BLOCKER**
3. Complete Phase 3: US1 - Automated Study Creation (T008-T021)
4. Complete Phase 4: US2 - Interview Guide Editing (T022-T033)
5. **STOP and VALIDATE**: Test US1 + US2 independently
6. Deploy/demo if ready

**Why US1 + US2 is MVP**: Users need both generation AND editing to have a complete workflow. Generation alone (US1) gives a starting point, but editing (US2) is required to customize the guide for their research needs.

### Incremental Delivery (All Stories)

1. Setup + Foundational → Foundation ready
2. Add US1 → Test independently
3. Add US2 → Test independently → **MVP COMPLETE** (generation + editing)
4. Add US3 → Test independently → Viewing improved
5. Add US4 → Test independently → Fallback option available
6. Polish → Production ready

### Parallel Team Strategy

With 4 developers after Foundational phase completes:

1. Team completes Setup + Foundational together (T001-T005)
2. Once Foundational done, split into 4 parallel tracks:
   - Dev A: US1 (T008-T021)
   - Dev B: US2 (T022-T033)
   - Dev C: US3 (T034-T041)
   - Dev D: US4 (T042-T049)
3. Stories integrate naturally (all use same API layer from Foundational)
4. Team reconvenes for Phase 7 polish

---

## Notes

- **BDD-First Required**: Per Constitution Principle I, all scenarios must be written and FAIL before implementation
- **[P] markers**: Different files, no dependencies, safe to parallelize
- **[Story] labels**: US1, US2, US3, US4 map to spec.md user stories
- **Independent stories**: Each story delivers standalone value and can be tested independently
- **Commit strategy**: Commit after each task or logical group (e.g., all scenarios for a story)
- **Testing checkpoints**: Run `make frontend-test` after implementing each story to verify
- **Type checking**: Run `make frontend-check` frequently to catch TypeScript errors early
- **Backend unchanged**: No backend tasks needed - all required endpoints exist and are tested
- **Focus on user value**: Each checkpoint should result in a testable, demonstrable feature

**Total Tasks**: 61
- Setup: 1
- Foundational: 4
- User Story 1: 14 tasks
- User Story 2: 14 tasks
- User Story 3: 8 tasks
- User Story 4: 8 tasks
- Polish: 12 tasks

**Parallel Opportunities**: ~15 tasks can run in parallel across different files/developers

**Suggested MVP Scope**: US1 + US2 (28 tasks total, ~2-3 days for one developer)
