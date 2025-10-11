import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class OrganizationCreate(BaseModel):
    name: str  # URL-safe slug: lowercase, alphanumeric, hyphens only
    display_name: str
    description: str | None = None
    owner_email: str

    @field_validator("name")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate organization name is a valid slug (lowercase, alphanumeric, hyphens)."""
        if not v:
            raise ValueError("Organization name cannot be empty")

        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Organization name must be lowercase letters, numbers, "
                "and hyphens only (no spaces, no uppercase)"
            )

        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Organization name cannot start or end with a hyphen")

        if "--" in v:
            raise ValueError("Organization name cannot contain consecutive hyphens")

        return v


class OwnerCreationResponse(BaseModel):
    user_id: str
    email: str
    role: str
    password_reset_link: str


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    org_id: str
    name: str
    display_name: str
    description: str | None
    created_at: datetime


class OrganizationWithOwnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    org_id: str
    name: str
    display_name: str
    description: str | None
    created_at: datetime
    owner: OwnerCreationResponse


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: str
    role: str
    created_at: datetime


class OrganizationWithUsersResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    org_id: str
    name: str
    display_name: str
    description: str | None
    created_at: datetime
    users: list[UserResponse]


class StudyCreate(BaseModel):
    title: str
    description: str | None = None


class StudyGenerateRequest(BaseModel):
    topic: str


class StudyWithGuideResponse(BaseModel):
    study: "StudyResponse"
    guide: "InterviewGuideResponse"


class StudyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_id: str
    title: str
    description: str | None
    slug: str
    participant_identity_flow: str
    org_id: str
    created_at: datetime
    updated_at: datetime | None


class StudyUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class StudyList(BaseModel):
    items: list[StudyResponse]


class UserCreate(BaseModel):
    email: str
    role: str


class UserCreationResponse(BaseModel):
    user_id: str
    email: str
    role: str
    password_reset_link: str


class UserList(BaseModel):
    items: list[UserResponse]


class InterviewGuideCreate(BaseModel):
    content_md: str


class InterviewGuideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_id: str
    content_md: str
    updated_at: datetime


class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interview_id: str
    study_id: str
    access_token: str
    interviewee_firebase_uid: str | None
    status: str
    created_at: datetime
    completed_at: datetime | None
    transcript_url: str | None
    recording_url: str | None
    notes: str | None


class InterviewLinkResponse(BaseModel):
    interview: InterviewResponse
    interview_url: str


class InterviewCompleteRequest(BaseModel):
    transcript_url: str
    recording_url: str | None = None
    notes: str | None = None


class InterviewList(BaseModel):
    items: list[InterviewResponse]


class DatabaseStatus(BaseModel):
    connected: bool
    error: str | None = None


class AudioRecordingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recording_id: str
    interview_id: str
    uri: str
    duration_ms: int | None
    mime_type: str | None
    sample_rate_hz: int | None
    file_size_bytes: int | None
    created_at: datetime


class HealthResponse(BaseModel):
    healthy: bool
    service: str
    version: str
    database: DatabaseStatus


class TranscriptSegment(BaseModel):
    start_ms: int
    end_ms: int
    text: str


class TranscriptFinalizeRequest(BaseModel):
    lang: str
    source: str
    segments: list[TranscriptSegment]


class TranscriptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transcript_id: str
    interview_id: str
    language: str
    full_text: str
    created_at: datetime
