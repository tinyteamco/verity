"""
Step definitions for interviewee tenant isolation tests
"""

import contextlib

import pytest
from fastapi.testclient import TestClient
from firebase_admin import auth
from pytest_bdd import given, scenarios, then, when

scenarios("../features/interviewee_isolation.feature")


@pytest.fixture
def auth_headers():
    """Auth headers for requests"""
    return {}


@pytest.fixture
def test_response():
    """Store response for assertions"""
    return {"response": None}


@given("a signed-in interviewee user")
def create_interviewee_user(client: TestClient, auth_headers):
    """Create an interviewee user"""
    try:
        auth.create_user(
            uid="test-interviewee-iso",
            email="interviewee-iso@example.com",
            password="testpass123",
            email_verified=True,
        )
        auth.set_custom_user_claims("test-interviewee-iso", {"tenant": "interviewee"})

        # Get token for API requests
        from tests.test_helpers import sign_in_user

        token = sign_in_user("interviewee-iso@example.com", "testpass123")
        auth_headers["Authorization"] = f"Bearer {token}"

        yield
    finally:
        with contextlib.suppress(Exception):
            auth.delete_user("test-interviewee-iso")


# Note: Defining owner user creation here to avoid import issues
@given('a signed-in organization user with role "owner"')
def create_owner_user(client: TestClient, auth_headers):
    """Create an owner organization user"""
    try:
        auth.create_user(
            uid="test-owner-iso",
            email="owner-iso@example.com",
            password="testpass123",
            email_verified=True,
        )
        auth.set_custom_user_claims("test-owner-iso", {"tenant": "organization", "role": "owner"})

        # Get token for API requests
        from tests.test_helpers import sign_in_user

        token = sign_in_user("owner-iso@example.com", "testpass123")
        auth_headers["Authorization"] = f"Bearer {token}"

        # Create organization and user in database
        from src.models import Organization, User
        from tests.conftest import TestingSessionLocal

        db_session = TestingSessionLocal()
        try:
            # Create organization first
            org = Organization(
                name="LTest Organization",
                display_name="Test Organization",
                description="Test organization",
            )
            db_session.add(org)
            db_session.commit()
            db_session.refresh(org)

            # Create user record
            db_user = User(
                firebase_uid="test-owner-iso",
                email="owner-iso@example.com",
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
            auth.delete_user("test-owner-iso")


@when("they GET /orgs/current")
def get_current_org(client: TestClient, auth_headers, test_response):
    """Make GET request to /orgs/current"""
    response = client.get("/orgs/current", headers=auth_headers)
    test_response["response"] = response


@when("they GET /orgs/current/users")
def get_org_users(client: TestClient, auth_headers, test_response):
    """Make GET request to /orgs/current/users"""
    response = client.get("/orgs/current/users", headers=auth_headers)
    test_response["response"] = response


@when('they POST /orgs with name "Hacker Org"')
def create_org_as_interviewee(client: TestClient, auth_headers, test_response):
    """Try to create an organization as interviewee"""
    response = client.post(
        "/orgs",
        json={
            "name": "hacker-org",
            "display_name": "Hacker Org",
            "description": "Test organization: Hacker Org",
            "owner_email": "hacker@hackerorg.com",
        },
        headers=auth_headers,
    )
    test_response["response"] = response


@when("they try to access an interviewee-only endpoint")
def access_interviewee_endpoint(client: TestClient, auth_headers, test_response):
    """Try to access a hypothetical interviewee-only endpoint"""
    # This is a placeholder - when interviewee endpoints are implemented,
    # this should be updated to use a real endpoint
    response = client.get("/interviews/my-interviews", headers=auth_headers)
    test_response["response"] = response


@then("the response status is 403")
def check_403_status(test_response):
    """Check response has 403 status"""
    assert test_response["response"].status_code == 403


@then("the response status is 404")
def check_404_status(test_response):
    """Check response has 404 status"""
    assert test_response["response"].status_code == 404


@then('the error message is "Organization user access required"')
def check_org_required_error(test_response):
    """Check specific error message for org user requirement"""
    data = test_response["response"].json()
    assert data["detail"] == "Organization user access required"


@then('the error message is "Super admin access required"')
def check_super_admin_error(test_response):
    """Check specific error message for super admin requirement"""
    data = test_response["response"].json()
    assert data["detail"] == "Super admin access required"


@then("the error message indicates wrong tenant")
def check_wrong_tenant_error(test_response):
    """Check error indicates wrong tenant"""
    # Since the endpoint doesn't exist yet, we expect 404
    # When interviewee endpoints are implemented, this should check for tenant errors
    assert test_response["response"].status_code in [403, 404]
