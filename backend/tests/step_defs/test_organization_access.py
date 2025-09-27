"""
Step definitions for organization access control tests
"""

import contextlib

import pytest
from fastapi.testclient import TestClient
from firebase_admin import auth
from pytest_bdd import given, scenarios, then, when
from src.models import Organization, User

scenarios("../features/organization_access.feature")


@pytest.fixture
def auth_headers():
    """Auth headers for requests"""
    return {}


@pytest.fixture
def test_response():
    """Store response for assertions"""
    return {"response": None}


@pytest.fixture
def test_org_id():
    """Store organization ID for assertions"""
    return {"org_id": None}


# Note: We'll need to redefine the role-based user creation functions
# to avoid circular imports and maintain test isolation


def create_org_user_with_role(uid: str, email: str, role: str, auth_headers):
    """Helper function to create organization user with specific role"""
    from tests.conftest import TestingSessionLocal
    from tests.test_helpers import sign_in_user

    auth.create_user(
        uid=uid,
        email=email,
        password="testpass123",
        email_verified=True,
    )
    auth.set_custom_user_claims(uid, {"tenant": "organization", "role": role})

    # Get token for API requests
    token = sign_in_user(email, "testpass123")
    auth_headers["Authorization"] = f"Bearer {token}"

    # Create organization and user in database
    db_session = TestingSessionLocal()
    try:
        # Create organization first
        org = Organization(name="Test Organization")
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)

        # Create user record
        db_user = User(
            firebase_uid=uid,
            email=email,
            role=role,
            organization_id=org.id,
        )
        db_session.add(db_user)
        db_session.commit()
    finally:
        db_session.close()


@given('a signed-in organization user with role "member"')
def create_member_user(client: TestClient, auth_headers):
    """Create a member organization user"""
    try:
        create_org_user_with_role(
            "test-member-access", "member-access@example.com", "member", auth_headers
        )
        yield
    finally:
        with contextlib.suppress(Exception):
            auth.delete_user("test-member-access")


@given('a signed-in organization user with role "admin"')
def create_admin_user(client: TestClient, auth_headers):
    """Create an admin organization user"""
    try:
        create_org_user_with_role(
            "test-admin-access", "admin-access@example.com", "admin", auth_headers
        )
        yield
    finally:
        with contextlib.suppress(Exception):
            auth.delete_user("test-admin-access")


@given('a signed-in organization user with role "owner"')
def create_owner_user(client: TestClient, auth_headers):
    """Create an owner organization user"""
    try:
        create_org_user_with_role(
            "test-owner-access", "owner-access@example.com", "owner", auth_headers
        )
        yield
    finally:
        with contextlib.suppress(Exception):
            auth.delete_user("test-owner-access")


@given("a signed-in interviewee user")
def create_interviewee_user(client: TestClient, auth_headers):
    """Create an interviewee user"""
    try:
        auth.create_user(
            uid="test-interviewee-access",
            email="interviewee@example.com",
            password="testpass123",
            email_verified=True,
        )
        auth.set_custom_user_claims("test-interviewee-access", {"tenant": "interviewee"})

        # Get token for API requests
        from tests.test_helpers import sign_in_user

        token = sign_in_user("interviewee@example.com", "testpass123")
        auth_headers["Authorization"] = f"Bearer {token}"

        yield
    finally:
        with contextlib.suppress(Exception):
            auth.delete_user("test-interviewee-access")


@given("an unauthenticated user")
def unauthenticated_user(auth_headers):
    """Clear auth headers for unauthenticated requests"""
    auth_headers.clear()


@given("a signed-in super admin user")
def create_super_admin_user(client: TestClient, auth_headers, super_admin_token):
    """Use the pre-seeded super admin user"""
    auth_headers["Authorization"] = f"Bearer {super_admin_token}"


@given("a signed-in organization user not in database")
def create_org_user_not_in_db(client: TestClient, auth_headers):
    """Create an org user in Firebase but not in database"""
    try:
        auth.create_user(
            uid="test-orphan-user",
            email="orphan@example.com",
            password="testpass123",
            email_verified=True,
        )
        auth.set_custom_user_claims(
            "test-orphan-user", {"tenant": "organization", "role": "member"}
        )

        # Get token for API requests
        from tests.test_helpers import sign_in_user

        token = sign_in_user("orphan@example.com", "testpass123")
        auth_headers["Authorization"] = f"Bearer {token}"

        # Deliberately NOT creating database record

        yield
    finally:
        with contextlib.suppress(Exception):
            auth.delete_user("test-orphan-user")


@when("they GET /orgs/current")
def get_current_org(client: TestClient, auth_headers, test_response):
    """Make GET request to /orgs/current"""
    response = client.get("/orgs/current", headers=auth_headers)
    test_response["response"] = response


@then("the response status is 200")
def check_200_status(test_response):
    """Check response has 200 status"""
    assert test_response["response"].status_code == 200


@then("the response status is 403")
def check_403_status(test_response):
    """Check response has 403 status"""
    assert test_response["response"].status_code == 403


@then("the response status is 401")
def check_401_status(test_response):
    """Check response has 401 status"""
    assert test_response["response"].status_code == 401


@then("the response contains their organization details")
def check_org_details(test_response):
    """Check response contains organization details"""
    data = test_response["response"].json()
    assert "org_id" in data
    assert "name" in data
    assert data["name"] == "Test Organization"


@then('the error message is "User not associated with any organization"')
def check_no_org_error(test_response):
    """Check specific error message"""
    data = test_response["response"].json()
    assert data["detail"] == "User not associated with any organization"
