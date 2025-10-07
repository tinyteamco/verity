# Feature Specification: Study Management UI

**Feature Branch**: `001-study-management-ui`
**Created**: 2025-10-07
**Status**: Draft
**Input**: User description: "Study Management UI - web interface for organization users to create, view, and manage research studies with interview guides"

## Context

**What's Already Working:**
- ✅ Basic study CRUD (list, create, edit, delete) - 16 E2E tests passing
- ✅ Backend study generation endpoint (`POST /orgs/{org_id}/studies/generate`)
- ✅ Backend interview guide upsert (`PUT /studies/{study_id}/guide`)
- ✅ Backend interview guide fetch (`GET /studies/{study_id}/guide`)

**What Needs Frontend:**
- ❌ Automated study creation flow
- ❌ Interview guide editor

**Design Philosophy:**
- Designer mockups are **inspiration only**, not final design
- Team will test lightweight sketches with real users first
- Advanced customization (goal-based reframing, tone adjustment) **deferred**

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automated Study Creation (Priority: P1)

A researcher wants to create a research study by describing what they want to learn, then receive a generated interview guide as a starting point.

**Why this priority**: This is the primary improvement over manual study creation. Users can start with a structured guide instead of a blank page, reducing setup time from hours to minutes.

**Independent Test**: Can be fully tested by entering a research topic, confirming the backend returns a study with interview guide, and displaying both in the UI.

**Acceptance Scenarios**:

1. **Given** I am logged in and viewing the studies page, **When** I click "Generate Study," **Then** I see a prompt asking "What do you want to learn?"

2. **Given** I enter a research topic "How do people shop in supermarkets?" and submit, **When** processing finishes, **Then** I see a new study with a generated title and interview guide

3. **Given** I have entered an empty topic, **When** I attempt to submit, **Then** I see a validation error requiring a topic description

4. **Given** study generation is in progress, **When** I wait for the response, **Then** I see a loading indicator with estimated wait time

5. **Given** study generation fails, **When** the error is returned, **Then** I see a clear error message with an option to retry or create manually

---

### User Story 2 - Interview Guide Editing (Priority: P1)

A researcher needs to edit the generated interview guide to refine questions and tailor the content to their specific needs.

**Why this priority**: Automated generation provides a starting point, but researchers must customize to ensure quality. Without editing capability, the generated output is just a suggestion.

**Independent Test**: Can be tested by opening an interview guide, editing the markdown content, saving, and verifying changes persist.

**Acceptance Scenarios**:

1. **Given** I am viewing a study detail page with an interview guide, **When** I click "Edit Guide," **Then** I see the guide content in an editable text area

2. **Given** I am editing the interview guide, **When** I modify the markdown content (add/remove/edit questions), **Then** my changes appear in the editor

3. **Given** I have made changes to the guide, **When** I click "Save," **Then** the changes are saved to the backend and I see a success confirmation

4. **Given** I am editing the interview guide, **When** I navigate away without saving, **Then** I am warned about unsaved changes

5. **Given** I want to see how the guide will look to interviewees, **When** I click "Preview," **Then** I see a rendered markdown view of the guide

---

### User Story 3 - View Study with Interview Guide (Priority: P2)

A researcher needs to see the complete study details including the interview guide to review what interviewees will experience.

**Why this priority**: Once studies have guides, users need to view them. This is the foundation for the editing workflow.

**Independent Test**: Can be tested by navigating to a study and verifying the interview guide content is displayed.

**Acceptance Scenarios**:

1. **Given** a study has an interview guide, **When** I navigate to the study detail page, **Then** I see the interview guide content rendered below study metadata

2. **Given** a study does not have an interview guide yet, **When** I view the detail page, **Then** I see a message "No interview guide yet" with an "Add Guide" button

3. **Given** I am viewing a study with a guide, **When** I scroll through the page, **Then** I see the guide's welcome message, sections, and questions in a readable format

---

### User Story 4 - Manual Study Creation Fallback (Priority: P3)

A researcher needs to create a study manually if they prefer to start from scratch or if automated generation is unavailable.

**Why this priority**: Provides fallback when generation fails or when users want complete control from the start. Lower priority since automated generation is the preferred path.

**Independent Test**: Can be tested by choosing manual creation and verifying a blank study is created.

**Acceptance Scenarios**:

1. **Given** I am on the studies page, **When** I click "Create Study Manually," **Then** I see a form asking for title and description only

2. **Given** I fill in title and description, **When** I submit, **Then** a study is created without an interview guide

3. **Given** I have created a manual study, **When** I view it, **Then** I see "No interview guide yet" with an option to generate one or add manually

---

### Edge Cases

- What happens when study generation takes longer than 30 seconds? (Show extended loading state, timeout after 60s with error)
- What happens when study generation fails? (Show error message with retry option, fallback to manual creation)
- What happens when a user tries to save an empty interview guide? (Allow it - they may want to delete content)
- What happens when multiple users edit the same guide simultaneously? (Last write wins, no conflict resolution in MVP)
- What happens when guide content is extremely large? (No hard limit initially, monitor backend performance)
- What happens when network connection is lost during save? (Show error, preserve unsaved content in browser)
- What happens when user navigates away during study generation? (Show warning, allow cancellation)
- What happens when viewing a study that was created manually (no guide)? (Show "No guide yet" with options to generate or create manually)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a way to create a study by entering a research topic that triggers automated generation
- **FR-002**: System MUST call the backend `/orgs/{org_id}/studies/generate` endpoint with the user's topic
- **FR-003**: System MUST display the generated study title and interview guide after generation completes
- **FR-004**: System MUST provide an editable text area for interview guide markdown content
- **FR-005**: System MUST call the backend `PUT /studies/{study_id}/guide` endpoint to save guide edits
- **FR-006**: System MUST fetch and display existing interview guides using `GET /studies/{study_id}/guide`
- **FR-007**: System MUST show a markdown preview of the interview guide
- **FR-008**: System MUST validate that topic input is not empty before submission
- **FR-009**: System MUST show loading indicators during study generation (30-60 second wait)
- **FR-010**: System MUST show clear error messages when generation or save operations fail
- **FR-011**: System MUST warn users about unsaved changes before navigation away from the editor
- **FR-012**: System MUST support manual study creation (existing functionality) as a fallback option
- **FR-013**: System MUST display interview guide content on the study detail page when available
- **FR-014**: System MUST show "No guide yet" message when study has no associated guide

### Key Entities

- **Study**: A research project with a title, description of what the researcher wants to learn, and associated interview guide
- **Interview Guide**: The structured questions and instructions that will be used when conducting interviews for a study

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Researchers can create a study with generated interview guide in under 3 minutes from topic entry to viewing results
- **SC-002**: Users can edit and save interview guide changes in under 1 minute
- **SC-003**: Study generation completes within 60 seconds or provides clear timeout error
- **SC-004**: Users can preview interview guide markdown rendering in under 2 seconds
- **SC-005**: Zero data loss from unsaved changes - users are always warned before navigation
- **SC-006**: 90% of generation attempts succeed without errors

### Assumptions

- **Backend Endpoints**: The following endpoints exist and work (verified against codebase):
  - `POST /orgs/{org_id}/studies/generate` - Automated study generation
  - `GET /studies/{study_id}/guide` - Fetch guide
  - `PUT /studies/{study_id}/guide` - Save guide edits
- **Authentication**: Users are authenticated via Firebase with valid JWT tokens (verified: auth complete)
- **Organization Context**: Users belong to an organization and org_id is available (verified: multi-tenancy complete)
- **Generation Response Time**: Generation completes within 30-60 seconds (backend handles timeouts)
- **Markdown Format**: Interview guides are markdown text stored in `content_md` field
- **Markdown Preview**: Use standard markdown parser (e.g., marked, remark) for rendering
- **Concurrent Editing**: No conflict resolution - last write wins (acceptable for MVP)
- **UI Design**: Start with simple, lightweight sketches - not the full designer mockups
- **Advanced Features Deferred**: Goal-based reframing, tone adjustment, two-panel editor not in this iteration
- **Browser Support**: Modern browsers (Chrome, Firefox, Safari, Edge)
- **Manual Creation**: Existing manual study creation remains available as fallback

