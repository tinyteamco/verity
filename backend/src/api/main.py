from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
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
from ..database_utils import check_database_connectivity_with_session, ensure_database_connectivity
from ..models import Organization, Study, User
from ..schemas import (
    HealthResponse,
    OrganizationCreate,
    OrganizationResponse,
    StudyCreate,
    StudyList,
    StudyResponse,
    StudyUpdate,
    UserResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    ensure_database_connectivity()
    yield
    # Shutdown - nothing needed for now


app = FastAPI(
    title="Verity API",
    version="0.1.0",
    description="UXR Platform Backend",
    lifespan=lifespan,
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
async def health_check(db: Annotated[Session, Depends(get_db)]) -> HealthResponse:
    """Health check endpoint with database connectivity status"""
    db_status = check_database_connectivity_with_session(db)

    # Overall health is healthy only if database is connected
    overall_healthy = db_status.connected

    return HealthResponse(
        healthy=overall_healthy, service="verity-backend", version="0.1.0", database=db_status
    )


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


# Study Management Endpoints


@app.post("/studies", response_model=StudyResponse, status_code=201)
async def create_study(
    study_data: StudyCreate,
    org_user: Annotated[OrgUser, Depends(get_org_user)],
    db: Annotated[Session, Depends(get_db)],
) -> StudyResponse:
    """Create a new study for the current organization"""
    study = Study(
        title=study_data.title,
        description=study_data.description,
        organization_id=org_user.organization_id,
    )
    db.add(study)
    db.commit()
    db.refresh(study)

    return StudyResponse(
        study_id=str(study.id),
        title=study.title,
        description=study.description,
        org_id=str(study.organization_id),
        created_at=study.created_at,
        updated_at=study.updated_at,
    )


@app.get("/studies", response_model=StudyList)
async def list_studies(
    org_user: Annotated[OrgUser, Depends(get_org_user)],
    db: Annotated[Session, Depends(get_db)],
) -> StudyList:
    """List all studies for the current organization"""
    studies = db.query(Study).filter(Study.organization_id == org_user.organization_id).all()

    study_responses = [
        StudyResponse(
            study_id=str(study.id),
            title=study.title,
            description=study.description,
            org_id=str(study.organization_id),
            created_at=study.created_at,
            updated_at=study.updated_at,
        )
        for study in studies
    ]

    return StudyList(items=study_responses)


@app.get("/studies/{study_id}", response_model=StudyResponse)
async def get_study(
    study_id: int,
    org_user: Annotated[OrgUser, Depends(get_org_user)],
    db: Annotated[Session, Depends(get_db)],
) -> StudyResponse:
    """Get a specific study by ID"""
    study = (
        db.query(Study)
        .filter(Study.id == study_id, Study.organization_id == org_user.organization_id)
        .first()
    )

    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    return StudyResponse(
        study_id=str(study.id),
        title=study.title,
        description=study.description,
        org_id=str(study.organization_id),
        created_at=study.created_at,
        updated_at=study.updated_at,
    )


@app.patch("/studies/{study_id}", response_model=StudyResponse)
async def update_study(
    study_id: int,
    study_update: StudyUpdate,
    org_user: Annotated[OrgUser, Depends(get_org_user)],
    db: Annotated[Session, Depends(get_db)],
) -> StudyResponse:
    """Update a study"""
    study = (
        db.query(Study)
        .filter(Study.id == study_id, Study.organization_id == org_user.organization_id)
        .first()
    )

    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    # Update fields if provided
    if study_update.title is not None:
        study.title = study_update.title
    if study_update.description is not None:
        study.description = study_update.description

    db.commit()
    db.refresh(study)

    return StudyResponse(
        study_id=str(study.id),
        title=study.title,
        description=study.description,
        org_id=str(study.organization_id),
        created_at=study.created_at,
        updated_at=study.updated_at,
    )


@app.delete("/studies/{study_id}")
async def delete_study(
    study_id: int,
    org_user: Annotated[OrgUser, Depends(get_org_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Delete a study"""
    study = (
        db.query(Study)
        .filter(Study.id == study_id, Study.organization_id == org_user.organization_id)
        .first()
    )

    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    db.delete(study)
    db.commit()

    return {"message": "Study deleted successfully"}
