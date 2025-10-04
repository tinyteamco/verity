"""
Step definitions for organization user management tests (super admin)
"""

import contextlib

import pytest
from fastapi.testclient import TestClient
from firebase_admin import auth
from pytest_bdd import given, parsers, scenarios, then, when
from src.models import Organization, User

scenarios("../features/organization_users.feature")


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


# Common step definitions


@given("a signed-in super admin user")
def create_super_admin_user(client: TestClient, auth_headers, super_admin_token):
    """Use the pre-seeded super admin user"""
    auth_headers["Authorization"] = f"Bearer {super_admin_token}"


@given('a signed-in organization user with role "admin"')
def create_admin_user(client: TestClient, auth_headers, test_org_id):
    """Create an admin organization user"""
    from tests.conftest import TestingSessionLocal
    from tests.test_helpers import sign_in_user

    uid = "test-admin-user"
    email = "admin@example.com"

    try:
        # Create organization if not exists
        if not test_org_id.get("org_id"):
            db_session = TestingSessionLocal()
            try:
                org = Organization(
                    name="LTest Organization",
                    display_name="Test Organization",
                    description="Test organization",
                )
                db_session.add(org)
                db_session.commit()
                db_session.refresh(org)
                test_org_id["org_id"] = org.id
            finally:
                db_session.close()

        auth.create_user(
            uid=uid,
            email=email,
            password="testpass123",
            email_verified=True,
        )
        auth.set_custom_user_claims(uid, {"tenant": "organization", "role": "admin"})

        token = sign_in_user(email, "testpass123")
        auth_headers["Authorization"] = f"Bearer {token}"

        # Create user in database
        db_session = TestingSessionLocal()
        try:
            db_user = User(
                firebase_uid=uid,
                email=email,
                role="admin",
                organization_id=test_org_id["org_id"],
            )
            db_session.add(db_user)
            db_session.commit()
        finally:
            db_session.close()

        yield
    finally:
        with contextlib.suppress(Exception):
            auth.delete_user(uid)


@given('a signed-in organization user with role "member"')
def create_member_user(client: TestClient, auth_headers, test_org_id):
    """Create a member organization user"""
    from tests.conftest import TestingSessionLocal
    from tests.test_helpers import sign_in_user

    uid = "test-member-user"
    email = "member@example.com"

    try:
        # Create organization if not exists
        if not test_org_id.get("org_id"):
            db_session = TestingSessionLocal()
            try:
                org = Organization(
                    name="LTest Organization",
                    display_name="Test Organization",
                    description="Test organization",
                )
                db_session.add(org)
                db_session.commit()
                db_session.refresh(org)
                test_org_id["org_id"] = org.id
            finally:
                db_session.close()

        auth.create_user(
            uid=uid,
            email=email,
            password="testpass123",
            email_verified=True,
        )
        auth.set_custom_user_claims(uid, {"tenant": "organization", "role": "member"})

        token = sign_in_user(email, "testpass123")
        auth_headers["Authorization"] = f"Bearer {token}"

        # Create user in database
        db_session = TestingSessionLocal()
        try:
            db_user = User(
                firebase_uid=uid,
                email=email,
                role="member",
                organization_id=test_org_id["org_id"],
            )
            db_session.add(db_user)
            db_session.commit()
        finally:
            db_session.close()

        yield
    finally:
        with contextlib.suppress(Exception):
            auth.delete_user(uid)


@given("an unauthenticated user")
def unauthenticated_user(auth_headers):
    """Clear auth headers for unauthenticated requests"""
    auth_headers.clear()


@given("an organization exists with multiple users")
def create_org_with_users(test_org_id):
    """Create an organization with multiple users"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        # Create organization
        org = Organization(
            name="LMulti-User Org", display_name="Multi-User Org", description="Test organization"
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        test_org_id["org_id"] = org.id

        # Create multiple users with different roles
        users_data = [
            ("owner-multi@example.com", "owner"),
            ("admin-multi@example.com", "admin"),
            ("member-multi@example.com", "member"),
        ]

        for email, role in users_data:
            # Create Firebase user
            uid = f"test-{role}-multi"
            try:
                auth.create_user(
                    uid=uid,
                    email=email,
                    password="testpass123",
                    email_verified=True,
                )
                auth.set_custom_user_claims(uid, {"tenant": "organization", "role": role})
            except Exception:
                # User might already exist, continue
                pass

            # Create user in database
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

    yield

    # Cleanup
    for _email, role in users_data:
        with contextlib.suppress(Exception):
            auth.delete_user(f"test-{role}-multi")


@given("an organization exists with an owner")
def create_org_with_owner(test_org_id):
    """Create an organization with an owner"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        # Create organization
        org = Organization(
            name="LOwner Test Org", display_name="Owner Test Org", description="Test organization"
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        test_org_id["org_id"] = org.id

        # Create owner user
        uid = "test-owner-only"
        email = "owner@example.com"

        try:
            auth.create_user(
                uid=uid,
                email=email,
                password="testpass123",
                email_verified=True,
            )
            auth.set_custom_user_claims(uid, {"tenant": "organization", "role": "owner"})
        except Exception:
            pass

        db_user = User(
            firebase_uid=uid,
            email=email,
            role="owner",
            organization_id=org.id,
        )
        db_session.add(db_user)
        db_session.commit()
    finally:
        db_session.close()

    yield

    with contextlib.suppress(Exception):
        auth.delete_user("test-owner-only")


@when(parsers.parse("they GET /orgs/{org_id}/users"))
def get_org_users_by_id(client: TestClient, auth_headers, test_response, test_org_id, org_id: str):
    """Make GET request to /orgs/{org_id}/users

    If org_id is a placeholder like {org_id}, use the actual org_id from test_org_id.
    Otherwise use the literal value from the scenario (e.g., 99999).
    """
    # Check if org_id is a literal number or a placeholder
    actual_org_id = org_id if org_id and org_id.isdigit() else test_org_id.get("org_id", 1)

    response = client.get(f"/orgs/{actual_org_id}/users", headers=auth_headers)
    test_response["response"] = response


@then("the response contains a list of users")
def verify_users_list(test_response):
    """Verify response contains a list of users"""
    response = test_response["response"]
    data = response.json()
    assert "items" in data, "Response should contain 'items' field"
    assert isinstance(data["items"], list), "'items' should be a list"
    assert len(data["items"]) > 0, "Should have at least one user"


@then("each user has email, role, and created_at fields")
def verify_user_fields(test_response):
    """Verify each user has required fields"""
    response = test_response["response"]
    data = response.json()
    for user in data["items"]:
        assert "email" in user, "User should have email field"
        assert "role" in user, "User should have role field"
        assert "created_at" in user, "User should have created_at field"


@then("the response includes the owner user")
def verify_owner_in_list(test_response):
    """Verify owner is included in the users list"""
    response = test_response["response"]
    data = response.json()
    users = data["items"]
    owner_users = [u for u in users if u["role"] == "owner"]
    assert len(owner_users) > 0, "Should have at least one owner user"


@then("the response status is 200")
def check_200_status(test_response):
    """Check response has 200 status"""
    assert test_response["response"].status_code == 200


@then("the response status is 401")
def check_401_status(test_response):
    """Check response has 401 status"""
    assert test_response["response"].status_code == 401


@then("the response status is 403")
def check_403_status(test_response):
    """Check response has 403 status"""
    assert test_response["response"].status_code == 403


@then("the response status is 404")
def check_404_status(test_response):
    """Check response has 404 status"""
    assert test_response["response"].status_code == 404


# New step definitions for user creation


@pytest.fixture
def test_user_data():
    """Store user data for cleanup"""
    return {"firebase_uids": [], "email": None, "role": None}


@given("an organization exists")
def create_organization(client, test_org_id):
    """Create a simple organization without users"""
    import uuid

    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        # Use unique name to avoid conflicts across tests
        unique_id = uuid.uuid4().hex[:8]
        org = Organization(
            name=f"test-organization-{unique_id}",
            display_name=f"Test Organization {unique_id}",
            description="Test organization for user tests",
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        test_org_id["org_id"] = org.id
    finally:
        db_session.close()


@when(
    parsers.parse('they POST /orgs/{{org_id}}/users with email "{email}" and role "{role}"'),
    converters={"email": str, "role": str},
)
def post_create_user(
    client: TestClient, auth_headers, test_response, test_org_id, test_user_data, email, role
):
    """Make POST request to create a new user"""
    actual_org_id = test_org_id.get("org_id", 1)
    test_user_data["email"] = email
    test_user_data["role"] = role

    response = client.post(
        f"/orgs/{actual_org_id}/users",
        json={"email": email, "role": role},
        headers=auth_headers,
    )
    test_response["response"] = response

    # Store firebase_uid for cleanup if user was created
    if response.status_code == 201:
        data = response.json()
        test_user_data["firebase_uids"].append(data.get("user_id"))


@when('they POST /orgs/{org_id}/users with the owner\'s email and role "admin"')
def post_create_duplicate_user(
    client: TestClient, auth_headers, test_response, test_org_id, test_user_data
):
    """Try to create a user with the same email as the owner"""
    from tests.conftest import TestingSessionLocal

    # Get the owner's email from the database
    db_session = TestingSessionLocal()
    try:
        org_id = test_org_id.get("org_id")
        owner = (
            db_session.query(User)
            .filter(User.organization_id == org_id, User.role == "owner")
            .first()
        )
        owner_email = owner.email if owner else "owner@example.com"
    finally:
        db_session.close()

    test_user_data["email"] = owner_email
    test_user_data["role"] = "admin"

    response = client.post(
        f"/orgs/{org_id}/users",
        json={"email": owner_email, "role": "admin"},
        headers=auth_headers,
    )
    test_response["response"] = response


@then("the response status is 201")
def check_201_status(test_response):
    """Check response has 201 status"""
    assert test_response["response"].status_code == 201


@then("the response status is 400")
def check_400_status(test_response):
    """Check response has 400 status"""
    assert test_response["response"].status_code == 400


@then("the response contains user_id, email, role, and password_reset_link")
def verify_user_creation_response(test_response):
    """Verify response contains all required fields for user creation"""
    response = test_response["response"]
    data = response.json()
    assert "user_id" in data, "Response should contain user_id"
    assert "email" in data, "Response should contain email"
    assert "role" in data, "Response should contain role"
    assert "password_reset_link" in data, "Response should contain password_reset_link"


@then(parsers.parse('the user email is "{email}"'))
def verify_user_email(test_response, email):
    """Verify the user email in the response"""
    response = test_response["response"]
    data = response.json()
    assert data["email"] == email


@then(parsers.parse('the user role is "{role}"'))
def verify_user_role(test_response, role):
    """Verify the user role in the response"""
    response = test_response["response"]
    data = response.json()
    assert data["role"] == role


@then(parsers.parse('a Firebase user was created with email "{email}"'))
def verify_firebase_user_created(test_user_data, email):
    """Verify Firebase user was created"""
    try:
        firebase_user = auth.get_user_by_email(email)
        assert firebase_user is not None
        assert firebase_user.email == email
        # Store UID for cleanup
        if firebase_user.uid not in test_user_data["firebase_uids"]:
            test_user_data["firebase_uids"].append(firebase_user.uid)
    except Exception as e:
        pytest.fail(f"Firebase user not found: {e}")


@then(parsers.parse('a database user exists with email "{email}" and role "{role}"'))
def verify_database_user_exists(test_org_id, email, role):
    """Verify user exists in database with correct role"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        user = db_session.query(User).filter(User.email == email).first()
        assert user is not None, f"User with email {email} not found in database"
        assert user.role == role, f"Expected role {role}, got {user.role}"
        assert user.organization_id == test_org_id.get("org_id")
    finally:
        db_session.close()


@then(parsers.parse('the error message contains "{text}"'))
def verify_error_message(test_response, text):
    """Verify error message contains specific text"""
    response = test_response["response"]
    data = response.json()
    error_msg = data.get("detail", "").lower()
    assert text.lower() in error_msg, f"Expected '{text}' in error message, got: {error_msg}"


# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_test_users(test_user_data):
    """Clean up Firebase users created during tests"""
    yield
    # Cleanup after test
    for uid in test_user_data.get("firebase_uids", []):
        with contextlib.suppress(Exception):
            auth.delete_user(uid)
