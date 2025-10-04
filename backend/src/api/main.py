import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from firebase_admin import auth
from scalar_fastapi import get_scalar_api_reference
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import (
    AuthUser,
    OrgUser,
    get_current_user,
    get_org_user_impl,
    require_interviewee_user,
    require_organization_user,
    require_super_admin,
)
from ..database import get_db
from ..database_utils import check_database_connectivity_with_session, ensure_database_connectivity
from ..models import (
    AudioRecording,
    Interview,
    InterviewGuide,
    Organization,
    Study,
    Transcript,
    TranscriptSegment,
    User,
)
from ..schemas import (
    AudioRecordingResponse,
    HealthResponse,
    InterviewCompleteRequest,
    InterviewGuideCreate,
    InterviewGuideResponse,
    InterviewLinkResponse,
    InterviewList,
    InterviewResponse,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationWithOwnerResponse,
    OwnerCreationResponse,
    StudyCreate,
    StudyList,
    StudyResponse,
    StudyUpdate,
    TranscriptFinalizeRequest,
    TranscriptResponse,
    UserCreate,
    UserCreationResponse,
    UserList,
    UserResponse,
)
from ..storage import generate_audio_object_name, get_storage_client


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
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware for local development and E2E tests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],  # Vite dev server + potential prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router with /api prefix for Firebase Hosting proxy
api_router = APIRouter(prefix="/api")


def get_org_user(
    user: Annotated[AuthUser, Depends(require_organization_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OrgUser:
    """Get organization user with full context from database"""
    return get_org_user_impl(user, db)


def require_owner_or_admin(
    org_user: Annotated[OrgUser, Depends(get_org_user)],
) -> OrgUser:
    """Require owner or admin role (super admins automatically pass)"""
    if org_user.role not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Owner or admin role required")
    return org_user


@api_router.get("/health", response_model=HealthResponse)
async def health_check(db: Annotated[Session, Depends(get_db)]) -> HealthResponse:
    """Health check endpoint with database connectivity status"""
    db_status = check_database_connectivity_with_session(db)

    # Overall health is healthy only if database is connected
    overall_healthy = db_status.connected

    return HealthResponse(
        healthy=overall_healthy, service="verity-backend", version="0.1.0", database=db_status
    )


@api_router.get("/orgs", response_model=list[OrganizationResponse])
async def list_organizations(
    current_user: Annotated[AuthUser, Depends(require_super_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> list[OrganizationResponse]:
    """List all active organizations (super admin only)"""
    orgs = db.query(Organization).filter(Organization.deleted_at.is_(None)).all()
    return [
        OrganizationResponse(
            org_id=str(org.id),
            name=org.name,
            display_name=org.display_name,
            description=org.description,
            created_at=org.created_at,
        )
        for org in orgs
    ]


@api_router.post("/orgs", status_code=201)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: Annotated[AuthUser, Depends(require_super_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> OrganizationWithOwnerResponse:
    # Create organization
    org = Organization(
        name=org_data.name,
        display_name=org_data.display_name,
        description=org_data.description,
    )
    db.add(org)
    try:
        db.commit()
        db.refresh(org)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Organization with name '{org_data.name}' already exists"
        ) from e

    # Create owner user
    try:
        # Create Firebase user without password
        firebase_user = auth.create_user(
            email=org_data.owner_email,
            email_verified=False,
        )

        # Set custom claims for organization tenant
        auth.set_custom_user_claims(firebase_user.uid, {"tenant": "organization"})

        # Generate password reset link
        password_reset_link = auth.generate_password_reset_link(
            email=org_data.owner_email,
            action_code_settings=auth.ActionCodeSettings(
                url="http://localhost:5173/login",  # TODO: Make this configurable
            ),
        )

        # Create User record in database
        user = User(
            firebase_uid=firebase_user.uid,
            email=org_data.owner_email,
            role="owner",
            organization_id=org.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Return organization with owner details
        owner_response = OwnerCreationResponse(
            user_id=str(user.id),
            email=user.email,
            role=user.role,
            password_reset_link=password_reset_link,
        )

        return OrganizationWithOwnerResponse(
            org_id=str(org.id),
            name=org.name,
            display_name=org.display_name,
            description=org.description,
            created_at=org.created_at,
            owner=owner_response,
        )

    except Exception as e:
        # Rollback org creation if owner creation fails
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create owner: {e!s}") from e


@api_router.get("/orgs/current", response_model=OrganizationResponse)
async def get_current_organization(
    org_user: Annotated[OrgUser, Depends(get_org_user)],
) -> OrganizationResponse:
    """Get current user's organization details"""
    return OrganizationResponse(
        org_id=str(org_user.organization_id),
        name=org_user.organization_name,
        display_name=org_user.organization_display_name,
        description=org_user.organization_description,
        created_at=org_user.organization_created_at,
    )


def _get_organization_users(org_id: int, db: Session) -> UserList:
    """
    Helper function to get users for an organization.
    Shared by both /orgs/current/users and /orgs/{org_id}/users endpoints.
    """
    users = db.query(User).filter(User.organization_id == org_id).all()

    return UserList(
        items=[
            UserResponse(
                user_id=str(user.id),
                email=user.email,
                role=user.role,
                created_at=user.created_at,
            )
            for user in users
        ]
    )


@api_router.get("/orgs/current/users", response_model=UserList)
async def list_organization_users(
    org_user: Annotated[OrgUser, Depends(require_owner_or_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> UserList:
    """List users in the current organization (owner/admin only)"""
    return _get_organization_users(org_user.organization_id, db)


@api_router.get("/orgs/{org_id}", response_model=OrganizationResponse)
async def get_organization_by_id(
    org_id: int,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OrganizationResponse:
    """Get organization by ID (super admin can access any, users only their own)"""
    # Get organization from database (only active orgs)
    org = (
        db.query(Organization)
        .filter(Organization.id == org_id, Organization.deleted_at.is_(None))
        .first()
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Super admins can access any organization
    if current_user.is_super_admin:
        return OrganizationResponse(
            org_id=str(org.id),
            name=org.name,
            display_name=org.display_name,
            description=org.description,
            created_at=org.created_at,
        )

    # Regular users can only access their own organization
    user = db.query(User).filter(User.firebase_uid == current_user.firebase_uid).first()
    if not user or user.organization_id != org_id:
        raise HTTPException(
            status_code=403, detail="You don't have permission to access this organization"
        )

    return OrganizationResponse(
        org_id=str(org.id),
        name=org.name,
        display_name=org.display_name,
        description=org.description,
        created_at=org.created_at,
    )


@api_router.get("/orgs/{org_id}/users", response_model=UserList)
async def list_organization_users_by_id(
    org_id: int,
    current_user: Annotated[AuthUser, Depends(require_super_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> UserList:
    """List users in a specific organization (super admin only)"""
    # Verify organization exists and is not deleted
    org = (
        db.query(Organization)
        .filter(Organization.id == org_id, Organization.deleted_at.is_(None))
        .first()
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Return users using shared helper
    return _get_organization_users(org_id, db)


def _create_organization_user(
    email: str,
    role: str,
    organization_id: int,
    db: Session,
) -> tuple[User, str]:
    """
    Helper function to create a user in an organization.

    Returns:
        Tuple of (User model, password_reset_link)

    Raises:
        HTTPException: If user creation fails
    """
    # Validate role
    if role not in ["admin", "member"]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid role. Owner role can only be created with organization. "
                "Use 'admin' or 'member'."
            ),
        )

    # Check if user already exists in this organization
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail=f"User with email '{email}' already exists")

    try:
        # Create Firebase user without password
        firebase_user = auth.create_user(
            email=email,
            email_verified=False,
        )

        # Set custom claims for organization tenant
        auth.set_custom_user_claims(firebase_user.uid, {"tenant": "organization"})

        # Generate password reset link
        password_reset_link = auth.generate_password_reset_link(
            email=email,
            action_code_settings=auth.ActionCodeSettings(
                url="http://localhost:5173/login",  # TODO: Make this configurable
            ),
        )

        # Create User record in database
        user = User(
            firebase_uid=firebase_user.uid,
            email=email,
            role=role,
            organization_id=organization_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return user, password_reset_link

    except Exception as e:
        db.rollback()
        # Clean up Firebase user if database commit fails
        try:
            if "firebase_user" in locals():
                auth.delete_user(firebase_user.uid)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail=f"Failed to create user: {e!s}") from e


@api_router.post("/orgs/{org_id}/users", response_model=UserCreationResponse, status_code=201)
async def create_organization_user(
    org_id: int,
    user_data: UserCreate,
    current_user: Annotated[AuthUser, Depends(require_super_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> UserCreationResponse:
    """Create a new user in an organization (super admin only)"""
    # Verify organization exists and is not deleted
    org = (
        db.query(Organization)
        .filter(Organization.id == org_id, Organization.deleted_at.is_(None))
        .first()
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Create user using shared helper
    user, password_reset_link = _create_organization_user(
        email=user_data.email,
        role=user_data.role,
        organization_id=org_id,
        db=db,
    )

    return UserCreationResponse(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        password_reset_link=password_reset_link,
    )


@api_router.delete("/orgs/{org_id}", status_code=204)
async def delete_organization(
    org_id: int,
    current_user: Annotated[AuthUser, Depends(require_super_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Soft delete an organization (super admin only)"""
    # Get organization
    org = (
        db.query(Organization)
        .filter(Organization.id == org_id, Organization.deleted_at.is_(None))
        .first()
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Soft delete by setting deleted_at timestamp
    org.deleted_at = datetime.now(UTC)
    db.commit()


# Study Management Endpoints


@api_router.post("/studies", response_model=StudyResponse, status_code=201)
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


@api_router.get("/studies", response_model=StudyList)
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


@api_router.get("/studies/{study_id}", response_model=StudyResponse)
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


@api_router.patch("/studies/{study_id}", response_model=StudyResponse)
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


@api_router.delete("/studies/{study_id}")
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


# Study Guide Management Endpoints


@api_router.put("/studies/{study_id}/guide", response_model=InterviewGuideResponse)
async def upsert_study_guide(
    study_id: int,
    guide_data: InterviewGuideCreate,
    org_user: Annotated[OrgUser, Depends(get_org_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InterviewGuideResponse:
    """Create or update an interview guide for a study"""
    # Check if study exists and belongs to user's organization
    study = (
        db.query(Study)
        .filter(Study.id == study_id, Study.organization_id == org_user.organization_id)
        .first()
    )

    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    # Check if guide already exists
    existing_guide = db.query(InterviewGuide).filter(InterviewGuide.study_id == study_id).first()

    if existing_guide:
        # Update existing guide
        existing_guide.content_md = guide_data.content_md
        db.commit()
        db.refresh(existing_guide)
        guide = existing_guide
    else:
        # Create new guide
        guide = InterviewGuide(
            study_id=study_id,
            content_md=guide_data.content_md,
        )
        db.add(guide)
        db.commit()
        db.refresh(guide)

    return InterviewGuideResponse(
        study_id=str(guide.study_id),
        content_md=guide.content_md,
        updated_at=guide.updated_at,
    )


@api_router.get("/studies/{study_id}/guide", response_model=InterviewGuideResponse)
async def get_study_guide(
    study_id: int,
    org_user: Annotated[OrgUser, Depends(get_org_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InterviewGuideResponse:
    """Get the interview guide for a study"""
    # Check if study exists and belongs to user's organization
    study = (
        db.query(Study)
        .filter(Study.id == study_id, Study.organization_id == org_user.organization_id)
        .first()
    )

    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    # Get the interview guide
    guide = db.query(InterviewGuide).filter(InterviewGuide.study_id == study_id).first()

    if not guide:
        raise HTTPException(status_code=404, detail="Interview guide not found")

    return InterviewGuideResponse(
        study_id=str(guide.study_id),
        content_md=guide.content_md,
        updated_at=guide.updated_at,
    )


# Interview Management Endpoints


@api_router.post(
    "/studies/{study_id}/interviews", response_model=InterviewLinkResponse, status_code=201
)
async def generate_interview_link(
    study_id: int,
    org_user: Annotated[OrgUser, Depends(get_org_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InterviewLinkResponse:
    """Generate a new interview link for a study"""
    import uuid

    # Check if study exists and belongs to user's organization
    study = (
        db.query(Study)
        .filter(Study.id == study_id, Study.organization_id == org_user.organization_id)
        .first()
    )

    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    # Generate unique access token
    access_token = str(uuid.uuid4())

    # Create interview
    interview = Interview(
        study_id=study_id,
        access_token=access_token,
        status="pending",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    # Create interview URL (this would be configurable in production)
    interview_url = f"https://app.verity.com/interview/{access_token}"

    return InterviewLinkResponse(
        interview=InterviewResponse(
            interview_id=str(interview.id),
            study_id=str(interview.study_id),
            access_token=interview.access_token,
            interviewee_firebase_uid=interview.interviewee_firebase_uid,
            status=interview.status,
            created_at=interview.created_at,
            completed_at=interview.completed_at,
            transcript_url=interview.transcript_url,
            recording_url=interview.recording_url,
            notes=interview.notes,
        ),
        interview_url=interview_url,
    )


@api_router.get("/studies/{study_id}/interviews", response_model=InterviewList)
async def list_interviews(
    study_id: int,
    org_user: Annotated[OrgUser, Depends(get_org_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InterviewList:
    """List all interviews for a study"""
    # Check if study exists and belongs to user's organization
    study = (
        db.query(Study)
        .filter(Study.id == study_id, Study.organization_id == org_user.organization_id)
        .first()
    )

    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    # Get interviews for the study
    interviews = db.query(Interview).filter(Interview.study_id == study_id).all()

    interview_responses = [
        InterviewResponse(
            interview_id=str(interview.id),
            study_id=str(interview.study_id),
            access_token=interview.access_token,
            interviewee_firebase_uid=interview.interviewee_firebase_uid,
            status=interview.status,
            created_at=interview.created_at,
            completed_at=interview.completed_at,
            transcript_url=interview.transcript_url,
            recording_url=interview.recording_url,
            notes=interview.notes,
        )
        for interview in interviews
    ]

    return InterviewList(items=interview_responses)


@api_router.get("/studies/{study_id}/interviews/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    study_id: int,
    interview_id: int,
    org_user: Annotated[OrgUser, Depends(get_org_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InterviewResponse:
    """Get a specific interview by ID"""
    # Check if study exists and belongs to user's organization
    study = (
        db.query(Study)
        .filter(Study.id == study_id, Study.organization_id == org_user.organization_id)
        .first()
    )

    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    # Get the interview
    interview = (
        db.query(Interview)
        .filter(Interview.id == interview_id, Interview.study_id == study_id)
        .first()
    )

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    return InterviewResponse(
        interview_id=str(interview.id),
        study_id=str(interview.study_id),
        access_token=interview.access_token,
        interviewee_firebase_uid=interview.interviewee_firebase_uid,
        status=interview.status,
        created_at=interview.created_at,
        completed_at=interview.completed_at,
        transcript_url=interview.transcript_url,
        recording_url=interview.recording_url,
        notes=interview.notes,
    )


# Public Interview Endpoints (No Authentication Required)


@api_router.get("/interview/{access_token}")
async def get_interview_public(
    access_token: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Access interview via link (public endpoint)"""
    # Get the interview by access token
    interview = db.query(Interview).filter(Interview.access_token == access_token).first()

    if not interview or interview.status == "completed":
        raise HTTPException(status_code=404, detail="Interview not found or already completed")

    # Get the study and interview guide
    study = db.query(Study).filter(Study.id == interview.study_id).first()
    guide = db.query(InterviewGuide).filter(InterviewGuide.study_id == interview.study_id).first()

    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    return {
        "interview": {
            "interview_id": str(interview.id),
            "study_id": str(interview.study_id),
            "access_token": interview.access_token,
            "status": interview.status,
            "created_at": interview.created_at.isoformat(),
        },
        "study": {
            "title": study.title,
            "interview_guide": {
                "content_md": guide.content_md if guide else "No guide available",
                "updated_at": guide.updated_at.isoformat() if guide else None,
            },
        },
    }


@api_router.post("/interview/{access_token}/complete")
async def complete_interview(
    access_token: str,
    completion_data: InterviewCompleteRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Submit interview completion (public endpoint)"""
    from datetime import datetime

    # Get the interview by access token
    interview = db.query(Interview).filter(Interview.access_token == access_token).first()

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.status == "completed":
        raise HTTPException(status_code=400, detail="Interview already completed")

    # Update interview with completion data
    interview.status = "completed"
    interview.completed_at = datetime.now(UTC)
    interview.transcript_url = completion_data.transcript_url
    interview.recording_url = completion_data.recording_url
    interview.notes = completion_data.notes

    db.commit()

    return {"message": "Interview completed successfully"}


@api_router.post("/interview/{access_token}/claim")
async def claim_interview(
    access_token: str,
    current_user: Annotated[AuthUser, Depends(require_interviewee_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Associate interview with authenticated user"""
    # Get the interview by access token
    interview = db.query(Interview).filter(Interview.access_token == access_token).first()

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.interviewee_firebase_uid is not None:
        raise HTTPException(status_code=400, detail="Interview already claimed")

    # Associate interview with current user
    interview.interviewee_firebase_uid = current_user.firebase_uid
    db.commit()

    return {"message": "Interview claimed successfully"}


# Audio Recording Endpoints


@api_router.post("/recordings:upload", response_model=AudioRecordingResponse, status_code=201)
async def upload_recording(
    interview_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    mime: Annotated[str | None, Form()] = None,
    sample_rate_hz: Annotated[int | None, Form()] = None,
    duration_ms: Annotated[int | None, Form()] = None,
) -> AudioRecordingResponse:
    """Upload audio recording for an interview"""

    # Validate interview exists
    interview = db.query(Interview).filter(Interview.id == int(interview_id)).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Check if recording already exists
    existing_recording = (
        db.query(AudioRecording).filter(AudioRecording.interview_id == int(interview_id)).first()
    )
    if existing_recording:
        raise HTTPException(status_code=400, detail="Recording already exists for this interview")

    # Validate file type if provided
    detected_mime = mime or file.content_type
    if detected_mime and not detected_mime.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")

    # Generate object name and upload to storage
    storage_client = get_storage_client()
    object_name = generate_audio_object_name(int(interview_id), file.filename or "recording.wav")

    try:
        # Get file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        # Upload to object storage
        uri = await storage_client.upload_file(
            bucket="audio-recordings",
            object_name=object_name,
            file_data=file.file,
            content_type=detected_mime,
            file_size=file_size,
        )

        # Create database record
        audio_recording = AudioRecording(
            interview_id=int(interview_id),
            uri=uri,
            duration_ms=duration_ms,
            mime_type=detected_mime,
            sample_rate_hz=sample_rate_hz,
            file_size_bytes=file_size,
        )

        db.add(audio_recording)
        db.commit()
        db.refresh(audio_recording)

        return AudioRecordingResponse(
            recording_id=str(audio_recording.id),
            interview_id=str(audio_recording.interview_id),
            uri=audio_recording.uri,
            duration_ms=audio_recording.duration_ms,
            mime_type=audio_recording.mime_type,
            sample_rate_hz=audio_recording.sample_rate_hz,
            file_size_bytes=audio_recording.file_size_bytes,
            created_at=audio_recording.created_at,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload recording: {e!s}") from e


@api_router.get("/recordings/{recording_id}/download")
async def download_recording(
    recording_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> RedirectResponse:
    """Get download URL for an audio recording"""

    # Get the recording
    recording = db.query(AudioRecording).filter(AudioRecording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    # Generate a presigned download URL from storage
    storage_client = get_storage_client()

    try:
        # Extract bucket and object name from the URI
        # URI format: http://localhost:9000/bucket/object/path
        uri_parts = recording.uri.replace("http://localhost:9000/", "").split("/", 1)
        if len(uri_parts) != 2:
            raise HTTPException(status_code=500, detail="Invalid recording URI format")

        bucket, object_name = uri_parts

        # Generate presigned download URL (valid for 1 hour)
        download_url = await storage_client.get_download_url(
            bucket=bucket, object_name=object_name, expires_in=3600
        )

        # Redirect to the presigned URL
        return RedirectResponse(url=download_url)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate download URL: {e!s}"
        ) from e


@api_router.get("/recordings/{recording_id}")
async def get_recording_metadata(
    recording_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> AudioRecordingResponse:
    """Get metadata for an audio recording"""

    recording = db.query(AudioRecording).filter(AudioRecording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    return AudioRecordingResponse(
        recording_id=str(recording.id),
        interview_id=str(recording.interview_id),
        uri=recording.uri,
        duration_ms=recording.duration_ms,
        mime_type=recording.mime_type,
        sample_rate_hz=recording.sample_rate_hz,
        file_size_bytes=recording.file_size_bytes,
        created_at=recording.created_at,
    )


@api_router.post("/interviews/{interview_id}/transcript:finalize", status_code=201)
async def finalize_transcript(
    interview_id: int,
    request: TranscriptFinalizeRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TranscriptResponse:
    """Finalize transcript for an interview"""

    # Validate segments not empty
    if not request.segments:
        raise HTTPException(status_code=400, detail="Request must contain at least one segment")

    # Find interview
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Check if transcript already exists
    existing_transcript = (
        db.query(Transcript).filter(Transcript.interview_id == interview_id).first()
    )
    if existing_transcript:
        raise HTTPException(status_code=400, detail="Transcript already exists for this interview")

    # Concatenate full text from segments
    full_text = " ".join(segment.text for segment in request.segments)

    # Create transcript
    transcript = Transcript(
        interview_id=interview_id,
        language=request.lang,
        source=request.source,
        full_text=full_text,
    )
    db.add(transcript)
    db.flush()  # Get transcript.id

    # Create segments
    for idx, segment_data in enumerate(request.segments):
        segment = TranscriptSegment(
            transcript_id=transcript.id,
            start_ms=segment_data.start_ms,
            end_ms=segment_data.end_ms,
            text=segment_data.text,
            sequence=idx,
        )
        db.add(segment)

    db.commit()
    db.refresh(transcript)

    return TranscriptResponse(
        transcript_id=str(transcript.id),
        interview_id=str(transcript.interview_id),
        language=transcript.language,
        full_text=transcript.full_text,
        created_at=transcript.created_at,
    )


# Test-only endpoints (only available in test/development environments)
if os.getenv("APP_ENV") in ("test", "local", "development"):

    @api_router.post("/test/orgs/{org_id}/users", status_code=201)
    async def create_test_user(
        org_id: int,
        user_data: dict,
        db: Annotated[Session, Depends(get_db)],
    ) -> dict:
        """
        Test-only endpoint to seed users in an organization.
        Only available in test/dev environments.
        """
        from ..models import User

        # Verify organization exists and is not deleted
        org = (
            db.query(Organization)
            .filter(Organization.id == org_id, Organization.deleted_at.is_(None))
            .first()
        )
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Create user
        user = User(
            firebase_uid=user_data["firebase_uid"],
            email=user_data["email"],
            role=user_data["role"],
            organization_id=org_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
        }


# Include the API router with /api prefix
app.include_router(api_router)


# Scalar API documentation endpoint
@app.get("/api/scalar", include_in_schema=False)
async def scalar_html() -> HTMLResponse:
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Verity API Documentation",
    )
