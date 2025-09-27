from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from ..auth import (
    AuthUser,
    OrgUser,
    get_org_user_impl,
    require_organization_user,
    require_super_admin,
)
from ..database import get_db
from ..models import Organization, User
from ..schemas import HealthResponse, OrganizationCreate, OrganizationResponse, UserResponse

app = FastAPI(
    title="Verity API",
    version="0.1.0",
    description="UXR Platform Backend",
)


def get_org_user(
    user: Annotated[AuthUser, Depends(require_organization_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OrgUser:
    """Get organization user with full context from database"""
    return get_org_user_impl(user, db)


def require_owner_or_admin(
    org_user: Annotated[OrgUser, Depends(get_org_user)],
) -> OrgUser:
    """Require owner or admin role"""
    if org_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Owner or admin role required")
    return org_user


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(healthy=True, service="verity-backend", version="0.1.0")


@app.post("/orgs", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: Annotated[AuthUser, Depends(require_super_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> OrganizationResponse:
    # Create organization
    org = Organization(name=org_data.name)
    db.add(org)
    db.commit()
    db.refresh(org)

    return OrganizationResponse(org_id=str(org.id), name=org.name, created_at=org.created_at)


@app.get("/orgs/current", response_model=OrganizationResponse)
async def get_current_organization(
    org_user: Annotated[OrgUser, Depends(get_org_user)],
) -> OrganizationResponse:
    """Get current user's organization details"""
    return OrganizationResponse(
        org_id=str(org_user.organization_id),
        name=org_user.organization_name,
        created_at=org_user.organization_created_at,
    )


@app.get("/orgs/current/users", response_model=list[UserResponse])
async def list_organization_users(
    org_user: Annotated[OrgUser, Depends(require_owner_or_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UserResponse]:
    """List users in the current organization (owner/admin only)"""
    users = db.query(User).filter(User.organization_id == org_user.organization_id).all()

    return [
        UserResponse(
            user_id=str(user.id),
            email=user.email,
            role=user.role,
            created_at=user.created_at,
        )
        for user in users
    ]
