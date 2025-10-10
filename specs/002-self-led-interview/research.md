# Research: Self-Led Interview Execution

**Date**: 2025-10-10
**Feature**: [spec.md](./spec.md)

This document contains technical research findings that resolve all "NEEDS CLARIFICATION" items from the Technical Context section of [plan.md](./plan.md).

---

## 1. Pipecat Integration

### 1.1 Callback URL Format

**Decision**: Pipecat should POST to the full Verity backend URL: `https://verity-backend.com/api/interview/{access_token}/complete`

**Rationale**:
- Current pipecat-momtest implementation doesn't have any callback mechanism - it saves files locally/to GCS when the WebSocket disconnects
- Verity's OpenAPI spec defines `/interview/{access_token}/complete` as the completion endpoint
- Request body must include:
  - `transcript_url` (required): URL where Verity can download the transcript
  - `recording_url` (optional): URL where Verity can download the audio recording
  - `notes` (optional): Additional notes about the interview
- The endpoint is public (`security: []`) and requires no authentication - only the access_token path parameter
- Verity expects URLs, not file data - pipecat needs to upload files to accessible storage first, then send URLs

**Required Changes to Pipecat**:
1. Add VERITY_CALLBACK_URL environment variable (e.g., `https://verity.com/api`)
2. Add `POST /session/start` endpoint to initialize from Verity access_token
3. Modify WebSocket to use session-based flow instead of local momtest files
4. Add HTTP callback to Verity's `/interview/{access_token}/complete` endpoint after file upload
5. Update file storage paths to use interview_id (not session_id)
6. Update frontend to handle `access_token` query parameter

### 1.2 CORS Requirements

**Required Origins**:
- Pipecat-momtest will be hosted on a different domain from Verity backend
- Need to add pipecat's production domain to CORS allowed origins in Verity backend

**Required Changes to Verity**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Potential prod
        "https://pipecat.verity.com",  # Add pipecat domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Methods/Headers**: Already covered by `["*"]` wildcard in current configuration

### 1.3 Session Token Lifetime

**Decision**: **7 days (604800 seconds)**

**Rationale**:
1. **Interview Duration**: Mom Test interviews are conversational and thorough (15-30 minutes typical, plus setup time)
2. **No timeout in pipecat**: WebSocket stays open until client disconnects, no automatic disconnection after inactivity
3. **Verity's Interview model**: `access_token` is UUID format (not time-limited JWT), single-use (once status is "completed", GET /interview/{access_token} returns 404)
4. **Security considerations**: Tokens are one-time use (invalidated on completion), 7 days allows flexibility for scheduling without excessive exposure
5. **Abandoned session cleanup**: Expiration is only enforced for abandoned sessions (pending interviews that never complete), not for active interviews

**Implementation Approach**:
- Add optional `expires_at` timestamp to Interview model
- Check expiration in `GET /interview/{access_token}` endpoint only if status is still "pending"
- Return 404 if current_time > expires_at AND status is "pending"
- Set expires_at = created_at + 7 days when generating interview link

### 1.4 Integration Flow

**Step-by-step flow with concrete examples**:

#### Step 1: Verity creates interview with access token
```http
POST https://verity.com/api/studies/{study_id}/interviews
Authorization: Bearer <firebase-jwt>

Response 201:
{
  "interview": {
    "interview_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "study_id": "550e8400-e29b-41d4-a716-446655440000",
    "access_token": "123e4567-e89b-12d3-a456-426614174000",
    "status": "pending",
    "created_at": "2025-10-10T20:14:18Z"
  },
  "interview_url": "https://app.verity.com/interview/123e4567-e89b-12d3-a456-426614174000"
}
```

#### Step 2: Verity redirects participant to pipecat URL with token
```
https://pipecat.verity.com/?access_token=123e4567-e89b-12d3-a456-426614174000&verity_api=https://verity.com/api
```

#### Step 3: Pipecat fetches interview data from Verity
```http
GET https://verity.com/api/interview/123e4567-e89b-12d3-a456-426614174000

Response 200:
{
  "interview": {
    "interview_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "study_id": "550e8400-e29b-41d4-a716-446655440000",
    "access_token": "123e4567-e89b-12d3-a456-426614174000",
    "status": "pending",
    "created_at": "2025-10-10T20:14:18Z"
  },
  "study": {
    "title": "Mobile Banking App Usability Study",
    "interview_guide": {
      "content_md": "# Interview Guide\n\n## Learning Goals\n1. ...",
      "updated_at": "2025-10-10T19:00:00Z"
    }
  }
}
```

#### Step 4: Pipecat conducts interview
- Pipecat frontend establishes WebSocket
- User talks with AI interviewer (using interview_guide.content_md as context)
- Pipecat records audio and transcript in real-time
- WebSocket stays open until user disconnects or completes interview

#### Step 5: Interview completes
- WebSocket disconnects
- Pipecat uploads audio to GCS bucket: `gs://verity-interviews/{interview_id}/recording.wav`
- Pipecat uploads transcript to GCS: `gs://verity-interviews/{interview_id}/transcript.txt`

#### Step 6: Pipecat posts results back to Verity
```http
POST https://verity.com/api/interview/123e4567-e89b-12d3-a456-426614174000/complete
Content-Type: application/json

{
  "transcript_url": "https://storage.googleapis.com/verity-interviews/{interview_id}/transcript.txt",
  "recording_url": "https://storage.googleapis.com/verity-interviews/{interview_id}/recording.wav",
  "notes": "Interview completed successfully. Duration: 18 minutes."
}

Response 200:
{
  "message": "Interview completed successfully"
}
```

#### Step 7: Verity marks interview as completed
- Updates interview status to "completed"
- Sets completed_at timestamp
- Stores transcript_url and recording_url
- Future GET requests to /interview/{access_token} return 404

---

## 2. Participant Identity Flows

### 2.1 Firebase Auth Patterns

**Decision**: Progressive authentication with anonymous-first entry, optional account linking, and cross-platform identity reconciliation

**Three-Tier Identity System**:

#### Tier 1: Anonymous Authentication (Default Entry Point)
```javascript
getAuth().signInAnonymously()
  .then((userCredential) => {
    // Creates random UID on Firebase server
    // UID persists across sessions on same device
    // No PII required at this stage
  });
```

**Benefits**: Zero-friction onboarding, unique user identifier without registration

#### Tier 2: Account Linking (Post-Interview Claim)
```javascript
linkWithCredential(auth.currentUser, credential)
  .then((usercred) => {
    // Original anonymous UID preserved
    // All interview data remains accessible
    // User now authenticated with email/provider
  });
```

**Critical Design Point**: Original Firebase UID persists after linking (no data migration needed)

#### Tier 3: Pre-Authenticated Access
```javascript
if (auth.currentUser && !auth.currentUser.isAnonymous) {
  // Auto-link interview to existing VerityUser
  // Skip interstitial (friction reduction)
}
```

**Implementation Pattern**:
```
Participant Accesses Reusable Link
│
├─ Has pid parameter? ──YES──> Skip sign-in (friction reduction)
│
└─ NO ──> Check study.participant_identity_flow
          │
          ├─ "anonymous" ──> signInAnonymously()
          ├─ "claim_after" ──> signInAnonymously() + show claim button on thank-you page
          └─ "allow_pre_signin" ──> Show interstitial: "Continue as Guest" vs "Sign In"
```

### 2.2 VerityUser Model Design

**Proposed Schema**:

```python
class VerityUser(Base):
    """Participant identity for cross-platform tracking"""
    __tablename__ = "verity_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    firebase_uid: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_sign_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    interviews: Mapped[list["Interview"]] = relationship("Interview", back_populates="verity_user")
    profile: Mapped["ParticipantProfile | None"] = relationship(
        "ParticipantProfile", back_populates="user", uselist=False
    )


class ParticipantProfile(Base):
    """Extended participant profile for cross-platform reconciliation"""
    __tablename__ = "participant_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    verity_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("verity_users.id"), nullable=False, unique=True
    )

    # Platform affiliations (JSON mapping)
    # Example: {"prolific": "abc123", "respondent": "xyz789"}
    platform_identities: Mapped[dict] = mapped_column(JSON, default=dict)

    # Participation stats
    total_interviews: Mapped[int] = mapped_column(Integer, default=0)
    total_minutes_participated: Mapped[int] = mapped_column(Integer, default=0)

    # Relationship
    user: Mapped["VerityUser"] = relationship("VerityUser", back_populates="profile")


class Interview(Base):
    # ... existing fields ...

    # External identity (from recruitment platform)
    external_participant_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    platform_source: Mapped[str | None] = mapped_column(String, nullable=True)  # "prolific", "respondent", "direct"

    # Verity identity (from sign-in/claim)
    verity_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("verity_users.id"), nullable=True, index=True
    )

    # Claimed timestamp
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    verity_user: Mapped["VerityUser | None"] = relationship("VerityUser", back_populates="interviews")
```

**Key Design Decisions**:
1. **Separate VerityUser from Organization Users**: Participants and researchers are distinct user types
2. **Both External + Verity IDs**: Interview can have `external_participant_id` (Prolific) AND `verity_user_id` (claimed account)
3. **Platform Identities JSON**: Flexible storage for multiple platform IDs per user
4. **Nullable Foreign Keys**: Supports anonymous interviews (no verity_user_id initially)
5. **Claimed Timestamp**: Track when interview was claimed (audit trail)

### 2.3 Claim Flow Implementation

**Client-Side (Frontend)**:
```javascript
// Thank-you page shows "Sign In to Track My Interviews" button

// Option A: Email/Password Registration
createUserWithEmailAndPassword(auth, email, password)
  .then((userCredential) => {
    return claimInterview(userCredential.user.uid, accessToken);
  });

// Option B: User already has account → Sign in first
signInWithEmailAndPassword(auth, email, password)
  .then((userCredential) => {
    return claimInterview(userCredential.user.uid, accessToken);
  });

// Call backend claim endpoint
async function claimInterview(firebaseUid, accessToken) {
  const idToken = await auth.currentUser.getIdToken();

  return fetch(`/api/interview/${accessToken}/claim`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${idToken}`,
      'Content-Type': 'application/json'
    }
  });
}
```

**Backend (Verity API)**:
```python
@router.post("/interview/{access_token}/claim")
async def claim_interview(
    access_token: str,
    current_user: Annotated[AuthUser, Depends(get_current_user)],  # Firebase JWT
    db: Annotated[Session, Depends(get_db)],
):
    """Link completed anonymous interview to authenticated VerityUser"""

    # 1. Find interview by access token
    interview = db.query(Interview).filter(
        Interview.access_token == access_token
    ).first()

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # 2. Verify interview is completed
    if interview.status != "completed":
        raise HTTPException(status_code=400, detail="Interview not completed yet")

    # 3. Check if already claimed (idempotent)
    if interview.verity_user_id is not None:
        existing_user = db.query(VerityUser).filter(
            VerityUser.id == interview.verity_user_id
        ).first()
        if existing_user and existing_user.firebase_uid == current_user.firebase_uid:
            return {"status": "already_claimed"}
        else:
            raise HTTPException(status_code=400, detail="Interview already claimed by another user")

    # 4. Get or create VerityUser from Firebase UID
    verity_user = db.query(VerityUser).filter(
        VerityUser.firebase_uid == current_user.firebase_uid
    ).first()

    if not verity_user:
        # First time signing in - create VerityUser
        verity_user = VerityUser(
            firebase_uid=current_user.firebase_uid,
            email=current_user.email,
            last_sign_in=datetime.now(timezone.utc)
        )
        db.add(verity_user)
        db.flush()

        # Create profile
        profile = ParticipantProfile(verity_user_id=verity_user.id)
        db.add(profile)

    # 5. Link interview to VerityUser
    interview.verity_user_id = verity_user.id
    interview.claimed_at = datetime.now(timezone.utc)

    # 6. Update platform identities if external_participant_id exists
    if interview.external_participant_id and interview.platform_source:
        profile = verity_user.profile
        if profile.platform_identities is None:
            profile.platform_identities = {}

        profile.platform_identities[interview.platform_source] = interview.external_participant_id

    db.commit()

    return {
        "status": "claimed",
        "verity_user_id": verity_user.id,
        "total_interviews": len(verity_user.interviews)
    }
```

**Error Handling Cases**:
1. **Interview not found**: 404 (invalid access_token)
2. **Interview not completed**: 400 (can only claim completed interviews)
3. **Already claimed by same user**: 200 idempotent response
4. **Already claimed by different user**: 400 error (security check)
5. **Firebase auth failure**: 401 (invalid JWT token)

### 2.4 Participant Dashboard Design

**UI/UX Recommendations**:

```
┌─────────────────────────────────────────────────────────────┐
│ My Participation                                            │
├─────────────────────────────────────────────────────────────┤
│ Total Interviews: 7                                         │
│ Total Time Contributed: 42 minutes                          │
│                                                             │
│ Platform Connections:                                       │
│   🟢 Prolific (abc123)                                      │
│   🟢 Respondent (xyz789)                                    │
│   🟢 Direct Links                                           │
├─────────────────────────────────────────────────────────────┤
│ Interview History                                           │
│                                                             │
│ [Study Title, Platform, Date, Duration cards...]            │
└─────────────────────────────────────────────────────────────┘
```

**API Endpoint**:
```python
@router.get("/api/participant/dashboard")
async def get_participant_dashboard(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get participant's complete participation history"""

    verity_user = db.query(VerityUser).filter(
        VerityUser.firebase_uid == current_user.firebase_uid
    ).first()

    if not verity_user:
        raise HTTPException(status_code=404, detail="Participant profile not found")

    interviews = db.query(Interview).filter(
        Interview.verity_user_id == verity_user.id,
        Interview.status == "completed"
    ).order_by(Interview.completed_at.desc()).all()

    return {
        "stats": {
            "total_interviews": len(interviews),
            "platforms_connected": list(verity_user.profile.platform_identities.keys())
        },
        "interviews": [
            {
                "study_title": interview.study.title,
                "platform_source": interview.platform_source or "direct",
                "completed_at": interview.completed_at,
                "duration_minutes": int((interview.completed_at - interview.created_at).total_seconds() / 60)
            }
            for interview in interviews
        ]
    }
```

**Privacy Considerations**:
1. **No Transcript Access**: Participants cannot view their interview transcripts (researcher's data)
2. **Metadata Only**: Show study title, platform, date, duration (no content)
3. **Masked External IDs**: Display last 4 chars only
4. **No Researcher Info**: Don't expose organization names or researcher identities
5. **Opt-Out Capability**: Participants can delete their VerityUser account

### 2.5 Security Considerations

**Cross-Organization Isolation**:
- VerityUser accounts are SEPARATE from Organization users
- Participants are global across all studies (can participate in studies from multiple organizations)
- Server-side authorization checks required for researcher endpoints

**PII Handling**:
- Anonymous interviews: No PII collected (only anonymous Firebase UID)
- Claimed interviews: Email + optional display name (from Firebase Auth)
- External IDs: Stored but not validated (trusted platform assumption)

**Firebase JWT Validation**:
```python
def verify_participant_token(token: str) -> VerityUser:
    """Verify Firebase JWT for participant endpoints"""
    decoded = verify_firebase_token(token)

    # Ensure tenant type is "interviewee" (not "organization")
    if decoded.get("tenant") != "interviewee":
        raise HTTPException(status_code=403, detail="Invalid tenant type")

    return VerityUser(firebase_uid=decoded["uid"], email=decoded.get("email"))
```

---

## 3. Shared GCS Bucket IAM

### 3.1 Pulumi Configuration

**Bucket Creation with Security Best Practices**:

```python
import pulumi
import pulumi_gcp as gcp

# Create GCS bucket for interview artifacts
artifacts_bucket = gcp.storage.Bucket(
    "interview-artifacts",
    name=f"verity-artifacts-{stack}",  # Globally unique name
    location="US",  # Multi-region for high availability
    storage_class="STANDARD",  # Standard for frequently accessed data

    # Security: Uniform bucket-level access (IAM-only, no ACLs)
    uniform_bucket_level_access=gcp.storage.BucketUniformBucketLevelAccessArgs(
        enabled=True,
    ),

    # Security: Prevent accidental public exposure
    public_access_prevention="enforced",

    # Lifecycle: TBD based on usage patterns (defer until storage costs material)
    # Versioning: Not needed for MVP (artifacts are write-once, rely on GCS default durability)
)

# Grant Verity backend read/write access
verity_bucket_iam = gcp.storage.BucketIAMBinding(
    "verity-artifacts-access",
    bucket=artifacts_bucket.name,
    role="roles/storage.objectAdmin",  # Full object CRUD + metadata
    members=[backend_sa.email.apply(lambda email: f"serviceAccount:{email}")],
)

# Grant pipecat service account write-only access
pipecat_bucket_iam = gcp.storage.BucketIAMBinding(
    "pipecat-artifacts-upload",
    bucket=artifacts_bucket.name,
    role="roles/storage.objectCreator",  # Create objects only, no read/delete
    members=[f"serviceAccount:pipecat-momtest@{project}.iam.gserviceaccount.com"],
)

# Export bucket name for application configuration
pulumi.export("artifacts_bucket_name", artifacts_bucket.name)
pulumi.export("artifacts_bucket_url", artifacts_bucket.url)
```

**Bucket Naming Conventions**:
- Must be globally unique across all GCP projects
- Use format: `{project}-{purpose}-{environment}` (e.g., `verity-artifacts-dev`)
- 3-63 characters, lowercase letters, numbers, dashes, underscores

**Storage Class & Location**:
- **STANDARD in Multi-Region (US/EU)**: Best for MVP scale with frequent access
  - Guarantees 2 geo-diverse replicas (100+ miles apart)
  - Optimized for low latency worldwide
  - Higher availability (99.95% SLA)
  - Cost: ~$0.026/GB/month
- **Alternative**: STANDARD in Single Region (e.g., us-central1) if compute is colocated
  - Lower cost: ~$0.020/GB/month

**Lifecycle Policies**:
- Automatic deletion after retention period (e.g., 90 days for interviews)
- Can filter by prefix: `{interview_id}/`
- Consider transitioning to NEARLINE/COLDLINE for archival (>30 days)

### 3.2 IAM Roles

**Recommended Roles for Least Privilege**:

| Role | Permissions | Use Case |
|------|-------------|----------|
| `roles/storage.objectViewer` | Read objects + metadata | Read-only access |
| `roles/storage.objectCreator` | Create objects only | **Pipecat**: Upload artifacts, cannot read/delete |
| `roles/storage.objectAdmin` | Full object CRUD + metadata | **Verity**: Read/write/delete artifacts, proxy to researchers |

**Security Principle**:
- Grant bucket-level IAM roles (not project-level) to limit blast radius
- Pipecat gets **Object Creator** (can only upload, not read other interviews)
- Verity gets **Object Admin** (full CRUD for researcher access)

### 3.3 Service Account Authentication

**Verity Backend (Cloud Run)**:
- **Automatic**: Cloud Run's attached service account uses Application Default Credentials (ADC)
- No keys required - credentials auto-detected via metadata server
- Example Python code:
```python
from google.cloud import storage

# No credentials needed - ADC handles authentication
client = storage.Client()
bucket = client.bucket("verity-artifacts-dev")
blob = bucket.blob(f"{interview_id}/recording.wav")
data = blob.download_as_bytes()
```

**Pipecat-momtest Service Account**:
- **Recommended**: Workload Identity Federation (keyless authentication)
  - If pipecat runs on GKE/Cloud Run: Use attached service account (same as Verity)
  - If external (AWS/Azure/on-prem): Configure Workload Identity Federation
  - Avoids JSON key management (rotation, leakage risks)
- **Alternative**: Service Account JSON key (legacy, not recommended)
  - Only if Workload Identity is not feasible
  - Requires manual rotation and secure storage

### 3.4 Artifact Organization

**Folder Structure (Flat Namespace with Prefixes)**:
```
verity-artifacts-dev/
├── {interview_id}/
│   ├── recording.wav
│   ├── transcript.txt
│   └── metadata.json
```

**Object Naming Best Practices**:
- Use consistent prefixes: `{interview_id}/` for filtering/lifecycle policies
- Example paths:
  - `iv_abc123/recording.wav`
  - `iv_abc123/transcript.txt`

**Prefix-Based Queries**:
```python
# List all artifacts for interview
blobs = bucket.list_blobs(prefix=f"{interview_id}/")
for blob in blobs:
    print(blob.name)  # iv_abc123/recording.wav, iv_abc123/transcript.txt
```

### 3.5 Local Development

**Recommendation**: Continue using MinIO for basic local testing (simple upload/download)

**Environment Variable Configuration**:
```bash
# Local development (.env)
GCS_BUCKET_NAME=verity-artifacts-local
STORAGE_EMULATOR_HOST=http://localhost:9000  # MinIO

# Production (Cloud Run)
GCS_BUCKET_NAME=verity-artifacts-prod
# STORAGE_EMULATOR_HOST unset - uses real GCS
```

**Alternative**: Add fake-gcs-server if you need to test:
- IAM policy evaluation
- Signed URLs for temporary access
- GCS-specific features (versioning, lifecycle)

### 3.6 Security Considerations

**Public Access Prevention**:
- **CRITICAL**: Set `public_access_prevention="enforced"` to block accidental public exposure
- Prevents setting ACLs that grant `allUsers` or `allAuthenticatedUsers`

**Encryption**:
- **Default**: Google-managed encryption keys (automatic, no configuration)
- **Optional**: Customer-managed encryption keys (CMEK) for compliance

**Audit Logging**:
- **Admin Activity Logs**: Always enabled (bucket creation, IAM changes)
- **Data Access Logs**: Disabled by default, enable for compliance

**Researcher Access Pattern (Verity Proxy)**:
```python
from google.cloud import storage
from datetime import timedelta

def get_artifact_download_url(interview_id: str, filename: str) -> str:
    client = storage.Client()  # Uses backend service account
    bucket = client.bucket("verity-artifacts-prod")
    blob = bucket.blob(f"{interview_id}/{filename}")

    # Generate signed URL valid for 1 hour
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="GET",
    )
    return url
```

**Cross-Org Security (Verity-Specific)**:
- Interview artifacts are scoped to organization
- Backend MUST verify researcher belongs to interview's organization before generating signed URLs
- Never trust client-provided org_id - retrieve from database based on authenticated user

---

## Summary of Key Decisions

### Pipecat Integration
- **Callback URL**: POST to `https://verity.com/api/interview/{access_token}/complete` with artifact URLs
- **CORS**: Add pipecat's production domain to Verity backend allowed origins
- **Session Token Lifetime**: 24 hours (86400 seconds)
- **Integration Flow**: Verity creates interview → redirects to pipecat → pipecat fetches guide → conducts interview → uploads artifacts → calls completion callback

### Participant Identity
- **Auth Pattern**: Progressive authentication (anonymous → optional claim → authenticated)
- **VerityUser Model**: Separate from Organization users, supports multiple platform_identities per user
- **Claim Flow**: Post-interview account creation/sign-in, backend links interview via verity_user_id
- **Participant Dashboard**: Metadata-only view (no transcripts), privacy-respecting design

### Shared GCS Bucket
- **Pulumi Configuration**: Create bucket with uniform bucket-level access + public access prevention
- **IAM Roles**: Verity (Object Admin), Pipecat (Object Creator)
- **Authentication**: ADC for Cloud Run, Workload Identity for pipecat (no JSON keys)
- **Artifact Organization**: `{interview_id}/` prefix pattern for easy filtering
- **Local Development**: Continue using MinIO for basic storage operations
