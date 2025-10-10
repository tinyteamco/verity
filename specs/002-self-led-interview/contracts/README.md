# API Contracts: Self-Led Interview Execution

This directory contains API contract definitions for the self-led interview execution feature.

## Files

- `api-endpoints.yaml`: OpenAPI 3.0 specification for all new endpoints

## Implementation Workflow

When implementing these endpoints:

1. **Write BDD tests first** - See [quickstart.md](../quickstart.md#testing-workflow) for BDD cycle
2. **Check data model** - See [data-model.md](../data-model.md) for schema details
3. **Follow security patterns** - See section "Authorization Patterns" below
4. **Reference implementation code** - See [quickstart.md](../quickstart.md) Phases 3-5

**Example**: Implementing `GET /study/{slug}/start`:
- **Requirements**: [plan.md § Phase 3](../plan.md#phase-3-backend-api---public-interview-access-4-hours)
- **BDD test**: [quickstart.md § Step 3.1](../quickstart.md#step-31-write-bdd-tests-first)
- **Database model**: [data-model.md § Interview](../data-model.md#interview-new)
- **Implementation**: [quickstart.md § Step 3.2](../quickstart.md#step-32-implement-public-interview-router)

## Endpoint Categories

### Public Interview Access (No Auth)

These endpoints are accessible without authentication. The `access_token` acts as a credential.

1. **GET /study/{slug}/start?pid={external_id}**
   - Purpose: Reusable study link entry point
   - Creates Interview on-the-fly (or returns existing for same pid)
   - Redirects to pipecat with access_token
   - Deduplication: One Interview per (study_id, external_participant_id) pair

2. **GET /interview/{access_token}**
   - Purpose: Pipecat fetches interview guide
   - Returns Interview + Study data (including interview_guide.content_md)
   - Called by pipecat after redirect from Verity
   - Returns 404 if interview completed (token is single-use)

3. **POST /interview/{access_token}/complete**
   - Purpose: Pipecat notifies Verity of completion
   - Request body: transcript_url (required), recording_url (optional), notes (optional)
   - Verity expects GCS URLs, not file data
   - Idempotent: Safe to call multiple times

### Participant Identity (Firebase Auth Required)

These endpoints require Firebase Auth token with tenant type "interviewee".

4. **POST /interview/{access_token}/claim**
   - Purpose: Link completed interview to VerityUser
   - Creates VerityUser + ParticipantProfile if first sign-in
   - Updates ParticipantProfile.platform_identities if external_participant_id exists
   - Idempotent: Returns success if already claimed by same user

5. **GET /api/participant/dashboard**
   - Purpose: Participant views their interview history
   - Returns metadata only (no transcripts/audio)
   - Aggregates interviews across multiple platforms
   - Privacy-respecting: Masks external IDs, hides researcher info

### Researcher Endpoints (Firebase Auth + Org-Level Authorization)

These endpoints require Firebase Auth token with tenant type "organization" AND server-side org membership check.

6. **GET /api/orgs/{org_id}/studies/{study_id}/interviews**
   - Purpose: List all interviews for study
   - Requires org-level authorization (server-side check)
   - Optional status filter (pending/completed)
   - Returns interview metadata with artifact availability flags

7. **GET /api/orgs/{org_id}/interviews/{interview_id}/artifacts/{filename}**
   - Purpose: Download interview artifacts (audio/transcript)
   - Uses API proxy pattern (streams from GCS through Verity backend)
   - Requires org-level authorization (interview belongs to org)
   - Filenames: recording.wav, transcript.txt

## Authorization Patterns

### Public Endpoints

```
GET /study/{slug}/start
GET /interview/{access_token}
POST /interview/{access_token}/complete
```

- No authentication required
- `access_token` acts as bearer credential (UUID v4, high entropy)
- Single-use tokens (invalidated on completion)
- 24-hour expiration for uncompleted interviews

### Participant Endpoints

```
POST /interview/{access_token}/claim
GET /api/participant/dashboard
```

- Firebase Auth JWT token required (Bearer scheme)
- Tenant type: "interviewee"
- Token extracted and verified server-side
- VerityUser lookup by firebase_uid

### Researcher Endpoints

```
GET /api/orgs/{org_id}/studies/{study_id}/interviews
GET /api/orgs/{org_id}/interviews/{interview_id}/artifacts/{filename}
```

- Firebase Auth JWT token required (Bearer scheme)
- Tenant type: "organization"
- **Critical**: Server-side org membership check
  - Never trust client-provided org_id
  - Query database to verify user belongs to organization
  - Verify resource (study/interview) belongs to organization
- Multi-tenancy security (Constitution principle III)

## API Design Principles

### RESTful Resource Modeling

- **Studies**: `/api/orgs/{org_id}/studies/{study_id}`
- **Interviews**: `/api/orgs/{org_id}/interviews/{interview_id}` (org-scoped)
- **Public Interview Access**: `/interview/{access_token}` (flat, public)
- **Participant Profile**: `/api/participant/dashboard` (global, not org-scoped)

### Idempotency

- **POST /interview/{access_token}/complete**: Safe to call multiple times (same result)
- **POST /interview/{access_token}/claim**: Returns success if already claimed by same user
- **GET /study/{slug}/start**: Returns existing Interview if (study_id, external_participant_id) already exists

### Error Handling

Standard HTTP status codes:
- **200 OK**: Success
- **302 Found**: Redirect (reusable link access)
- **400 Bad Request**: Invalid state (e.g., interview not completed, already claimed by another user)
- **401 Unauthorized**: Missing or invalid Firebase Auth token
- **403 Forbidden**: User does not belong to organization
- **404 Not Found**: Resource not found
- **410 Gone**: Interview access token expired
- **429 Too Many Requests**: Rate limit or deduplication (participant already has pending interview)

### Content Types

- **JSON**: Default for all request/response bodies
- **audio/wav**: Audio artifacts (recording.wav)
- **text/plain**: Transcript artifacts (transcript.txt)

## Security Considerations

### CORS Configuration

Verity backend must allow requests from:
- Vite dev server: `http://localhost:5173`
- Verity production frontend: `https://app.verity.com`
- Pipecat production: `https://pipecat.verity.com`

Public endpoints must be accessible from pipecat domain.

### Multi-Tenancy

**Critical Security Rule**: VerityUsers are SEPARATE from Organization users

```
Organization Users (User table):
- Multi-tenant (organization_id scoped)
- Researcher/admin/member roles
- Access study/interview data within their organization

VerityUsers (verity_users table):
- Global (no organization_id)
- Participants can complete interviews across multiple organizations
- Only access their own claimed interviews
```

**Authorization Flow**:

```python
# Researcher endpoint
@app.get("/api/orgs/{org_id}/interviews/{interview_id}/artifacts/{filename}")
def download_artifact(
    org_id: int,
    interview_id: int,
    filename: str,
    current_user: User = Depends(get_current_org_user),  # Firebase Auth → User
    db: Session = Depends(get_db),
):
    # 1. Verify user belongs to org (server-side check)
    if current_user.organization_id != org_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    # 2. Verify interview belongs to org
    interview = db.query(Interview).join(Study).filter(
        Interview.id == interview_id,
        Study.organization_id == org_id
    ).first()

    if not interview:
        raise HTTPException(status_code=404, detail="Not found")

    # 3. Stream artifact from GCS (API proxy pattern)
    return stream_gcs_artifact(interview_id, filename)
```

### Token Expiration

- **Interview access_token**: 24 hours from creation (expires_at field)
- **Firebase Auth JWT**: 1 hour (default Firebase expiration)
- **GCS Signed URLs** (future): 1 hour (temporary artifact access)

## Integration with Pipecat

### Flow Diagram

```
┌─────────┐                                 ┌─────────┐
│ Verity  │                                 │ Pipecat │
└────┬────┘                                 └────┬────┘
     │                                           │
     │ 1. Redirect to pipecat with access_token │
     ├───────────────────────────────────────────>
     │   GET /?access_token=xxx&verity_api=...  │
     │                                           │
     │         2. Fetch interview data           │
     │<───────────────────────────────────────────┤
     │   GET /interview/{access_token}           │
     │                                           │
     │         3. Return guide + metadata        │
     ├───────────────────────────────────────────>
     │   200 {interview, study}                  │
     │                                           │
     │      [Participant completes interview]    │
     │                                           │
     │     4. Notify completion with URLs        │
     │<───────────────────────────────────────────┤
     │   POST /interview/{access_token}/complete │
     │   {transcript_url, recording_url, notes}  │
     │                                           │
     │             5. Acknowledge                │
     ├───────────────────────────────────────────>
     │   200 {message: "success"}                │
```

### Pipecat Changes Required

1. Add `POST /session/start` endpoint to initialize from access_token
2. Modify WebSocket handler to use session data (not local momtest files)
3. Add HTTP callback to Verity's `/interview/{access_token}/complete`
4. Update file storage paths to use interview_id (not session_id)
5. Configure VERITY_API_BASE environment variable

See [research.md](../research.md) for detailed pipecat integration requirements.

## Testing Strategy

### BDD Scenarios (Backend)

```gherkin
# backend/tests/features/interview_access.feature
Feature: Reusable Study Links

  Scenario: Participant accesses reusable link with pid parameter
    Given a study exists with slug "mobile-banking-study"
    When I access GET /study/mobile-banking-study/start?pid=prolific_abc123
    Then I should be redirected to pipecat with access_token in query params
    And an Interview should be created with external_participant_id "prolific_abc123"
    And the Interview status should be "pending"

  Scenario: Participant accesses same link twice (deduplication)
    Given a study exists with slug "mobile-banking-study"
    And an Interview exists for (study_id, external_participant_id "prolific_abc123")
    When I access GET /study/mobile-banking-study/start?pid=prolific_abc123
    Then I should be redirected to pipecat with the existing access_token
    And no new Interview should be created
```

### BDD Scenarios (Frontend E2E)

```gherkin
# frontend/tests/features/interview_list.feature
Feature: Researcher Views Interview Artifacts

  Scenario: Researcher views completed interviews
    Given I am logged in as a researcher in organization "Acme Research"
    And a study "Mobile Banking Study" has 3 completed interviews
    When I navigate to the study details page
    Then I should see a list of 3 interviews
    And each interview should show completion timestamp and platform source

  Scenario: Researcher downloads transcript
    Given I am viewing a completed interview
    When I click "View Transcript"
    Then I should see the transcript content inline
    And the transcript should be streamed from the backend API proxy
```

## Migration from Existing OpenAPI Spec

The existing `openapi.yaml` in the repository root defines similar endpoints. Changes:

**New Endpoints** (not in existing spec):
- `GET /study/{slug}/start` - Reusable link entry point
- `GET /interview/{access_token}` - Public interview data fetch
- `POST /interview/{access_token}/claim` - Claim interview
- `GET /api/participant/dashboard` - Participant profile

**Modified Existing Endpoints**:
- `/api/orgs/{org_id}/studies/{study_id}/interviews` - Add artifact availability flags

**No Changes**:
- `/interview/{access_token}/complete` - Already defined in existing spec
- Artifact download endpoints - Use existing pattern

## Next Steps

After planning phase:
1. Implement FastAPI routers for new endpoints (`backend/src/api/routers/`)
2. Write BDD tests before implementation (`backend/tests/features/`)
3. Implement frontend API client (`frontend/src/api/interviews.ts`)
4. Write frontend E2E tests (`frontend/tests/features/`)
5. Update existing OpenAPI spec in repository root
