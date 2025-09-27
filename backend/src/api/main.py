from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from ..auth import AuthUser, require_super_admin
from ..database import get_db
from ..models import Organization
from ..schemas import HealthResponse, OrganizationCreate, OrganizationResponse

app = FastAPI(
    title="Verity API",
    version="0.1.0",
    description="UXR Platform Backend",
)


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
