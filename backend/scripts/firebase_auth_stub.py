#!/usr/bin/env python3
"""
Lightweight Firebase Auth emulator stub for E2E testing.

This replaces the full Firebase emulator (12-15s startup) with a minimal
implementation (<1s startup) that provides only the endpoints actually used
by the backend and tests.

Endpoints implemented:
- POST /identitytoolkit.googleapis.com/v1/projects/{project}/accounts
  Create user (Admin SDK)
- POST /identitytoolkit.googleapis.com/v1/accounts:signInWithPassword
  Sign in
- GET /robot/v1/metadata/x509/securetoken@system.gserviceaccount.com
  Public keys (JWT verification)

Runs on port 9099 (drop-in replacement for Firebase emulator).
"""

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="Firebase Auth Stub")

# Add CORS middleware to handle preflight requests from browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory user store
# Format: {uid: {email, password, emailVerified, customClaims}}
users: dict[str, dict[str, Any]] = {}

# Test JWT secret (known by both stub and backend in test mode)
JWT_SECRET = "firebase-auth-stub-secret-key"
JWT_ALGORITHM = "HS256"

# RSA key pair for JWT signing (simplified - using symmetric for speed)
# In real Firebase, this would be RSA public/private key pair


def generate_uid() -> str:
    """Generate a Firebase-style UID"""
    return str(uuid.uuid4()).replace("-", "")[:28]


def create_id_token(user: dict[str, Any]) -> str:
    """Create a Firebase-compatible ID token (JWT)"""
    now = datetime.now(UTC)
    payload = {
        "iss": "https://securetoken.google.com/verity-local",
        "aud": "verity-local",
        "auth_time": int(now.timestamp()),
        "user_id": user["uid"],
        "sub": user["uid"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "email": user["email"],
        "email_verified": user.get("emailVerified", False),
        "firebase": {"identities": {"email": [user["email"]]}, "sign_in_provider": "password"},
        "uid": user["uid"],
    }

    # Add custom claims to token payload
    if user.get("customClaims"):
        payload.update(user["customClaims"])

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@app.get("/")
def root() -> dict[str, str]:
    """Health check"""
    return {"status": "Firebase Auth Stub running", "version": "1.0.0"}


async def _create_user_impl(body: dict[str, Any]) -> JSONResponse:
    """
    Implementation for user creation (shared by both endpoints)
    """
    uid = body.get("localId", generate_uid())
    email = body.get("email")
    password = body.get("password", "default-password")
    email_verified = body.get("emailVerified", False)
    return_secure_token = body.get("returnSecureToken", False)

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    # Check if user already exists
    existing = next((u for u in users.values() if u["email"] == email), None)
    if existing:
        raise HTTPException(status_code=400, detail=f"User with email {email} already exists")

    # Create user
    users[uid] = {
        "uid": uid,
        "email": email,
        "password": password,
        "emailVerified": email_verified,
        "customClaims": {},
    }

    response_data = {
        "kind": "identitytoolkit#SignupNewUserResponse",
        "localId": uid,
        "email": email,
        "emailVerified": email_verified,
    }

    # If returnSecureToken is requested, include ID token (for client SDK signup)
    if return_secure_token:
        id_token = create_id_token(users[uid])
        response_data.update(
            {
                "idToken": id_token,
                "refreshToken": f"refresh-{uid}",
                "expiresIn": "3600",
            }
        )

    return JSONResponse(response_data)


@app.post("/identitytoolkit.googleapis.com/v1/projects/{project}/accounts")
async def create_user_with_project(project: str, request: Request) -> JSONResponse:
    """
    Create user endpoint (used by Firebase Admin SDK)

    Request body:
    {
        "localId": "optional-uid",
        "email": "user@example.com",
        "password": "password123",
        "emailVerified": true
    }
    """
    body = await request.json()
    return await _create_user_impl(body)


@app.post("/identitytoolkit.googleapis.com/v1/accounts")
async def create_user_no_project(request: Request) -> JSONResponse:
    """
    Create user endpoint without project (used by Firebase Client SDK signup)

    Request body:
    {
        "email": "user@example.com",
        "password": "password123",
        "returnSecureToken": true
    }
    """
    body = await request.json()
    return await _create_user_impl(body)


@app.post("/identitytoolkit.googleapis.com/v1/projects/{project}/accounts:update")
async def update_user(project: str, request: Request) -> JSONResponse:
    """
    Update user endpoint (used by Firebase Admin SDK for setting custom claims)

    Request body:
    {
        "localId": "user-uid",
        "customAttributes": "{\"role\":\"admin\",\"tenant\":\"organization\"}"
    }
    """
    body = await request.json()

    uid = body.get("localId")
    if not uid or uid not in users:
        raise HTTPException(status_code=404, detail="User not found")

    # Parse and set custom claims
    if "customAttributes" in body:
        custom_attrs = body["customAttributes"]
        if isinstance(custom_attrs, str):
            custom_attrs = json.loads(custom_attrs)
        users[uid]["customClaims"] = custom_attrs

    return JSONResponse(
        {
            "kind": "identitytoolkit#SetAccountInfoResponse",
            "localId": uid,
            "email": users[uid]["email"],
        }
    )


@app.get("/identitytoolkit.googleapis.com/v1/projects/{project}/accounts:lookup")
@app.post("/identitytoolkit.googleapis.com/v1/accounts:lookup")
@app.post("/identitytoolkit.googleapis.com/v1/projects/{project}/accounts:lookup")
async def get_user(request: Request, project: str | None = None) -> JSONResponse:
    """
    Get user by email, ID token, or localId endpoint (used by Firebase SDK)

    Query params (GET):
    - email: user email

    POST body:
    - idToken: Firebase ID token to lookup user (string)
    - localId: User ID(s) to lookup (string or array)
    """
    if request.method == "GET":
        params = dict(request.query_params)
        email = params.get("email")

        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        user = next((u for u in users.values() if u["email"] == email), None)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    else:  # POST
        body = await request.json()

        # Handle email lookup (used by Admin SDK get_user_by_email)
        if "email" in body:
            emails = body["email"]
            if not isinstance(emails, list):
                emails = [emails]

            # Return all requested users
            found_users = []
            for email in emails:
                user = next((u for u in users.values() if u["email"] == email), None)
                if user:
                    found_users.append(user)

            return JSONResponse(
                {
                    "kind": "identitytoolkit#GetAccountInfoResponse",
                    "users": [
                        {
                            "localId": u["uid"],
                            "email": u["email"],
                            "emailVerified": u.get("emailVerified", False),
                            "customAttributes": json.dumps(u.get("customClaims", {})),
                        }
                        for u in found_users
                    ],
                }
            )

        # Handle localId lookup (used by Admin SDK get_user)
        if "localId" in body:
            local_ids = body["localId"]
            if not isinstance(local_ids, list):
                local_ids = [local_ids]

            # Return all requested users
            found_users = []
            for uid in local_ids:
                if uid in users:
                    found_users.append(users[uid])

            return JSONResponse(
                {
                    "kind": "identitytoolkit#GetAccountInfoResponse",
                    "users": [
                        {
                            "localId": u["uid"],
                            "email": u["email"],
                            "emailVerified": u.get("emailVerified", False),
                            "customAttributes": json.dumps(u.get("customClaims", {})),
                        }
                        for u in found_users
                    ],
                }
            )

        # Handle idToken lookup
        id_token = body.get("idToken")
        if not id_token:
            raise HTTPException(status_code=400, detail="idToken, localId, or email is required")

        # Decode token to get user ID
        try:
            decoded = jwt.decode(
                id_token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_aud": False}
            )
            uid = decoded.get("uid") or decoded.get("user_id")

            if not uid or uid not in users:
                raise HTTPException(status_code=404, detail="User not found")

            user = users[uid]
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=400, detail="Invalid token") from e

    return JSONResponse(
        {
            "kind": "identitytoolkit#GetAccountInfoResponse",
            "users": [
                {
                    "localId": user["uid"],
                    "email": user["email"],
                    "emailVerified": user.get("emailVerified", False),
                    "customAttributes": json.dumps(user.get("customClaims", {})),
                }
            ],
        }
    )


@app.post("/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword")
async def sign_in(request: Request) -> JSONResponse:
    """
    Sign in with email/password endpoint (used by test helpers)

    Request body:
    {
        "email": "user@example.com",
        "password": "password123",
        "returnSecureToken": true
    }
    """
    body = await request.json()

    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    # Find user
    user = next((u for u in users.values() if u["email"] == email), None)
    if not user:
        raise HTTPException(status_code=400, detail="EMAIL_NOT_FOUND")

    # Check password
    if user["password"] != password:
        raise HTTPException(status_code=400, detail="INVALID_PASSWORD")

    # Generate ID token
    id_token = create_id_token(user)

    return JSONResponse(
        {
            "kind": "identitytoolkit#VerifyPasswordResponse",
            "localId": user["uid"],
            "email": user["email"],
            "displayName": "",
            "idToken": id_token,
            "registered": True,
            "refreshToken": f"refresh-{user['uid']}",
            "expiresIn": "3600",
        }
    )


@app.delete("/identitytoolkit.googleapis.com/v1/projects/{project}/accounts:delete")
@app.post("/identitytoolkit.googleapis.com/v1/projects/{project}/accounts:delete")
async def delete_user(project: str, request: Request) -> JSONResponse:
    """
    Delete user endpoint (used by test cleanup)

    Request body:
    {
        "localId": "user-uid"
    }
    """
    body = await request.json()
    uid = body.get("localId")

    if uid and uid in users:
        del users[uid]

    return JSONResponse({"kind": "identitytoolkit#DeleteAccountResponse"})


@app.post("/identitytoolkit.googleapis.com/v1/projects/{project}/accounts:sendOobCode")
async def generate_password_reset_link(project: str, request: Request) -> JSONResponse:
    """
    Generate password reset link (used by Firebase Admin SDK)

    Request body:
    {
        "email": "user@example.com",
        "requestType": "PASSWORD_RESET"
    }
    """
    body = await request.json()
    email = body.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    # Check if user exists
    user = next((u for u in users.values() if u["email"] == email), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate a mock OOB code (out-of-band code for password reset)
    oob_code = f"mock-oob-code-{uuid.uuid4().hex[:16]}"

    # Return Firebase-style response with a mock password reset link
    return JSONResponse(
        {
            "kind": "identitytoolkit#GetOobConfirmationCodeResponse",
            "email": email,
            "oobCode": oob_code,
            "oobLink": f"http://localhost:5173/auth/action?mode=resetPassword&oobCode={oob_code}",
        }
    )


@app.get("/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com")
def get_public_keys() -> dict[str, str]:
    """
    Public keys endpoint for JWT verification (used by Firebase Admin SDK)

    In real Firebase, this returns RSA public keys. We're using symmetric
    signing for simplicity, so we return a mock response.
    """
    # Return a mock key ID - the actual verification happens via shared secret
    return {"firebase-auth-stub-key": "MOCK_PUBLIC_KEY"}


@app.get("/.well-known/openid-configuration")
def openid_configuration() -> dict[str, Any]:
    """OpenID configuration endpoint"""
    return {
        "issuer": "https://securetoken.google.com/verity-local",
        "jwks_uri": "http://localhost:9099/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com",
        "response_types_supported": ["id_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
    }


@app.post("/emulator/v1/projects/{project}/accounts:delete")
async def emulator_clear_accounts(project: str) -> JSONResponse:
    """Clear all accounts (emulator-only endpoint for test isolation)"""
    users.clear()
    return JSONResponse({"status": "ok"})


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(request: Request, path: str) -> JSONResponse:
    """Catch-all handler to log unimplemented endpoints"""
    print(f"⚠️  Unimplemented endpoint: {request.method} /{path}")
    print(f"   Query params: {dict(request.query_params)}")
    body = None
    try:
        body = await request.json()
        print(f"   Body: {json.dumps(body, indent=2)}")
    except Exception:
        pass

    raise HTTPException(
        status_code=501, detail=f"Endpoint not implemented: {request.method} /{path}"
    )


if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.getenv("STUB_PORT", "9099"))

    print(f"🔥 Starting Firebase Auth Stub on http://localhost:{port}")
    print("   This is a lightweight replacement for the Firebase emulator")
    print("   Startup time: <1 second (vs 12-15s for full emulator)")
    print()

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
