from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrganizationCreate(BaseModel):
    name: str


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    org_id: str
    name: str
    created_at: datetime


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
    created_at: datetime
    users: list[UserResponse]


class StudyCreate(BaseModel):
    title: str
    description: str | None = None


class StudyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_id: str
    title: str
    description: str | None
    org_id: str
    created_at: datetime
    updated_at: datetime | None


class StudyUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class StudyList(BaseModel):
    items: list[StudyResponse]


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
