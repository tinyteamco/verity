from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from ..auth import (
    AuthUser,
    OrgUser,
    get_org_user_impl,
    require_interviewee_user,
    require_organization_user,
    require_super_admin,
)
from ..database import get_db
from ..database_utils import check_database_connectivity_with_session, ensure_database_connectivity
from ..models import Interview, InterviewGuide, Organization, Study, User
from ..schemas import (
    HealthResponse,
    InterviewCompleteRequest,
    InterviewGuideCreate,
    InterviewGuideResponse,
    InterviewLinkResponse,
    InterviewList,
    InterviewResponse,
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


# Study Guide Management Endpoints


@app.put("/studies/{study_id}/guide", response_model=InterviewGuideResponse)
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


@app.get("/studies/{study_id}/guide", response_model=InterviewGuideResponse)
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


@app.post("/studies/{study_id}/interviews", response_model=InterviewLinkResponse, status_code=201)
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


@app.get("/studies/{study_id}/interviews", response_model=InterviewList)
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


@app.get("/studies/{study_id}/interviews/{interview_id}", response_model=InterviewResponse)
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


@app.get("/interview/{access_token}")
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


@app.post("/interview/{access_token}/complete")
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


@app.post("/interview/{access_token}/claim")
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
