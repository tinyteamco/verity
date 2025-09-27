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


class DatabaseStatus(BaseModel):
    connected: bool
    error: str | None = None


class HealthResponse(BaseModel):
    healthy: bool
    service: str
    version: str
    database: DatabaseStatus
