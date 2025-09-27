from datetime import datetime

from pydantic import BaseModel


class OrganizationCreate(BaseModel):
    name: str


class OrganizationResponse(BaseModel):
    org_id: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user_id: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationWithUsersResponse(BaseModel):
    org_id: str
    name: str
    created_at: datetime
    users: list[UserResponse]

    class Config:
        from_attributes = True


class StudyCreate(BaseModel):
    title: str
    description: str | None = None


class StudyResponse(BaseModel):
    study_id: str
    title: str
    description: str | None
    organization_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    healthy: bool
    service: str
    version: str
