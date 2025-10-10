# Developer Quickstart: Self-Led Interview Execution

**Date**: 2025-10-10
**Feature**: [spec.md](./spec.md)

**Note**: This is the detailed implementation guide. For the big picture and implementation roadmap, see **[plan.md](./plan.md)**.

This guide provides step-by-step instructions for implementing the self-led interview execution feature following BDD-First Development (Constitution principle I).

---

## Prerequisites

- Read [spec.md](./spec.md), [research.md](./research.md), and [data-model.md](./data-model.md)
- Understand the constitution principles (especially BDD-First, Multi-Tenancy Security, MVP-First)
- Local development environment set up (`make bootstrap` completed)
- Firebase Auth emulator running (`make dev`)

---

## Implementation Phases

### Phase 1: Infrastructure (Pulumi)

**Duration**: ~2 hours
**Files Modified**: `infra/__main__.py`

#### Step 1.1: Create Shared GCS Bucket

```python
# infra/__main__.py

import pulumi
import pulumi_gcp as gcp

# Get stack name
stack = pulumi.get_stack()  # "dev" or "prod"
project = pulumi.Config("gcp").require("project")

# Create GCS bucket for interview artifacts
artifacts_bucket = gcp.storage.Bucket(
    "interview-artifacts",
    name=f"verity-artifacts-{stack}",
    location="US",  # Multi-region
    storage_class="STANDARD",

    # Security: IAM-only access (no ACLs)
    uniform_bucket_level_access=gcp.storage.BucketUniformBucketLevelAccessArgs(
        enabled=True,
    ),

    # Security: Prevent accidental public exposure
    public_access_prevention="enforced",

    # Lifecycle: Delete after 90 days
    lifecycle_rules=[
        gcp.storage.BucketLifecycleRuleArgs(
            action=gcp.storage.BucketLifecycleRuleActionArgs(
                type="Delete",
            ),
            condition=gcp.storage.BucketLifecycleRuleConditionArgs(
                age=90,
            ),
        ),
    ],

    # Versioning for accidental deletion protection
    versioning=gcp.storage.BucketVersioningArgs(
        enabled=True,
    ),
)

# Grant Verity backend Object Admin (full CRUD)
verity_bucket_iam = gcp.storage.BucketIAMBinding(
    "verity-artifacts-access",
    bucket=artifacts_bucket.name,
    role="roles/storage.objectAdmin",
    members=[backend_sa.email.apply(lambda email: f"serviceAccount:{email}")],
)

# Export for application configuration
pulumi.export("artifacts_bucket_name", artifacts_bucket.name)
pulumi.export("artifacts_bucket_url", artifacts_bucket.url)
```

#### Step 1.2: Deploy via GitHub Actions

```bash
# Local preview (read-only)
cd infra
mise exec -- pulumi preview

# Deploy via GitHub Actions
# 1. Go to GitHub Actions → Deploy Infrastructure
# 2. Select stack: dev
# 3. Select action: up
# 4. Approve deployment
```

#### Step 1.3: Configure Backend Environment

```bash
# Add to backend/.mise.toml
[env]
GCS_BUCKET_NAME = "verity-artifacts-dev"  # From Pulumi output
```

---

### Phase 2: Database Models (Backend)

**Duration**: ~3 hours
**Files**: `backend/src/api/models/`

#### Step 2.1: Write BDD Test for Study Model Changes

```gherkin
# backend/tests/features/study_model.feature
Feature: Study Slug and Participant Identity Flow

  Scenario: Create study with unique slug
    Given I am logged in as an organization admin
    When I create a study with slug "mobile-banking-study"
    Then the study should be created successfully
    And the study slug should be "mobile-banking-study"

  Scenario: Slug uniqueness validation
    Given a study exists with slug "mobile-banking-study"
    When I try to create another study with slug "mobile-banking-study"
    Then the creation should fail with "Slug must be unique"
```

#### Step 2.2: Modify Study Model

```python
# backend/src/api/models/study.py

from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column

class Study(Base):
    __tablename__ = "studies"

    # Existing fields...
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"))
    title: Mapped[str] = mapped_column(String, nullable=False)

    # NEW: Unique slug for reusable links
    slug: Mapped[str] = mapped_column(
        String(63), unique=True, nullable=False, index=True
    )

    # NEW: Participant identity tracking behavior
    participant_identity_flow: Mapped[str] = mapped_column(
        Enum("anonymous", "claim_after", "allow_pre_signin", name="identity_flow_enum"),
        nullable=False,
        default="anonymous"
    )
```

#### Step 2.3: Create Interview Model

```python
# backend/src/api/models/interview.py

from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
import uuid

class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(Integer, ForeignKey("studies.id"), nullable=False, index=True)

    # Public access token (UUID v4)
    access_token: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Interview status
    status: Mapped[str] = mapped_column(
        Enum("pending", "completed", "completion_pending", name="interview_status_enum"),
        nullable=False,
        default="pending",
        index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # External identity (from recruitment platform)
    external_participant_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    platform_source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Verity identity (from sign-in/claim)
    verity_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("verity_users.id"), nullable=True, index=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Artifacts (GCS URLs)
    transcript_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    recording_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Pipecat metadata
    pipecat_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    study: Mapped["Study"] = relationship("Study", back_populates="interviews")
    verity_user: Mapped["VerityUser | None"] = relationship("VerityUser", back_populates="interviews")

    @staticmethod
    def generate_access_token() -> str:
        """Generate cryptographically secure access token"""
        return str(uuid.uuid4())
```

#### Step 2.4: Create VerityUser and ParticipantProfile Models

```python
# backend/src/api/models/verity_user.py

from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

class VerityUser(Base):
    """Participant identity (separate from Organization users)"""
    __tablename__ = "verity_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_sign_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    interviews: Mapped[list["Interview"]] = relationship("Interview", back_populates="verity_user")
    profile: Mapped["ParticipantProfile | None"] = relationship("ParticipantProfile", back_populates="user", uselist=False)


class ParticipantProfile(Base):
    """Extended participant profile for cross-platform tracking"""
    __tablename__ = "participant_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    verity_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("verity_users.id"), unique=True, nullable=False, index=True)

    # Platform identities (JSON mapping)
    platform_identities: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Cached stats
    total_interviews: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_minutes_participated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationship
    user: Mapped["VerityUser"] = relationship("VerityUser", back_populates="profile")
```

#### Step 2.5: Generate Alembic Migration

```bash
cd backend
mise exec -- alembic revision --autogenerate -m "add interview models and study slug"

# Review generated migration in backend/alembic/versions/
# Run migration
mise exec -- alembic upgrade head

# Run tests to verify
make test
```

---

### Phase 3: Backend API Endpoints

**Duration**: ~8 hours
**Files**: `backend/src/api/routers/`

#### Step 3.1: Write BDD Tests FIRST

```gherkin
# backend/tests/features/interview_access.feature
Feature: Reusable Study Links

  Scenario: Participant accesses reusable link with pid
    Given a study exists with slug "mobile-banking-study"
    When I access GET /study/mobile-banking-study/start?pid=prolific_abc123
    Then I should receive a 302 redirect
    And the Location header should contain "pipecat.verity.com"
    And the Location header should contain "access_token="
    And an Interview should be created with external_participant_id "prolific_abc123"

  Scenario: Pipecat fetches interview data
    Given an Interview exists with access_token "123e4567-e89b-12d3-a456-426614174000"
    When pipecat calls GET /interview/123e4567-e89b-12d3-a456-426614174000
    Then I should receive 200 OK
    And the response should include interview metadata
    And the response should include interview guide content
```

#### Step 3.2: Implement Public Interview Router

```python
# backend/src/api/routers/interviews.py

from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import os

router = APIRouter(tags=["Public Interview Access"])


@router.get("/study/{slug}/start")
async def access_reusable_study_link(
    slug: str,
    pid: str | None = None,
    db: Session = Depends(get_db),
):
    """Create interview on-the-fly and redirect to pipecat"""

    # Lookup study by slug
    study = db.query(Study).filter(Study.slug == slug).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    # Check for existing interview (deduplication)
    if pid:
        existing_interview = db.query(Interview).filter(
            Interview.study_id == study.id,
            Interview.external_participant_id == pid,
            Interview.status == "pending"
        ).first()

        if existing_interview:
            # Return existing interview
            access_token = existing_interview.access_token
        else:
            # Create new interview
            access_token = Interview.generate_access_token()
            platform_source = pid.split("_")[0] if "_" in pid else "direct"

            interview = Interview(
                study_id=study.id,
                access_token=access_token,
                status="pending",
                external_participant_id=pid,
                platform_source=platform_source,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
            )
            db.add(interview)
            db.commit()
    else:
        # Anonymous interview (no pid)
        access_token = Interview.generate_access_token()
        interview = Interview(
            study_id=study.id,
            access_token=access_token,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        db.add(interview)
        db.commit()

    # Redirect to pipecat
    pipecat_url = os.getenv("PIPECAT_URL", "https://pipecat.verity.com")
    verity_api = os.getenv("VERITY_API_BASE", "https://verity.com/api")
    redirect_url = f"{pipecat_url}/?access_token={access_token}&verity_api={verity_api}"

    return Response(status_code=302, headers={"Location": redirect_url})


@router.get("/interview/{access_token}")
async def get_interview_data(
    access_token: str,
    db: Session = Depends(get_db),
):
    """Pipecat fetches interview guide (public endpoint)"""

    # Find interview by access_token
    interview = db.query(Interview).filter(
        Interview.access_token == access_token
    ).first()

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Check if completed (single-use token)
    if interview.status == "completed":
        raise HTTPException(status_code=404, detail="Interview already completed")

    # Check if expired
    if interview.expires_at and datetime.now(timezone.utc) > interview.expires_at:
        raise HTTPException(status_code=410, detail="Interview access token expired")

    # Return interview + study data
    study = interview.study
    return {
        "interview": {
            "interview_id": interview.id,
            "study_id": interview.study_id,
            "access_token": interview.access_token,
            "status": interview.status,
            "created_at": interview.created_at.isoformat(),
        },
        "study": {
            "title": study.title,
            "interview_guide": {
                "content_md": study.interview_guide_content,
                "updated_at": study.updated_at.isoformat(),
            }
        }
    }


@router.post("/interview/{access_token}/complete")
async def complete_interview(
    access_token: str,
    request: dict,
    db: Session = Depends(get_db),
):
    """Pipecat notifies completion (public endpoint)"""

    # Find interview
    interview = db.query(Interview).filter(
        Interview.access_token == access_token
    ).first()

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Idempotent check
    if interview.status == "completed":
        return {"message": "Interview already completed"}

    # Update interview
    interview.status = "completed"
    interview.completed_at = datetime.now(timezone.utc)
    interview.transcript_url = request.get("transcript_url")
    interview.recording_url = request.get("recording_url")
    interview.notes = request.get("notes")

    db.commit()

    return {"message": "Interview completed successfully"}
```

#### Step 3.3: Run BDD Tests

```bash
cd backend
make test

# Should see:
# ✅ Scenario: Participant accesses reusable link with pid
# ✅ Scenario: Pipecat fetches interview data
# ✅ Scenario: Pipecat notifies completion
```

---

### Phase 4: Participant Identity Endpoints

**Duration**: ~4 hours

#### Step 4.1: Write BDD Tests

```gherkin
# backend/tests/features/participant_identity.feature
Feature: Post-Interview Claim Flow

  Scenario: Participant claims completed interview
    Given a completed interview exists with access_token "abc123"
    And I am signed in as a VerityUser with firebase_uid "xyz789"
    When I POST to /interview/abc123/claim with my Firebase token
    Then I should receive 200 OK
    And the interview should be linked to my VerityUser
    And my ParticipantProfile should be created
```

#### Step 4.2: Implement Participant Router

```python
# backend/src/api/routers/participant_profile.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

router = APIRouter(tags=["Participant Identity"])


@router.post("/interview/{access_token}/claim")
async def claim_interview(
    access_token: str,
    current_user: AuthUser = Depends(get_current_participant_user),  # Firebase Auth
    db: Session = Depends(get_db),
):
    """Link completed interview to VerityUser"""

    # Find interview
    interview = db.query(Interview).filter(
        Interview.access_token == access_token
    ).first()

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Verify completed
    if interview.status != "completed":
        raise HTTPException(status_code=400, detail="Interview not completed yet")

    # Check if already claimed (idempotent)
    if interview.verity_user_id:
        existing_user = db.query(VerityUser).filter(
            VerityUser.id == interview.verity_user_id
        ).first()
        if existing_user and existing_user.firebase_uid == current_user.firebase_uid:
            return {"status": "already_claimed", "verity_user_id": existing_user.id}
        else:
            raise HTTPException(status_code=400, detail="Interview already claimed by another user")

    # Get or create VerityUser
    verity_user = db.query(VerityUser).filter(
        VerityUser.firebase_uid == current_user.firebase_uid
    ).first()

    if not verity_user:
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

    # Link interview
    interview.verity_user_id = verity_user.id
    interview.claimed_at = datetime.now(timezone.utc)

    # Update platform identities
    if interview.external_participant_id and interview.platform_source:
        profile = verity_user.profile
        if not profile.platform_identities:
            profile.platform_identities = {}
        profile.platform_identities[interview.platform_source] = interview.external_participant_id

    db.commit()

    return {
        "status": "claimed",
        "verity_user_id": verity_user.id,
        "total_interviews": len(verity_user.interviews)
    }
```

---

### Phase 5: Researcher Endpoints & Artifact Proxy

**Duration**: ~4 hours

#### Step 5.1: Write BDD Tests

```gherkin
# backend/tests/features/artifact_management.feature
Feature: Researcher Downloads Artifacts

  Scenario: Researcher lists interviews for study
    Given I am logged in as a researcher in organization "Acme Research"
    And a study "Mobile Banking" has 3 completed interviews
    When I GET /api/orgs/{org_id}/studies/{study_id}/interviews
    Then I should receive 200 OK
    And the response should contain 3 interviews

  Scenario: Researcher downloads transcript
    Given I am logged in as a researcher in organization "Acme Research"
    And an interview exists with id 42 in my organization
    And the interview has a transcript artifact
    When I GET /api/orgs/{org_id}/interviews/42/artifacts/transcript.txt
    Then I should receive 200 OK
    And the Content-Type should be "text/plain"
    And the response body should contain the transcript text
```

#### Step 5.2: Implement GCS Service

```python
# backend/src/api/services/gcs_service.py

from google.cloud import storage
from fastapi import HTTPException
import os

class GCSService:
    def __init__(self):
        self.client = storage.Client()
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "verity-artifacts-dev")
        self.bucket = self.client.bucket(self.bucket_name)

    def stream_artifact(self, interview_id: int, filename: str) -> bytes:
        """Stream artifact from GCS (API proxy pattern)"""
        blob_path = f"iv_{interview_id}/{filename}"
        blob = self.bucket.blob(blob_path)

        if not blob.exists():
            raise HTTPException(status_code=404, detail="Artifact not found")

        return blob.download_as_bytes()
```

#### Step 5.3: Implement Org Interview Router

```python
# backend/src/api/routers/org_interviews.py

from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.orm import Session

router = APIRouter(tags=["Researcher Endpoints"])


@router.get("/api/orgs/{org_id}/studies/{study_id}/interviews")
async def list_study_interviews(
    org_id: int,
    study_id: int,
    current_user: User = Depends(get_current_org_user),  # Firebase Auth
    db: Session = Depends(get_db),
):
    """List interviews for study (researcher endpoint)"""

    # Verify user belongs to org
    if current_user.organization_id != org_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Verify study belongs to org
    study = db.query(Study).filter(
        Study.id == study_id,
        Study.organization_id == org_id
    ).first()

    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    # Query interviews
    interviews = db.query(Interview).filter(
        Interview.study_id == study_id,
        Interview.status == "completed"
    ).order_by(Interview.completed_at.desc()).all()

    return {
        "interviews": [
            {
                "id": i.id,
                "study_id": i.study_id,
                "status": i.status,
                "created_at": i.created_at.isoformat(),
                "completed_at": i.completed_at.isoformat() if i.completed_at else None,
                "external_participant_id": i.external_participant_id,
                "platform_source": i.platform_source,
                "has_transcript": bool(i.transcript_url),
                "has_recording": bool(i.recording_url),
            }
            for i in interviews
        ]
    }


@router.get("/api/orgs/{org_id}/interviews/{interview_id}/artifacts/{filename}")
async def download_artifact(
    org_id: int,
    interview_id: int,
    filename: str,
    current_user: User = Depends(get_current_org_user),
    db: Session = Depends(get_db),
    gcs: GCSService = Depends(get_gcs_service),
):
    """Stream interview artifact (API proxy pattern)"""

    # Verify user belongs to org
    if current_user.organization_id != org_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Verify interview belongs to org
    interview = db.query(Interview).join(Study).filter(
        Interview.id == interview_id,
        Study.organization_id == org_id
    ).first()

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Stream artifact from GCS
    artifact_bytes = gcs.stream_artifact(interview_id, filename)

    # Set appropriate Content-Type
    content_type = "audio/wav" if filename == "recording.wav" else "text/plain"

    return Response(
        content=artifact_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
```

---

### Phase 6: Frontend UI Components

**Duration**: ~10 hours

#### Step 6.1: Write Frontend BDD Tests

```gherkin
# frontend/tests/features/study_settings.feature
Feature: Study Settings with Reusable Link

  Scenario: Researcher views reusable link template
    Given I am logged in as a researcher
    And I have a study "Mobile Banking" with slug "mobile-banking-study"
    When I navigate to the study settings page
    Then I should see a reusable link template
    And the link should be "https://verity.com/study/mobile-banking-study/start?pid={{PARTICIPANT_ID}}"
    And I should see a "Copy Link" button
```

#### Step 6.2: Implement API Client

```typescript
// frontend/src/api/interviews.ts

export interface Interview {
  id: number;
  study_id: number;
  status: 'pending' | 'completed' | 'completion_pending';
  created_at: string;
  completed_at: string | null;
  external_participant_id: string | null;
  platform_source: string | null;
  has_transcript: boolean;
  has_recording: boolean;
}

export async function listStudyInterviews(
  orgId: number,
  studyId: number
): Promise<Interview[]> {
  const response = await fetch(
    `/api/orgs/${orgId}/studies/${studyId}/interviews`,
    {
      headers: {
        Authorization: `Bearer ${await getFirebaseToken()}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch interviews');
  }

  const data = await response.json();
  return data.interviews;
}

export async function downloadArtifact(
  orgId: number,
  interviewId: number,
  filename: string
): Promise<Blob> {
  const response = await fetch(
    `/api/orgs/${orgId}/interviews/${interviewId}/artifacts/${filename}`,
    {
      headers: {
        Authorization: `Bearer ${await getFirebaseToken()}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to download artifact');
  }

  return response.blob();
}
```

#### Step 6.3: Implement Study Settings Component

```tsx
// frontend/src/components/StudySettings.tsx

import React, { useState } from 'react';
import { Study } from '../types';

interface StudySettingsProps {
  study: Study;
}

export function StudySettings({ study }: StudySettingsProps) {
  const [copied, setCopied] = useState(false);

  const reusableLinkTemplate = `${window.location.origin}/study/${study.slug}/start?pid={{PARTICIPANT_ID}}`;

  const handleCopyLink = () => {
    navigator.clipboard.writeText(reusableLinkTemplate);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="study-settings">
      <h2>Study Settings</h2>

      <section>
        <h3>Reusable Interview Link</h3>
        <p>Share this link with participants or integrate with recruitment platforms:</p>

        <div className="link-display">
          <code>{reusableLinkTemplate}</code>
          <button onClick={handleCopyLink}>
            {copied ? 'Copied!' : 'Copy Link'}
          </button>
        </div>

        <details>
          <summary>How to use with recruitment platforms</summary>
          <ul>
            <li><strong>Prolific:</strong> Replace {"{{PARTICIPANT_ID}}"} with {"{{%PROLIFIC_PID%}}"}</li>
            <li><strong>Respondent:</strong> Replace {"{{PARTICIPANT_ID}}"} with {"{{respondent_id}}"}</li>
            <li><strong>Direct distribution:</strong> Remove the ?pid= parameter entirely</li>
          </ul>
        </details>
      </section>
    </div>
  );
}
```

---

## Testing Workflow

### BDD-First Development Cycle

**CRITICAL**: Always follow this workflow (Constitution principle I)

```bash
# 1. Write Gherkin scenario
vim backend/tests/features/interview_access.feature

# 2. Run tests (should FAIL)
cd backend
make test

# 3. Implement minimal code to pass test
vim backend/src/api/routers/interviews.py

# 4. Run tests (should PASS)
make test

# 5. Refactor while keeping tests green
vim backend/src/api/routers/interviews.py
make test

# 6. Repeat for next scenario
```

### Quality Checks

```bash
# Format code
make format

# Run all checks (format + lint + types)
make check

# Should see:
# ✅ ruff format (no changes)
# ✅ ruff check (no warnings)
# ✅ ty src (no type errors)
```

---

## Deployment

### Local Testing

```bash
# Start backend dev server
cd backend
make dev

# In another terminal, start frontend
cd frontend
npm run dev

# Test reusable link access
curl -v http://localhost:8000/study/mobile-banking-study/start?pid=prolific_abc123
```

### CI/CD Pipeline

```bash
# Pre-commit hooks run automatically
git commit -m "feat: add interview access endpoint"

# Pre-push hooks run all tests
git push origin 002-self-led-interview

# GitHub Actions runs:
# 1. Format checks
# 2. Lint checks
# 3. Type checks
# 4. Backend BDD tests
# 5. Frontend E2E tests
# 6. Cloud Run deployment (if all pass)
```

---

## Common Issues

### Issue: Migration conflicts

```bash
# If multiple migrations created simultaneously
cd backend
mise exec -- alembic heads  # Show all heads
mise exec -- alembic merge -m "merge migrations"
mise exec -- alembic upgrade head
```

### Issue: Firebase Auth token invalid

```bash
# Ensure Firebase emulator is running
make dev

# Check token expiration (default 1 hour)
# Refresh token in frontend:
const idToken = await auth.currentUser.getIdToken(true);  // Force refresh
```

### Issue: GCS bucket not accessible locally

```bash
# Use MinIO for local development
# backend/.mise.toml
[env]
STORAGE_EMULATOR_HOST = "http://localhost:9000"  # MinIO
GCS_BUCKET_NAME = "verity-artifacts-local"
```

---

## Next Steps After Implementation

1. **Run full test suite**: `make test` (backend + frontend)
2. **Create pull request**: Follow PR template, reference spec
3. **Code review**: Address feedback, maintain BDD coverage
4. **Deploy to dev**: Via GitHub Actions (automatic)
5. **Manual testing**: Test full flow end-to-end
6. **Deploy to prod**: Manual approval in GitHub Actions

---

## Reference Documents

- [Feature Specification](./spec.md) - Requirements and user stories
- [Research Findings](./research.md) - Technical decisions and rationale
- [Data Model](./data-model.md) - Database schema and relationships
- [API Contracts](./contracts/api-endpoints.yaml) - OpenAPI specification
- [Constitution](.specify/memory/constitution.md) - Development principles

---

**Questions?** Check the constitution, specs, or ask in #engineering channel.
