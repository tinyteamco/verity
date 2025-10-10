# Data Model: Self-Led Interview Execution

**Date**: 2025-10-10
**Feature**: [spec.md](./spec.md)

This document defines the database schema and entity relationships for the self-led interview execution feature.

---

## Entity Relationship Diagram

```
┌─────────────────────┐
│   Organization      │
└──────────┬──────────┘
           │ 1
           │
           │ *
┌──────────┴──────────┐
│      Study          │
│  + slug (unique)    │
│  + participant_     │
│    identity_flow    │
└──────────┬──────────┘
           │ 1
           │
           │ *
┌──────────┴──────────┐           ┌─────────────────────┐
│    Interview        │ *       1 │    VerityUser       │
│  + access_token     ├───────────┤  + firebase_uid     │
│  + status           │           │  + email            │
│  + external_        │           └──────────┬──────────┘
│    participant_id   │                      │ 1
│  + verity_user_id   │                      │
│  + transcript_url   │                      │ 1
│  + recording_url    │                      │
└─────────────────────┘           ┌──────────┴──────────┐
                                  │ ParticipantProfile  │
                                  │  + platform_        │
                                  │    identities (JSON)│
                                  │  + total_interviews │
                                  └─────────────────────┘
```

---

## Entities

### Study (Existing - Modified)

**Purpose**: Represents a research study with interview guide

**New Fields**:
- `slug: str` - Unique URL-friendly identifier for reusable links (e.g., "mobile-banking-study")
- `participant_identity_flow: str` - Controls identity tracking behavior

**participant_identity_flow Values**:
- `"anonymous"`: No identity tracking, no claim option shown
- `"claim_after"`: Post-interview claim available (show button on thank-you page)
- `"allow_pre_signin"`: Show interstitial page with "Continue as Guest" vs "Sign In" options

**Validation Rules**:
- slug must be unique within organization
- slug must match pattern: `^[a-z0-9-]+$` (lowercase alphanumeric + hyphens)
- slug length: 3-63 characters
- participant_identity_flow must be one of three enum values

**State Transitions**: None (study configuration only)

**Example**:
```python
Study(
    id=1,
    organization_id=5,
    title="Mobile Banking App Usability Study",
    slug="mobile-banking-study",
    participant_identity_flow="claim_after",
    interview_guide_content="# Interview Guide\n\n## Learning Goals..."
)
```

**Database Migration Required**:
```sql
ALTER TABLE studies ADD COLUMN slug VARCHAR(63) UNIQUE NOT NULL;
ALTER TABLE studies ADD COLUMN participant_identity_flow VARCHAR(20) NOT NULL DEFAULT 'anonymous';
CREATE INDEX idx_studies_slug ON studies(slug);
```

---

### Interview (New)

**Purpose**: Represents a single participant's response session for a study

**Fields**:
- `id: int` - Primary key
- `study_id: int` - Foreign key to Study (required)
- `access_token: str` - UUID v4 for public access (unique, required)
- `status: str` - Enum: `pending`, `completed`
- `created_at: datetime` - Timestamp when interview was created
- `completed_at: datetime | None` - Timestamp when interview was completed (nullable)
- `expires_at: datetime | None` - Token expiration time (7 days from creation, for abandoned sessions only, nullable)
- `external_participant_id: str | None` - From recruitment platform (e.g., Prolific ID, nullable)
- `platform_source: str | None` - Platform identifier (e.g., "prolific", "respondent", "direct", nullable)
- `verity_user_id: int | None` - Foreign key to VerityUser (nullable, set on claim)
- `claimed_at: datetime | None` - Timestamp when interview was claimed (nullable)
- `transcript_url: str | None` - GCS URL to transcript file (nullable, set by pipecat callback)
- `recording_url: str | None` - GCS URL to audio file (nullable, set by pipecat callback)
- `pipecat_session_id: str | None` - Pipecat internal session ID (nullable)
- `notes: str | None` - Optional notes from pipecat (nullable)

**Validation Rules**:
- access_token must be UUID v4 format
- status must be one of: `pending`, `completed`
- completed_at must be after created_at
- expires_at must be after created_at
- platform_source must match pattern: `^[a-z0-9_-]+$` if provided
- external_participant_id max length: 255 characters
- Only completed interviews can be claimed (status = "completed")

**State Transitions**:
```
pending → completed (via POST /interview/{access_token}/complete)
```

**Note**: Simplified state machine for MVP. If callback fails, interview stays pending. No intermediate state for upload-in-progress (Constitution X: MVP-First).

**Relationships**:
- Belongs to one Study
- Optionally belongs to one VerityUser (when claimed)

**Indexes**:
- `access_token` (unique index for public access lookups)
- `study_id` (foreign key index for org-level queries)
- `verity_user_id` (foreign key index for participant dashboard)
- `external_participant_id` (index for deduplication checks)

**Example**:
```python
Interview(
    id=42,
    study_id=1,
    access_token="123e4567-e89b-12d3-a456-426614174000",
    status="completed",
    created_at=datetime(2025, 10, 10, 20, 14, 18, tzinfo=timezone.utc),
    completed_at=datetime(2025, 10, 10, 20, 32, 45, tzinfo=timezone.utc),
    expires_at=datetime(2025, 10, 17, 20, 14, 18, tzinfo=timezone.utc),  # 7 days for abandoned sessions
    external_participant_id="prolific_abc123",
    platform_source="prolific",
    verity_user_id=5,
    claimed_at=datetime(2025, 10, 10, 20, 35, 12, tzinfo=timezone.utc),
    transcript_url="https://storage.googleapis.com/verity-artifacts-prod/iv_042/transcript.txt",
    recording_url="https://storage.googleapis.com/verity-artifacts-prod/iv_042/recording.wav",
    pipecat_session_id="sess_xyz789",
    notes="Interview completed successfully. Duration: 18 minutes."
)
```

**Database Schema**:
```sql
CREATE TABLE interviews (
    id SERIAL PRIMARY KEY,
    study_id INTEGER NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
    access_token VARCHAR(36) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    external_participant_id VARCHAR(255),
    platform_source VARCHAR(50),
    verity_user_id INTEGER REFERENCES verity_users(id) ON DELETE SET NULL,
    claimed_at TIMESTAMP WITH TIME ZONE,
    transcript_url TEXT,
    recording_url TEXT,
    pipecat_session_id VARCHAR(255),
    notes TEXT
);

CREATE INDEX idx_interviews_access_token ON interviews(access_token);
CREATE INDEX idx_interviews_study_id ON interviews(study_id);
CREATE INDEX idx_interviews_verity_user_id ON interviews(verity_user_id);
CREATE INDEX idx_interviews_external_participant_id ON interviews(external_participant_id);
CREATE INDEX idx_interviews_status ON interviews(status);
```

---

### VerityUser (New)

**Purpose**: Participant identity for cross-platform tracking (separate from Organization users)

**Fields**:
- `id: int` - Primary key
- `firebase_uid: str` - Firebase Auth UID (unique, required)
- `email: str` - Email address from Firebase (unique, required)
- `display_name: str | None` - Optional display name (nullable)
- `created_at: datetime` - Timestamp when VerityUser was created
- `last_sign_in: datetime | None` - Last authentication timestamp (nullable)

**Validation Rules**:
- firebase_uid must be unique across all VerityUsers
- email must be unique across all VerityUsers
- email must be valid email format (validated by Firebase)
- display_name max length: 255 characters

**State Transitions**: None (identity record only)

**Relationships**:
- Has many Interviews (claimed interviews)
- Has one ParticipantProfile

**Indexes**:
- `firebase_uid` (unique index for Firebase Auth lookups)
- `email` (unique index for email-based queries)

**Example**:
```python
VerityUser(
    id=5,
    firebase_uid="oRzxDjSk3NabC2EfGhIjKlMnOpQr",
    email="participant@example.com",
    display_name="Jane Doe",
    created_at=datetime(2025, 10, 10, 20, 35, 0, tzinfo=timezone.utc),
    last_sign_in=datetime(2025, 10, 10, 20, 35, 12, tzinfo=timezone.utc)
)
```

**Database Schema**:
```sql
CREATE TABLE verity_users (
    id SERIAL PRIMARY KEY,
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_sign_in TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_verity_users_firebase_uid ON verity_users(firebase_uid);
CREATE INDEX idx_verity_users_email ON verity_users(email);
```

---

### ParticipantProfile (New)

**Purpose**: Extended participant profile for cross-platform reconciliation

**Fields**:
- `id: int` - Primary key
- `verity_user_id: int` - Foreign key to VerityUser (unique, required)
- `platform_identities: dict` - JSON mapping of platform → external ID (e.g., `{"prolific": "abc123", "respondent": "xyz789"}`)

**Note**: Stats (total interviews, participation time) computed via COUNT/SUM queries on demand. No caching for MVP scale. Add denormalized stats later if queries become slow (Constitution X: MVP-First).

**Validation Rules**:
- verity_user_id must be unique (1-to-1 relationship)
- platform_identities must be valid JSON object
- platform_identities keys must match pattern: `^[a-z0-9_-]+$`

**State Transitions**: None (profile record only)

**Relationships**:
- Belongs to one VerityUser

**Indexes**:
- `verity_user_id` (unique foreign key index)

**Example**:
```python
ParticipantProfile(
    id=3,
    verity_user_id=5,
    platform_identities={
        "prolific": "prolific_abc123",
        "respondent": "respondent_xyz789"
    }
)
```

**Database Schema**:
```sql
CREATE TABLE participant_profiles (
    id SERIAL PRIMARY KEY,
    verity_user_id INTEGER UNIQUE NOT NULL REFERENCES verity_users(id) ON DELETE CASCADE,
    platform_identities JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_participant_profiles_verity_user_id ON participant_profiles(verity_user_id);
CREATE INDEX idx_participant_profiles_platform_identities ON participant_profiles USING GIN (platform_identities);
```

---

## Data Flows

### Flow 1: Reusable Link Access (On-the-Fly Interview Creation)

```
1. Participant accesses: https://verity.com/study/{slug}/start?pid=prolific_abc123

2. Verity backend:
   - Looks up Study by slug
   - Checks if Interview already exists for (study_id, external_participant_id)
   - If not exists, creates new Interview:
     * access_token = UUID v4
     * status = "pending"
     * external_participant_id = "prolific_abc123"
     * platform_source = "prolific" (inferred from pid prefix)
     * expires_at = now() + 7 days
   - Redirects to pipecat URL with access_token

3. Pipecat receives access_token, fetches Interview data from Verity
```

**SQL Queries**:
```sql
-- Lookup study by slug
SELECT * FROM studies WHERE slug = 'mobile-banking-study' AND organization_id = 5;

-- Check for existing interview (deduplication)
SELECT * FROM interviews
WHERE study_id = 1 AND external_participant_id = 'prolific_abc123';

-- Create new interview (if not exists)
INSERT INTO interviews (study_id, access_token, status, external_participant_id, platform_source, expires_at)
VALUES (1, '123e4567-e89b-12d3-a456-426614174000', 'pending', 'prolific_abc123', 'prolific', NOW() + INTERVAL '7 days')
RETURNING *;
```

---

### Flow 2: Interview Completion Callback

```
1. Pipecat uploads artifacts to GCS:
   - gs://verity-artifacts-prod/iv_042/recording.wav
   - gs://verity-artifacts-prod/iv_042/transcript.txt

2. Pipecat POSTs to: /api/interview/{access_token}/complete
   - Body: { transcript_url, recording_url, notes }

3. Verity backend:
   - Validates access_token (Interview exists and status = "pending")
   - Updates Interview:
     * status = "completed"
     * completed_at = now()
     * transcript_url = <from callback>
     * recording_url = <from callback>
     * notes = <from callback>
   - Returns 200 OK
```

**SQL Queries**:
```sql
-- Find interview by access_token
SELECT * FROM interviews WHERE access_token = '123e4567-e89b-12d3-a456-426614174000';

-- Update interview on completion
UPDATE interviews
SET status = 'completed',
    completed_at = NOW(),
    transcript_url = 'https://storage.googleapis.com/.../transcript.txt',
    recording_url = 'https://storage.googleapis.com/.../recording.wav',
    notes = 'Interview completed successfully'
WHERE access_token = '123e4567-e89b-12d3-a456-426614174000'
RETURNING *;
```

---

### Flow 3: Post-Interview Claim

```
1. Participant clicks "Sign In to Track My Interviews" on thank-you page

2. Frontend:
   - User signs in with Firebase Auth (or creates account)
   - Gets Firebase ID token

3. Frontend POSTs to: /api/interview/{access_token}/claim
   - Headers: Authorization: Bearer <firebase-id-token>

4. Verity backend:
   - Validates Firebase token → extracts firebase_uid + email
   - Finds Interview by access_token (must be status="completed")
   - Gets or creates VerityUser by firebase_uid
   - If new VerityUser, creates ParticipantProfile
   - Links Interview to VerityUser:
     * verity_user_id = <user_id>
     * claimed_at = now()
   - Updates ParticipantProfile.platform_identities if external_participant_id exists
   - Returns 200 OK with user stats
```

**SQL Queries**:
```sql
-- Find or create VerityUser
SELECT * FROM verity_users WHERE firebase_uid = 'oRzxDjSk3NabC2EfGhIjKlMnOpQr';

-- If not found, insert
INSERT INTO verity_users (firebase_uid, email, last_sign_in)
VALUES ('oRzxDjSk3NabC2EfGhIjKlMnOpQr', 'participant@example.com', NOW())
RETURNING *;

-- Create profile
INSERT INTO participant_profiles (verity_user_id, platform_identities)
VALUES (5, '{}')
RETURNING *;

-- Link interview to user
UPDATE interviews
SET verity_user_id = 5, claimed_at = NOW()
WHERE access_token = '123e4567-e89b-12d3-a456-426614174000'
RETURNING *;

-- Update platform identities (if external_participant_id exists)
UPDATE participant_profiles
SET platform_identities = jsonb_set(platform_identities, '{prolific}', '"prolific_abc123"')
WHERE verity_user_id = 5;
```

---

### Flow 4: Researcher Views Interview Artifacts

```
1. Researcher navigates to study details page in Verity frontend

2. Frontend GETs: /api/orgs/{org_id}/studies/{study_id}/interviews
   - Headers: Authorization: Bearer <firebase-id-token>

3. Verity backend:
   - Validates Firebase token → extracts user identity
   - Verifies user belongs to organization (server-side check)
   - Queries Interviews for study:
     * WHERE study_id = <study_id>
     * JOIN Study to verify study.organization_id = <org_id>
     * Only return completed interviews
   - Returns list of interviews with metadata (no artifact URLs yet)

4. Researcher clicks "View Transcript" or "Download Audio"

5. Frontend GETs: /api/orgs/{org_id}/interviews/{interview_id}/artifacts/{filename}
   - Headers: Authorization: Bearer <firebase-id-token>

6. Verity backend:
   - Validates Firebase token
   - Verifies user belongs to organization
   - Verifies interview belongs to study in organization
   - Generates signed URL for GCS artifact (1 hour expiration)
   - Streams artifact from GCS through backend (API proxy pattern)
   - Returns artifact bytes with appropriate Content-Type header
```

**SQL Queries**:
```sql
-- List interviews for study (with org-level access control)
SELECT i.*
FROM interviews i
JOIN studies s ON i.study_id = s.id
WHERE s.id = 1
  AND s.organization_id = 5
  AND i.status = 'completed'
ORDER BY i.completed_at DESC;

-- Verify interview belongs to organization (before artifact access)
SELECT i.*, s.organization_id
FROM interviews i
JOIN studies s ON i.study_id = s.id
WHERE i.id = 42 AND s.organization_id = 5;
```

---

### Flow 5: Participant Dashboard

```
1. Participant signs in to Verity (Firebase Auth)

2. Frontend GETs: /api/participant/dashboard
   - Headers: Authorization: Bearer <firebase-id-token>

3. Verity backend:
   - Validates Firebase token → extracts firebase_uid
   - Finds VerityUser by firebase_uid
   - Queries all claimed Interviews for user:
     * WHERE verity_user_id = <user_id>
     * WHERE status = "completed"
     * JOIN Study to get study titles
   - Calculates stats (or uses cached values from ParticipantProfile)
   - Returns dashboard data (metadata only, no artifacts)
```

**SQL Queries**:
```sql
-- Find VerityUser by Firebase UID
SELECT * FROM verity_users WHERE firebase_uid = 'oRzxDjSk3NabC2EfGhIjKlMnOpQr';

-- Get claimed interviews
SELECT i.*, s.title AS study_title
FROM interviews i
JOIN studies s ON i.study_id = s.id
WHERE i.verity_user_id = 5
  AND i.status = 'completed'
ORDER BY i.completed_at DESC;

-- Get profile with stats
SELECT * FROM participant_profiles WHERE verity_user_id = 5;
```

---

## Security Considerations

### Multi-Tenancy Isolation

**Critical Rule**: VerityUsers are SEPARATE from Organization users

```
Organization Users (Researchers):
- Multi-tenant (organization_id scoped)
- Server-side authorization checks required
- Access study/interview data within their organization

VerityUsers (Participants):
- Global (no organization_id)
- Can participate in studies from multiple organizations
- Only access their own claimed interviews
```

**Authorization Checks**:

```python
# Researcher accessing interview data
def verify_org_access(user: User, interview_id: int, db: Session) -> Interview:
    """Verify researcher belongs to organization that owns interview"""
    interview = db.query(Interview).join(Study).filter(
        Interview.id == interview_id,
        Study.organization_id == user.organization_id  # Server-side check
    ).first()

    if not interview:
        raise HTTPException(status_code=404)

    return interview


# Participant accessing their own data
def verify_participant_access(verity_user: VerityUser, interview_id: int, db: Session) -> Interview:
    """Verify participant claimed this interview"""
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.verity_user_id == verity_user.id  # Only their interviews
    ).first()

    if not interview:
        raise HTTPException(status_code=404)

    return interview
```

### Data Privacy

**Participant Privacy**:
- Participants CANNOT view transcripts or audio (researcher's data)
- Participant dashboard shows only metadata (study title, date, duration)
- External IDs are stored but not validated (trusted platform assumption)

**Researcher Privacy**:
- Participants do not see organization names or researcher identities
- Study titles are visible to participants (necessary for tracking)

**PII Handling**:
- Anonymous interviews: No PII collected
- Claimed interviews: Email + optional display_name (from Firebase Auth)
- External IDs: Platform-specific identifiers (not validated by Verity)

### Access Control Summary

| Endpoint | Auth Required | Scope | Authorization Check |
|----------|---------------|-------|---------------------|
| `GET /study/{slug}/start` | No | Public | None (creates interview on-the-fly) |
| `GET /interview/{access_token}` | No | Public | Valid access_token, not expired |
| `POST /interview/{access_token}/complete` | No | Public | Valid access_token, status=pending |
| `POST /interview/{access_token}/claim` | Yes (Firebase) | Participant | Interview must be completed, not already claimed |
| `GET /api/orgs/{org_id}/studies/{study_id}/interviews` | Yes (Firebase) | Researcher | User belongs to organization |
| `GET /api/orgs/{org_id}/interviews/{interview_id}/artifacts/{filename}` | Yes (Firebase) | Researcher | User belongs to organization, interview belongs to organization |
| `GET /api/participant/dashboard` | Yes (Firebase) | Participant | User is VerityUser |

---

## Indexes Summary

**Performance Considerations**:

1. **Interview.access_token (UNIQUE)**: Critical for public endpoint lookups (`GET /interview/{access_token}`)
2. **Interview.study_id**: Critical for org-level interview list queries
3. **Interview.verity_user_id**: Critical for participant dashboard queries
4. **Interview.external_participant_id**: Critical for deduplication checks on link access
5. **Study.slug (UNIQUE)**: Critical for reusable link resolution
6. **VerityUser.firebase_uid (UNIQUE)**: Critical for Firebase Auth lookups
7. **ParticipantProfile.verity_user_id (UNIQUE)**: 1-to-1 relationship enforcement

**Composite Indexes (Future Optimization)**:
- `(study_id, external_participant_id)` for faster deduplication checks
- `(verity_user_id, status)` for faster participant dashboard queries
- `(study_id, status, completed_at)` for faster org-level interview list queries with sorting
