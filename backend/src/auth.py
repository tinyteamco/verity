import os
from typing import Annotated, Any

import firebase_admin
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Initialize Firebase Admin for local/production
if not firebase_admin._apps:
    if os.getenv("APP_ENV") == "local":
        # Local development: use emulator with explicit project ID
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"
        firebase_admin.initialize_app(options={"projectId": "verity-local"})
    else:
        # Production: use default credentials (gcloud project)
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)

security = HTTPBearer(auto_error=False)


class AuthUser(BaseModel):
    firebase_uid: str
    tenant_id: str
    email: str | None = None
    is_super_admin: bool = False


class OrgUser(BaseModel):
    firebase_uid: str
    email: str
    role: str
    organization_id: int
    organization_name: str
    organization_created_at: Any


def verify_firebase_token(token: str) -> dict[str, Any]:
    """Verify Firebase ID token using emulator or production"""
    try:
        # Use Firebase Admin SDK - it automatically handles emulator vs production
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e!s}") from e


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> AuthUser:
    """Extract and validate Firebase JWT token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    token_data = verify_firebase_token(credentials.credentials)

    # Extract tenant from custom claims (we store it there for emulator)
    tenant_id = token_data.get("tenant")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid tenant")

    # Check if user is super admin from custom claims
    is_super_admin = token_data.get("super_admin", False)

    return AuthUser(
        firebase_uid=token_data["uid"],
        tenant_id=tenant_id,
        email=token_data.get("email"),
        is_super_admin=is_super_admin,
    )


def require_super_admin(user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUser:
    """Dependency that requires super admin privileges"""
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super admin access required")
    return user


def require_organization_user(user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUser:
    """Dependency that requires organization tenant user"""
    if user.tenant_id != "organization":
        raise HTTPException(status_code=403, detail="Organization user access required")
    return user


def get_org_user_impl(user: AuthUser, db: Session) -> OrgUser:
    """Get organization user with full context from database"""
    # Import here to avoid circular import
    from .models import User

    # Look up user in database
    db_user = db.query(User).filter(User.firebase_uid == user.firebase_uid).first()

    if not db_user:
        raise HTTPException(status_code=403, detail="User not associated with any organization")

    return OrgUser(
        firebase_uid=db_user.firebase_uid,
        email=db_user.email,
        role=db_user.role,
        organization_id=db_user.organization_id,
        organization_name=db_user.organization.name,
        organization_created_at=db_user.organization.created_at,
    )
