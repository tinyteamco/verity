"""
Test helpers for Firebase Auth and other testing utilities
"""

import os

import requests

# Use Firebase stub port if running via test-ci, otherwise default to emulator port
FIREBASE_EMULATOR_HOST = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")
PROJECT_ID = "verity-local"


def sign_in_user(email: str, password: str) -> str:
    """Sign in a user and return their ID token"""
    url = f"http://{FIREBASE_EMULATOR_HOST}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-api-key"

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
