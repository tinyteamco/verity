# Feature Specification: Self-Led Interview Execution

**Feature Branch**: `002-self-led-interview`
**Created**: 2025-10-10
**Status**: Draft
**Input**: User description: "Self-Led Interview Execution"

## Clarifications

### Session 2025-10-10

- **Q: How should artifacts be transferred from pipecat-momtest to Verity?** → **A: Shared storage pattern**. Pipecat writes artifacts to shared GCS bucket and provides storage paths in completion callback. Verity references the same storage (no download needed). Rationale: Avoids HTTP upload timeouts for large audio files, eliminates intermediate storage complexity, simpler than credential management for direct upload.

- **Q: What is the source of truth for transcripts?** → **A: Audio recording**. Pipecat provides streaming transcript (real-time, lower accuracy) in completion callback. Verity will generate batch transcript from stored audio later (higher accuracy, source of truth). Streaming transcript enables immediate viewing; batch transcript used for analysis.

- **Q: How does pipecat avoid App Engine timeouts during finalization?** → **A: Background task (out of scope for Verity)**. Pipecat returns 200 immediately on disconnect, then finalizes WebM container and uploads to shared storage in background task. Completion callback sent to Verity after upload completes. This is a pipecat implementation detail not affecting Verity's interface contract.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate and Share Interview Link (Priority: P1)

As a researcher, I create a unique shareable link for my study so that participants can access the interview without needing an account or login.

**Why this priority**: This is the foundation of the self-led interview flow. Without the ability to generate and share links, no interviews can happen. This is the critical path that enables all other functionality.

**Independent Test**: Can be fully tested by creating a study, generating an interview link, and verifying the link is accessible without authentication. Delivers immediate value by enabling researchers to distribute interviews.

**Acceptance Scenarios**:

1. **Given** I have a study with an interview guide, **When** I click "Generate Interview Link", **Then** I see a unique shareable URL that I can copy
2. **Given** I have generated an interview link, **When** I share it with a participant, **Then** they can access the interview without logging in
3. **Given** I have multiple active links for a study, **When** I view the study details, **Then** I see a list of all active interview links with creation dates

---

### User Story 2 - Participant Access & Redirect (Priority: P1)

As a participant, I click an interview link and Verity redirects me to the interview application with my unique access token.

**Why this priority**: This is Verity's core responsibility for participant access. Without correct redirect behavior, participants cannot reach the interview interface. Testable entirely within Verity (no pipecat dependency).

**Independent Test**: Access an interview link and verify Verity returns 302 redirect with correct URL format. Test error cases (completed, invalid token) show proper error pages. Fully testable via BDD without pipecat deployment.

**Acceptance Scenarios**:

1. **Given** I have a valid interview link, **When** I access it, **Then** Verity returns 302 redirect to `{PIPECAT_BASE_URL}?token={access_token}`
2. **Given** an interview is already completed, **When** I try to access the link, **Then** Verity shows "Interview already completed" page (no redirect)
3. **Given** a link is invalid or expired, **When** I access it, **Then** Verity shows error message page (no redirect)
4. **Given** a study has been deleted, **When** I try to access an interview link for it, **Then** Verity shows "Study no longer available" message

---

### User Story 2.5 - Interview Data API Contract (Priority: P1)

As the pipecat-momtest application, I fetch interview data via Verity's public API to conduct the interview.

**Why this priority**: This is the interface contract pipecat depends on. Without this working, pipecat cannot retrieve interview guides. Testable entirely within Verity via API endpoint tests.

**Independent Test**: Call the public API endpoints with various tokens and verify responses match contract. Fully testable via BDD without pipecat deployment.

**Acceptance Scenarios**:

1. **Given** pipecat calls `GET /interview/{token}`, **When** token is valid, **Then** Verity returns 200 with `{study_title, interview_guide}`
2. **Given** pipecat calls with completed interview token, **When** request is made, **Then** Verity returns 410 Gone
3. **Given** pipecat calls with invalid token, **When** request is made, **Then** Verity returns 404
4. **Given** study has been deleted, **When** pipecat fetches interview data, **Then** Verity returns 410 Gone

---

### User Story 3 - Completion Callback Handling (Priority: P2)

As the system, I accept completion callbacks from pipecat with storage paths to artifacts, mark interviews complete, and make recordings available to researchers.

**Why this priority**: This completes the interview lifecycle from Verity's perspective. Verity must correctly process completion callbacks to make artifacts available. Testable via mock callback requests.

**Independent Test**: Send mock completion callback with storage paths to Verity and verify interview is marked complete and artifacts are accessible. Fully testable via BDD with stub requests (no pipecat dependency).

**Acceptance Scenarios**:

1. **Given** Verity receives `POST /interview/{token}/complete` with storage paths, **When** callback is valid, **Then** marks interview completed and stores artifact references
2. **Given** completion callback includes streaming transcript, **When** processed, **Then** transcript is immediately viewable by researcher
3. **Given** completion callback includes audio storage path, **When** processed, **Then** audio is downloadable by researcher
4. **Given** pipecat retries completion callback, **When** interview already complete, **Then** Verity returns 200 (idempotent, no error)
5. **Given** storage paths reference missing files, **When** researcher tries to access them, **Then** marks interview as "completion_pending" and logs error

---

### User Story 4 - View Interview Submissions (Priority: P2)

As a researcher, I view all interview submissions for my study so I can track participation and access recordings and transcripts for analysis.

**Why this priority**: This enables researchers to see the results of their interviews. While important, it's secondary to getting interviews out to participants (US1-US3). Can initially be a simple list view.

**Independent Test**: After participants complete interviews (from US3), log in as the researcher and verify all completed interviews appear in a list with access to transcripts and recordings. Delivers value by providing visibility into collected data.

**Acceptance Scenarios**:

1. **Given** I have a study with completed interviews, **When** I navigate to the study details page, **Then** I see a list of all interviews with their completion status and completion timestamp
2. **Given** an interview has artifacts, **When** I click on the interview, **Then** I can view the transcript inline and download the audio file
3. **Given** I have both completed and pending interviews, **When** I view the interview list, **Then** I can filter by status (completed/pending)

---

### User Story 5 - Reusable Study Link for Recruitment Platforms (Priority: P2)

As a researcher, I generate a reusable study link with a readable slug that recruitment platforms can use to dynamically send participants to my study without pre-generating individual interview links.

**Why this priority**: Critical for integration with external recruitment platforms (Prolific, UserTesting, Respondent) that manage participant distribution and need a single reusable URL. This enables scalable participant recruitment without manual link generation.

**Independent Test**: Configure a study with a reusable link, substitute a participant ID into the URL template, access it, and verify a new interview is created on-the-fly. Delivers value by enabling platform integrations.

**Acceptance Scenarios**:

1. **Given** I have created a study with slug "freelancer-tool-selection", **When** I view study settings, **Then** I see a reusable link template: `https://verity.com/study/freelancer-tool-selection/start?pid={{PARTICIPANT_ID}}`
2. **Given** a recruitment platform uses the reusable link with pid=prolific_123, **When** the participant clicks it, **Then** Verity creates a new interview on-the-fly and redirects to pipecat
3. **Given** the same participant ID accesses the link twice, **When** the second access occurs, **Then** they see "Interview already completed" (no duplicate interviews)
4. **Given** an interview was completed via reusable link, **When** I view interviews, **Then** I see the external participant ID (e.g., "prolific_123") associated with the interview

---

### User Story 6 - API for Programmatic Interview Link Generation (Priority: P2)

As an external recruitment platform, I programmatically generate interview links via API when I have a confirmed participant so I can control distribution timing and track individual assignments.

**Why this priority**: Required for platforms that manage scheduling (Respondent.io, UserInterviews) and need to generate links on-demand when sessions are booked. Enables quota management and advanced tracking.

**Independent Test**: Call the API with valid credentials and participant metadata, receive a unique interview URL, and verify the participant can access it. Delivers value for platforms with complex scheduling needs.

**Acceptance Scenarios**:

1. **Given** I have Verity API credentials, **When** I POST to `/api/orgs/{org_id}/studies/{study_id}/interviews` with external_participant_id, **Then** I receive a unique interview URL
2. **Given** I have generated a link via API, **When** the participant completes the interview, **Then** I receive a webhook notification with the external_participant_id I provided
3. **Given** I generate multiple links for the same study, **When** I list interviews via API, **Then** I see all generated links with their status and external IDs
4. **Given** a link is generated but never used, **When** I check its status, **Then** it shows as "pending" with no completion data

---

### User Story 7 - Pre-Interview Optional Sign-In (Priority: P2)

As a participant, I have the option to sign in before starting an interview so my participation is automatically tracked across all platforms without needing to claim it afterward.

**Why this priority**: Improves user experience for repeat participants and enables Verity to build a participant database. While optional (anonymous flow still works), this provides long-term value for participant retention.

**Independent Test**: Access an interview link while signed in and verify the interview is automatically associated with the user account. Delivers value by simplifying participation tracking.

**Acceptance Scenarios**:

1. **Given** I click an interview link, **When** the interstitial page loads, **Then** I see options: "Continue as Guest" or "Sign In"
2. **Given** I choose "Sign In" and authenticate, **When** I complete the interview, **Then** it automatically appears in my participation history
3. **Given** I choose "Continue as Guest", **When** I complete the interview, **Then** I still see an option to claim it afterward
4. **Given** I am already signed in to Verity, **When** I access a new interview link, **Then** my session is recognized and the interview is auto-linked

---

### User Story 8 - Post-Interview Claim and Cross-Platform Identity (Priority: P3)

As a participant, I can sign in after completing anonymous interviews to claim them and view my complete participation history across all platforms (Prolific, Respondent, direct links) in one dashboard.

**Why this priority**: Enables Verity to build participant profiles and provide value to repeat participants. Supports cross-platform identity reconciliation. Nice-to-have feature that can be deferred.

**Independent Test**: Complete multiple anonymous interviews from different sources, sign in once, and verify all interviews appear in a unified dashboard with their original platform sources visible.

**Acceptance Scenarios**:

1. **Given** I have completed an interview anonymously from Prolific (external_id: prolific_123), **When** I click "Sign In to Track My Interviews" on the thank-you page, **Then** I can authenticate and the interview is linked to my Verity account
2. **Given** I am signed in and complete an interview from Respondent (external_id: respondent_789), **When** I view my dashboard, **Then** I see both Prolific and Respondent interviews with their platform sources labeled
3. **Given** I have claimed multiple interviews across platforms, **When** I view my profile, **Then** I see my total participation count and completion dates
4. **Given** I complete another interview from Prolific with a different external_id, **When** it auto-links to my Verity account, **Then** the system knows both Prolific IDs belong to the same person

---

### User Story 9 - Participant Profile Dashboard (Priority: P3)

As a signed-in participant, I view my complete participation history across all studies and platforms so I can track my contributions and understand my involvement.

**Why this priority**: Provides value to engaged participants and helps Verity build a participant community. Can be deferred until participant sign-in patterns are established.

**Independent Test**: Sign in as a participant who has completed interviews across multiple platforms and verify all participation data is visible. Delivers value for participant engagement and retention.

**Acceptance Scenarios**:

1. **Given** I am signed in as a participant, **When** I navigate to "My Participation", **Then** I see a list of all interviews I've completed with study titles and dates
2. **Given** I view my participation history, **When** I see an interview, **Then** I can identify which platform it came from (Prolific, Respondent, direct link, etc.)
3. **Given** I have completed interviews across 3 different platforms, **When** I view my profile stats, **Then** I see total participation count aggregated across all sources
4. **Given** I want to review a past interview, **When** I click on it, **Then** I can view the study title and date (but not transcript - that belongs to the researcher)

---

### Edge Cases

- What happens when a participant tries to access the same interview link twice (after completion)?
  - **Handling**: Verity checks interview status before redirect; if completed, show message "This interview has already been completed" instead of redirecting to pipecat

- What happens when pipecat-momtest's completion callback fails to reach Verity?
  - **Handling**: Pipecat retries the callback with exponential backoff; Verity handles idempotent completion (FR-034) so duplicate calls don't cause errors; artifacts remain in shared storage accessible by both apps

- What happens when storage paths in completion callback reference missing files?
  - **Handling**: Verity marks interview as "completion_pending"; logs error with storage path for debugging; provides admin interface to verify storage and update paths; researcher sees "artifacts pending" status until resolved

- What happens when a researcher deletes a study that has pending interview links?
  - **Handling**: Interview links become invalid; participants see "This study is no longer available" message from Verity (before redirect to pipecat)

- How does the system handle participants navigating away mid-interview?
  - **Handling**: Pipecat-momtest handles this; on disconnect, saves recording/transcript and sends completion callback to Verity; partial interviews are stored as completed

- What happens when pipecat-momtest is unavailable (deployment down)?
  - **Handling**: Verity redirect fails; participant sees browser error; no graceful degradation in MVP; researcher can regenerate links once pipecat is back online

- What happens when multiple researchers from the same organization try to view the same interview simultaneously?
  - **Handling**: Standard concurrent read access; no locking needed for viewing

- How does the system handle interview links shared on social media or public forums?
  - **Handling**: Links work for anyone with the URL; no additional restrictions in MVP; one-time use per link (marked complete after first session); rate limiting may be added later

- What happens when the same external participant ID accesses a reusable study link multiple times?
  - **Handling**: First access creates interview and redirects; subsequent accesses show "Interview already completed" (deduplication by external_participant_id + study_id)

- How does the system prevent participant ID spoofing on reusable links?
  - **Handling**: No validation in MVP - reusable links are for trusted recruitment platforms; external_id is stored for tracking, not authentication; future enhancement could add HMAC signatures

- What happens when a signed-in participant accesses a link with an external_id?
  - **Handling**: Interview is linked to both verity_user_id AND external_participant_id; enables cross-platform identity reconciliation

- How does the system handle API rate limiting for programmatic link generation?
  - **Handling**: Standard API rate limits apply (per organization); prevents abuse while allowing legitimate bulk operations; exact limits TBD based on usage patterns

- What happens when a recruitment platform webhook endpoint is unreachable?
  - **Handling**: Retry with exponential backoff (3 attempts over 1 hour); log failure; provide admin interface to manually retry; interview completion proceeds regardless of webhook success

## Integration Architecture

### Overview

This feature supports two primary integration patterns:
1. **Pipecat-momtest Integration**: Live interview execution (separate application)
2. **Recruitment Platform Integration**: Participant sourcing via external platforms

### Recruitment Platform Integration Patterns

External recruitment platforms (Prolific, UserTesting, Respondent.io, UserInterviews) integrate with Verity to send participants to studies. Verity supports two patterns based on platform capabilities:

#### Pattern 1: Reusable Study Link (URL Substitution)

**Best for**: Platforms that manage participant distribution via URL redirection (Prolific, UserTesting)

**How it works**:
```
1. Researcher creates study with slug: "freelancer-tool-selection"
2. Verity provides template URL:
   https://verity.com/study/freelancer-tool-selection/start?pid={{PARTICIPANT_ID}}

3. Platform substitutes participant ID:
   Prolific uses: https://verity.com/study/freelancer-tool-selection/start?pid={{%PROLIFIC_PID%}}
   UserTesting uses: https://verity.com/study/freelancer-tool-selection/start?pid={{tester_id}}

4. When participant clicks:
   - Verity creates Interview record on-the-fly
   - Stores external_participant_id (e.g., "prolific_abc123")
   - Generates unique access_token
   - Redirects 302 to: https://interview.verity.com?token={access_token}

5. Participant completes interview → Pipecat callback → Verity
6. (Optional) Verity webhook to platform: "Interview completed by prolific_abc123"
```

**Deduplication**: External_participant_id + study_id ensures one interview per participant per study

**Benefits**:
- Simple integration (no API auth required)
- Works with platforms that only support URL templates
- Readable, shareable URLs using study slug

#### Pattern 2: Programmatic API Link Generation

**Best for**: Platforms that manage scheduling and need on-demand link generation (Respondent.io, UserInterviews)

**How it works**:
```
1. Platform has Verity API credentials (org-level API key)

2. When participant books session:
   POST /api/orgs/{org_id}/studies/{study_id}/interviews
   Authorization: Bearer {api_key}
   Body: {
     "external_participant_id": "respondent_user_456",
     "metadata": {
       "source": "respondent.io",
       "session_id": "booking_xyz"
     }
   }

3. Verity creates Interview record immediately:
   Response: {
     "interview_id": "uuid-123",
     "interview_url": "https://verity.com/interview/{access_token}",
     "created_at": "2025-10-10T18:00:00Z"
   }

4. Platform sends unique URL to participant via email/platform

5. Participant completes → Pipecat callback → Verity

6. Verity webhook to platform:
   POST {platform_webhook_url}
   Headers: X-Verity-Signature: {HMAC}
   Body: {
     "interview_id": "uuid-123",
     "external_participant_id": "respondent_user_456",
     "completed_at": "2025-10-10T19:00:00Z",
     "metadata": {"session_id": "booking_xyz"}
   }
```

**Benefits**:
- Platform controls when links are generated
- Supports quota management (max completions)
- Enables pre-booking workflows
- Rich metadata tracking

#### Completion Webhooks (Optional)

Platforms can register webhook URLs to receive completion notifications:

**Webhook Configuration** (per study):
```json
{
  "webhook_url": "https://platform.com/webhooks/verity-completion",
  "webhook_secret": "shared_secret_for_hmac",
  "events": ["interview.completed"]
}
```

**Webhook Payload**:
```json
{
  "event": "interview.completed",
  "interview_id": "uuid-123",
  "study_id": "study-456",
  "external_participant_id": "prolific_abc123",
  "completed_at": "2025-10-10T19:00:00Z",
  "transcript_available": true,
  "recording_available": true,
  "metadata": {}  // Platform-provided metadata from link generation
}
```

**Webhook Signature** (HMAC-SHA256):
```
X-Verity-Signature: sha256={HMAC(webhook_secret, payload)}
```

**Retry Logic**: 3 attempts with exponential backoff (immediate, 5min, 1hr)

### Interactive Interview Component (Pipecat-momtest)

The **interactive interview component** (pipecat-momtest: https://github.com/tinyteamco/pipecat-momtest) is a **separate application** and is **out of scope** for this feature. This feature focuses on the orchestration layer: link generation, interview access, and results collection.

**Architectural Decision**: Verity and pipecat-momtest communicate via URL-passing using a "pull" pattern where the interview component fetches data from Verity and posts completion back.

### Integration Flow

```
1. Researcher generates interview link in Verity
   └─> Verity creates Interview record with access_token

2. Participant clicks link
   └─> Verity redirects to: https://interview.verity.com?token={access_token}

3. Pipecat-momtest fetches interview data
   └─> GET https://api.verity.com/interview/{access_token}
       Response: {
         "study_title": "Freelancer Tool Selection Research",
         "interview_guide": "# Welcome\n\nThank you for participating...\n\n## Section 1: Background\n\n1. Tell me about..."
       }

4. Pipecat-momtest conducts live interview
   └─> WebSocket connection, real-time transcription, AI conversation

5. Interview completes (participant disconnects)
   └─> Pipecat returns 200 immediately to client
   └─> Background task: finalize WebM, write to shared GCS bucket

6. Pipecat-momtest notifies Verity of completion
   └─> POST https://api.verity.com/interview/{access_token}/complete
       Body: {
         "session_id": "uuid-123",
         "transcript_streaming": "Interviewer: Welcome...\nParticipant: Hi...",
         "audio_storage_path": "gs://shared-bucket/interviews/{session_id}/recording.webm",
         "completed_at": "2025-10-10T18:30:00Z"
       }

7. Verity processes completion
   └─> Store streaming transcript (immediate viewing)
   └─> Store audio storage path reference
   └─> Mark interview as completed
   └─> (Later) Generate batch transcript from audio (async job)
```

### API Contracts

#### Verity → Pipecat (Interview Data Fetch)

**Endpoint**: `GET /interview/{access_token}`
- **Auth**: None required (public access via unique token)
- **Response**:
```json
{
  "study_title": "Freelancer Tool Selection Research",
  "interview_guide": "# Welcome\n\nThank you for participating...\n\n## Section 1: Background\n\n1. Tell me about..."
}
```
- **Errors**:
  - `404`: Invalid or expired access token
  - `410`: Interview already completed

**Notes**:
- `study_title`: Display name of the study
- `interview_guide`: Markdown content from the study's interview guide (replaces hardcoded prompts in pipecat)
- System prompt behavior: Pipecat determines how to use the guide (current implementation has hardcoded system prompt in `_system.md`)

#### Pipecat → Verity (Completion Callback)

**Endpoint**: `POST /interview/{access_token}/complete`
- **Auth**: None required (callback from trusted interview component)
- **Body**:
```json
{
  "session_id": "uuid-abc-123",
  "transcript_streaming": "Interviewer: Welcome to the study...\nParticipant: Hi, thanks...",
  "audio_storage_path": "gs://shared-bucket/interviews/{session_id}/recording.webm",
  "completed_at": "2025-10-10T18:30:00Z"
}
```
- **Response**: `200 OK`
- **Errors**:
  - `404`: Invalid access token
  - `409`: Interview already marked complete (idempotent, returns 200)

**Notes**:
- `transcript_streaming`: Real-time transcript from pipecat (lower accuracy, immediate availability)
- `audio_storage_path`: GCS path to finalized audio file in shared bucket
- Verity will generate batch transcript from audio asynchronously (source of truth)

### Implementation Notes

**Shared Storage Architecture**:
- Both Verity and pipecat-momtest access same GCS bucket (`gs://shared-bucket/interviews/`)
- IAC grants both applications read/write access to this bucket (one-time configuration)
- Pipecat writes finalized artifacts directly to GCS (no HTTP upload to Verity)
- Verity references storage paths (no download, just path storage)
- Avoids HTTP upload timeouts, eliminates intermediate storage complexity

**Current Pipecat-momtest Architecture**:
- Hardcoded interview scripts in `/backend/src/momtest/prompts/*.md`
- WebSocket endpoint: `/ws/{momtest_id}/{session_id}`
- Completion handler currently blocks on finalization (causes App Engine timeouts)
- Saves to local storage or environment-specific bucket

**Required Changes to Pipecat-momtest** (out of scope for Verity):
1. Fetch interview guide dynamically from Verity `GET /interview/{token}`
2. Make disconnect handler non-blocking (return 200 immediately)
3. Background task: finalize WebM container → write to shared GCS bucket → POST completion callback
4. Use Verity access tokens in WebSocket flow
5. Include streaming transcript and storage path in completion callback

**Required Changes to Verity**:
1. Add `GET /interview/{token}` endpoint (public, returns guide data)
2. Add `POST /interview/{token}/complete` endpoint (accepts storage paths, not URLs)
3. Store artifact storage path references (no download needed)
4. Generate batch transcript from stored audio (async job)
5. Generate redirect URLs to pipecat-momtest with access token

**Configuration**:
- Environment variable: `PIPECAT_BASE_URL` (e.g., `https://interview.verity.com`)
- Shared GCS bucket: `gs://shared-bucket/interviews/` (configured via IAC)

**Rationale for Shared Storage**:
- Avoids HTTP upload timeouts for large audio files (5-10 MB for 5-10 minute interviews)
- Eliminates credential complexity (both apps access same bucket via service accounts)
- Pipecat can finalize WebM asynchronously without blocking disconnect
- Single source of truth for artifacts (no download/sync failures)

## Requirements *(mandatory)*

### Functional Requirements

**Link Generation & Management**

- **FR-001**: Researchers MUST be able to generate unique interview links for any study they have access to
- **FR-002**: Each interview link MUST contain a unique access token that cannot be guessed or enumerated
- **FR-003**: Researchers MUST be able to view all active interview links for their studies
- **FR-004**: System MUST display when each interview link was created and by whom
- **FR-005**: Researchers MUST be able to deactivate an interview link without deleting the interview data

**Participant Access**

- **FR-006**: Participants MUST be able to access an interview using only the unique link (no authentication required)
- **FR-007**: System MUST display the study title and full interview guide when a participant accesses a valid link
- **FR-008**: System MUST show a clear error message when an interview link is invalid, expired, or deactivated
- **FR-009**: System MUST prevent access to interview links from studies that have been deleted

**Interview Completion (via Pipecat-momtest Callback)**

- **FR-010**: System MUST accept completion callbacks from pipecat-momtest containing storage paths, streaming transcript, and completion timestamp
- **FR-011**: System MUST validate access tokens in completion callbacks match existing pending interviews
- **FR-012**: System MUST prevent duplicate interview access after completion (show "already completed" message)
- **FR-013**: System MUST handle idempotent completion callbacks gracefully (no errors on retry)
- **FR-014**: System MUST store the completion timestamp when receiving completion callback from pipecat-momtest

**Artifact Management (Transcripts & Recordings)**

- **FR-015**: System MUST store artifact storage path references (GCS paths) provided in completion callback
- **FR-016**: System MUST store streaming transcript from completion callback for immediate researcher viewing
- **FR-017**: Researchers MUST be able to view streaming transcripts inline and download audio recordings from shared storage
- **FR-018**: System MUST generate batch transcript from stored audio asynchronously (source of truth, higher accuracy than streaming transcript)

**Interview Tracking**

- **FR-019**: Researchers MUST be able to view a list of all interviews (pending and completed) for their studies
- **FR-020**: System MUST display interview status (pending, completed, completion_pending) and completion date if applicable
- **FR-021**: Researchers MUST be able to filter interviews by status
- **FR-022**: System MUST show which interview link was used to access each interview
- **FR-023**: System MUST display transcript content inline for completed interviews
- **FR-024**: System MUST provide download links for audio recordings from completed interviews

**Optional Participant Sign-In**

- **FR-025**: Participants MAY optionally sign in to associate an interview with their account
- **FR-026**: Participants who sign in MUST be able to view their participation history across all studies
- **FR-027**: System MUST allow participants to claim previously completed anonymous interviews after signing in

**Security & Privacy**

- **FR-028**: System MUST enforce multi-tenancy: researchers can only view interviews for studies within their organization
- **FR-029**: System MUST NOT expose participant identity unless they explicitly sign in
- **FR-030**: Interview links MUST be accessible over HTTPS only (no unencrypted access)

**Integration Requirements (Pipecat-momtest)**

- **FR-031**: System MUST provide public `GET /interview/{access_token}` endpoint that returns study title and interview guide content (no authentication required)
- **FR-032**: System MUST provide public `POST /interview/{access_token}/complete` endpoint that accepts completion callback with storage paths and streaming transcript
- **FR-033**: System MUST accept GCS storage path format (`gs://bucket/path`) in completion callback for audio artifacts
- **FR-034**: System MUST mark interviews as completed and store completion timestamp when receiving completion callback (covered by FR-014)
- **FR-035**: Generated interview links MUST redirect to pipecat-momtest with access token as query parameter (e.g., `{PIPECAT_BASE_URL}?token={access_token}`)
- **FR-036**: System MUST support CORS on public interview endpoints to allow cross-origin requests from pipecat-momtest application
- **FR-037**: System MUST reference artifacts in shared storage via path (no download or copy needed)

**Recruitment Platform Integration (Reusable Links)**

- **FR-038**: System MUST provide reusable study links using study slug format: `https://verity.com/study/{slug}/start?pid={{PARTICIPANT_ID}}`
- **FR-039**: System MUST create Interview records on-the-fly when reusable study links are accessed with external_participant_id
- **FR-040**: System MUST store external_participant_id from query parameter when creating interviews via reusable links
- **FR-041**: System MUST prevent duplicate interviews for the same external_participant_id + study_id combination (show "already completed" message)
- **FR-042**: System MUST support optional interstitial page before interview showing "Continue as Guest" or "Sign In" options

**Recruitment Platform Integration (API)**

- **FR-043**: System MUST provide authenticated API endpoint `POST /api/orgs/{org_id}/studies/{study_id}/interviews` for programmatic interview link generation
- **FR-044**: API MUST accept external_participant_id and optional metadata when generating interview links
- **FR-045**: API MUST return unique interview URL and interview_id upon successful link generation
- **FR-046**: System MUST enforce organization-level API rate limits for programmatic link generation
- **FR-047**: System MUST support webhook configuration per study (webhook_url, webhook_secret, events)
- **FR-048**: System MUST send completion webhooks to configured URLs with HMAC signature verification
- **FR-049**: System MUST retry failed webhooks with exponential backoff (3 attempts: immediate, 5min, 1hr)
- **FR-050**: System MUST log webhook delivery status and provide admin interface for manual retry

**Participant Identity & Sign-In**

- **FR-051**: Participants MUST be able to optionally sign in before starting an interview (pre-interview sign-in)
- **FR-052**: System MUST auto-link interviews to signed-in participants (populate verity_user_id on Interview creation)
- **FR-053**: System MUST display sign-in/register option on interview completion page for anonymous participants
- **FR-054**: System MUST allow claiming anonymous interviews by linking them to verity_user_id after authentication
- **FR-055**: Interview records MUST store BOTH external_participant_id (from platform) AND verity_user_id (from sign-in) when available
- **FR-056**: System MUST support cross-platform identity reconciliation (same verity_user_id across different external_participant_ids)
- **FR-057**: Signed-in participants MUST be able to view complete participation history across all platforms and studies
- **FR-058**: Participation dashboard MUST display platform source for each interview (e.g., "Prolific", "Respondent", "Direct")
- **FR-059**: System MUST aggregate participation statistics across all platforms for signed-in users

### Key Entities

- **Interview**: Represents a single participant's response session for a study. Contains access token, status (pending/completed/completion_pending), completion timestamp, pipecat session ID, external_participant_id (from recruitment platform, nullable), verity_user_id (from sign-in, nullable), source platform identifier, and optional metadata. Linked to exactly one Study. Can have both external_participant_id AND verity_user_id for cross-platform identity reconciliation.

- **Share Link**: A generated unique URL for accessing a study's interview. Contains creation timestamp, creator identifier, active/deactivated status, and generation method (manual, API). Multiple share links can exist for one Study. Used for pre-generated interview links via UI or API.

- **Transcript**: Text artifact from a completed interview showing conversation between participant and AI interviewer. Two types: (1) **Streaming transcript** from pipecat (real-time, lower accuracy, immediate availability) stored directly in database; (2) **Batch transcript** generated from audio (higher accuracy, source of truth) created asynchronously. Linked to exactly one Interview.

- **Recording**: Audio file artifact from a completed interview. Contains file metadata (format, storage path) and GCS path reference (`gs://shared-bucket/interviews/{session_id}/recording.webm`). Audio stored in shared GCS bucket accessible by both Verity and pipecat. Linked to exactly one Interview.

- **VerityUser**: Represents a signed-in participant's identity. Contains email (unique), name, Firebase UID, created_at timestamp. Enables cross-platform participation tracking. Separate from Organization users (researchers).

- **ParticipantProfile**: Extended profile data for VerityUser. Contains demographics (optional), preferences, total participation count, platform affiliations (maps verity_user_id to external_participant_ids from different platforms). Enables participant discovery and matching for future studies.

- **WebhookConfig**: Per-study webhook configuration for recruitment platforms. Contains webhook_url, webhook_secret (for HMAC), enabled events (interview.completed), retry settings, and delivery log. Enables integration with external platforms for completion notifications.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Researchers can generate an interview link and copy it to their clipboard in under 10 seconds
- **SC-002**: Participants can access an interview within 5 seconds of clicking a link (no authentication delays, no authentication required)
- **SC-003**: Participants can complete interviews automatically without manual upload steps (pipecat handles recording/transcript)
- **SC-004**: Researchers can view all completed interviews for a study and access recordings within 3 clicks
- **SC-005**: 95% of interview link accesses successfully redirect to pipecat and load the interview
- **SC-006**: Interview completion rate increases by measuring submissions vs. link accesses (baseline to be established)
- **SC-007**: External recruitment platforms can generate interview links programmatically in under 2 seconds via API
- **SC-008**: Reusable study links create interview records on-the-fly without pre-generation (unlimited participants per link)
- **SC-009**: Participants can sign in and claim anonymous interviews in under 30 seconds
- **SC-010**: Signed-in participants can view participation history across all platforms in a single dashboard

## Scope & Constraints

### In Scope

- Link generation and basic management (manual UI, API, reusable study links)
- Public access to interviews via unique tokens (no authentication required)
- Pipecat-momtest integration (callback-based completion, artifact download)
- Interview submission and status tracking (pending, completed, completion_pending)
- Interview list and detail views for researchers (transcripts inline, audio download)
- Recruitment platform integration (reusable slug-based links, API, webhooks)
- External participant ID tracking (Prolific, Respondent, etc.)
- Optional participant sign-in (pre-interview and post-interview claim)
- Cross-platform identity reconciliation (verity_user_id links multiple external_ids)
- Participant profile dashboard (view participation history across platforms)

### Out of Scope (Separate Components/Future Features)

**Separate Application (Not Part of This Feature)**:
- Interactive interview component (live recording, transcription UI) - separate app
- In-browser audio recording interface - handled by separate component
- Real-time transcript display during interview - handled by separate component

**Deferred to Future Iterations**:
- Link expiration dates and auto-deactivation
- Bulk link generation UI (API supports it, but no batch UI)
- Live interview progress tracking from Verity dashboard (real-time status updates)
- Multi-file uploads per interview (single transcript + audio only)
- Advanced analytics (completion rates, drop-off analysis, platform comparison)
- Email notifications when interviews are completed
- AI-generated interview summaries and insights
- Participant demographic filtering and matching for researchers
- Participant incentive/compensation tracking
- Interview quota limits per study (unlimited in MVP)
- HMAC signature verification for reusable links (trusted platforms only in MVP)
- Participant consent management and GDPR compliance tooling

### Constraints

- Pipecat-momtest handles recording and writes to shared GCS bucket (no size limit imposed by Verity)
- Only audio file formats supported (WebM from pipecat, no video)
- Two transcripts per interview: streaming (immediate, lower accuracy) and batch (async, source of truth)
- One audio recording per interview (no multi-part submissions in MVP)
- Interview links cannot be edited after creation (must deactivate and create new)
- Reusable study links require study to have a unique slug (auto-generated from title)
- External participant IDs are not validated (trusted recruitment platforms assumption)
- API rate limits apply per organization (exact limits TBD based on usage patterns)
- Webhook retries limited to 3 attempts over 1 hour (after that, manual retry required)
- Shared GCS bucket requires IAC configuration granting access to both Verity and pipecat service accounts

## Dependencies & Assumptions

### Dependencies

- **Study Management**: Studies with interview guides and unique slugs must exist before interview links can be generated
- **Authentication System**: Firebase Auth for optional participant sign-in (VerityUser accounts) and researcher access control
- **Shared Object Storage**: GCS bucket accessible by both Verity and pipecat-momtest service accounts (configured via IAC)
- **Pipecat-momtest**: Separate application for conducting live interviews (https://github.com/tinyteamco/pipecat-momtest) - requires deployment, configuration to call Verity's completion callback, and access to shared GCS bucket
- **Organization API Keys**: Required for programmatic interview link generation via external platforms

### Assumptions

- Pipecat-momtest application is deployed and accessible (handles live recording and transcription)
- Both Verity and pipecat have read/write access to shared GCS bucket (configured via IAC)
- Pipecat finalizes WebM container asynchronously after participant disconnect (background task)
- Researchers will distribute interview links via recruitment platforms (Prolific, Respondent), email, messaging, or social media
- Recruitment platforms are trusted (no HMAC verification on reusable links in MVP)
- External participant IDs from platforms are unique within that platform's namespace
- Pipecat-momtest produces artifacts in compatible format (WebM audio, plain text streaming transcript)
- Network connectivity is sufficient for real-time WebSocket communication during interviews
- Participants complete interviews in a single session via pipecat-momtest (no save/resume in MVP)
- Organization members have sufficient permissions to generate links and configure webhooks for studies they can access
- Pipecat-momtest callback URLs are reachable from Verity's backend (no firewall blocking)
- Webhook endpoints provided by recruitment platforms are reachable from Verity's backend
- Participants who sign in use valid email addresses (Firebase Auth handles validation)

## Open Questions

None. All critical decisions have been made based on industry standards and the existing backend implementation.
