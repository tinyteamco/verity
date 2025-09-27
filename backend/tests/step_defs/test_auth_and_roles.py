"""
Step definitions for authentication and role-based authorization tests
"""

import contextlib

import pytest
from fastapi.testclient import TestClient
from firebase_admin import auth
from pytest_bdd import given, scenarios, then, when
from src.models import Organization, User

scenarios("../features/auth_and_roles.feature")


@pytest.fixture
def auth_headers():
    """Auth headers for requests"""
    return {}


@pytest.fixture
def test_response():
    """Store response for assertions"""
    return {"response": None}


@given('a signed-in organization user with role "member"')
def create_member_user(client: TestClient, auth_headers):
    """Create a member organization user"""
    try:
        auth.create_user(
            uid="test-member",
            email="member@example.com",
            password="testpass123",
            email_verified=True,
        )
        auth.set_custom_user_claims("test-member", {"tenant": "organization", "role": "member"})

        # Get token for API requests
        from tests.test_helpers import sign_in_user

        token = sign_in_user("member@example.com", "testpass123")
        auth_headers["Authorization"] = f"Bearer {token}"

        # Create organization and user in database
        from tests.conftest import TestingSessionLocal

        db_session = TestingSessionLocal()
        try:
            # Create organization first
            org = Organization(name="Test Organization")
            db_session.add(org)
            db_session.commit()
            db_session.refresh(org)

            # Create user record
            db_user = User(
                firebase_uid="test-member",
                email="member@example.com",
                role="member",
                organization_id=org.id,
            )
            db_session.add(db_user)
            db_session.commit()
        finally:
            db_session.close()

        yield
    finally:
        with contextlib.suppress(Exception):
            auth.delete_user("test-member")


@given('a signed-in organization user with role "owner"')
def create_owner_user(client: TestClient, auth_headers):
    """Create an owner organization user"""
    try:
        auth.create_user(
            uid="test-owner",
            email="owner@example.com",
            password="testpass123",
            email_verified=True,
        )
        auth.set_custom_user_claims("test-owner", {"tenant": "organization", "role": "owner"})

        # Get token for API requests
        from tests.test_helpers import sign_in_user

        token = sign_in_user("owner@example.com", "testpass123")
        auth_headers["Authorization"] = f"Bearer {token}"

        # Create organization and user in database
        from tests.conftest import TestingSessionLocal

        db_session = TestingSessionLocal()
        try:
            # Create organization first
            org = Organization(name="Test Organization")
            db_session.add(org)
            db_session.commit()
            db_session.refresh(org)

            # Create user record
            db_user = User(
                firebase_uid="test-owner",
                email="owner@example.com",
                role="owner",
                organization_id=org.id,
            )
            db_session.add(db_user)
            db_session.commit()
        finally:
            db_session.close()

        yield
    finally:
        with contextlib.suppress(Exception):
            auth.delete_user("test-owner")


@when("they GET /orgs/current/users")
def request_org_users(client: TestClient, auth_headers, test_response):
    """Make GET request to /orgs/current/users"""
    response = client.get("/orgs/current/users", headers=auth_headers)
    test_response["response"] = response


@then("the response status is 403")
def check_403_status(test_response):
    """Check response has 403 status"""
    assert test_response["response"].status_code == 403


@then("the response status is 200")
def check_200_status(test_response):
    """Check response has 200 status"""
    assert test_response["response"].status_code == 200
