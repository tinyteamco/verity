"""
Test helpers for Firebase Auth and other testing utilities
"""

import os

import requests

PROJECT_ID = "verity-local"


def _get_firebase_host() -> str:
    """Get Firebase emulator host (read at runtime to pick up pytest fixture changes)."""
    return os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")


def sign_in_user(email: str, password: str) -> str:
    """Sign in a user and return their ID token"""
    url = f"http://{_get_firebase_host()}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-api-key"

    data = {"email": email, "password": password, "returnSecureToken": True}

    response = requests.post(url, json=data)

    if response.status_code == 200:
        result = response.json()
        return result["idToken"]
    else:
        raise Exception(f"Failed to sign in {email}: {response.text}")


def get_super_admin_token() -> str:
    """Get ID token for super admin user"""
    return sign_in_user("admin@tinyteam.co", "superadmin123")


def get_org_user_token() -> str:
    """Get ID token for regular organization user"""
    return sign_in_user("user@acme.com", "user123")


def get_interviewee_token() -> str:
    """Get ID token for interviewee user"""
    return sign_in_user("interviewee@example.com", "interviewee123")


def get_auth_headers(token: str) -> dict:
    """Get authorization headers for API requests"""
    return {"Authorization": f"Bearer {token}"}
