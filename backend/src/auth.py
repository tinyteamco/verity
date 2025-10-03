import os
from typing import Annotated, Any

import firebase_admin
import jwt as pyjwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Firebase Auth Stub secret (used when APP_ENV=test)
FIREBASE_STUB_SECRET = "firebase-auth-stub-secret-key"

# Initialize Firebase Admin for local/production
if not firebase_admin._apps:
    if os.getenv("APP_ENV") in ("local", "development") or os.getenv("FIREBASE_EMULATOR_HOST"):
        # Local development: use emulator with explicit project ID and no credentials
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"
        # Use None credentials to avoid default credential interference
        firebase_admin.initialize_app(credential=None, options={"projectId": "verity-local"})
    else:
        # Production: use default credentials (gcloud project)
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)

security = HTTPBearer(auto_error=False)


class AuthUser(BaseModel):
    firebase_uid: str
    tenant_type: str
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
    """Verify Firebase ID token using emulator, stub, or production"""
    # In test mode with Firebase Auth Stub, verify using shared secret
    if os.getenv("APP_ENV") == "test" and os.getenv("USE_FIREBASE_STUB") == "true":
        try:
            # Skip audience verification to match Firebase stub behavior
            decoded = pyjwt.decode(
                token, FIREBASE_STUB_SECRET, algorithms=["HS256"], options={"verify_aud": False}
            )
            return decoded
        except pyjwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid stub token: {e!s}") from e

    # Otherwise use Firebase Admin SDK (handles emulator vs production)
    try:
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
    tenant_type = token_data.get("tenant")
    if not tenant_type:
        raise HTTPException(status_code=401, detail="Invalid tenant")

    # Check if user is super admin from custom claims
    is_super_admin = token_data.get("role") == "super_admin"

    return AuthUser(
        firebase_uid=token_data["uid"],
        tenant_type=tenant_type,
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
    if user.tenant_type != "organization":
        raise HTTPException(status_code=403, detail="Organization user access required")
    return user


def require_interviewee_user(user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUser:
    """Dependency that requires interviewee tenant user"""
    if user.tenant_type != "interviewee":
        raise HTTPException(status_code=403, detail="Interviewee user access required")
    return user


def get_org_user_impl(user: AuthUser, db: Session) -> OrgUser:
    """Get organization user with full context from database

    Super admins have god-mode access:
    - They can access any organization without a User record
    - Organization context is derived from the resource being accessed
    - They appear as invisible members (not in user lists)
    """
    # Import here to avoid circular import
    from .models import Organization, User

    # Super admin god-mode: derive org from request context if available
    if user.is_super_admin:
        # Try to find any organization (for listing endpoints)
        # Individual endpoints will validate against specific resources
        first_org = db.query(Organization).first()
        if first_org:
            return OrgUser(
                firebase_uid=user.firebase_uid,
                email=user.email or "superadmin@platform.com",
                role="super_admin",
                organization_id=first_org.id,
                organization_name=first_org.name,
                organization_created_at=first_org.created_at,
            )
        # No orgs exist yet, but super admin can still proceed
        raise HTTPException(status_code=404, detail="No organizations exist")

    # Regular users: look up user in database
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
