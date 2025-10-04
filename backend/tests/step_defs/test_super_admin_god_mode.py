"""Step definitions for super admin god-mode BDD tests."""

from contextlib import suppress
from typing import Any

from firebase_admin import auth
from pytest_bdd import given, parsers, scenarios, then, when
from src.models import Interview, Organization, Study, User
from tests.conftest import TestingSessionLocal

scenarios("../features/super_admin_god_mode.feature")


# Helper functions


def get_unique_uid(prefix: str, request: Any) -> str:
    """Generate unique UID for each test."""
    test_name = request.node.name
    return f"{prefix}-{hash(test_name) % 10000}"


def get_unique_email(prefix: str, request: Any) -> str:
    """Generate unique email for each test."""
    test_name = request.node.name
    return f"{prefix}-{hash(test_name) % 10000}@example.com"


# Given steps


@given(parsers.parse('a super admin user exists with email "{email}"'))
def create_super_admin(super_admin_user: Any, request: Any, email: str) -> None:
    """Use the session-level super admin user."""
    # Store reference to session super admin
    request.super_admin_email = super_admin_user.email
    request.super_admin_uid = super_admin_user.uid


@given(parsers.parse('a regular user exists with email "{email}"'))
def create_regular_user(client: Any, request: Any, email: str) -> None:
    """Create a regular user in Firebase."""
    uid = get_unique_uid("regular-user", request)

    # Use unique email per test to avoid collisions
    unique_email = get_unique_email("regular-user", request)

    # Try to delete user first (in case it exists from previous test)
    with suppress(Exception):
        auth.delete_user(uid)

    # Create user in Firebase with unique email
    user = auth.create_user(
        uid=uid,
        email=unique_email,
        password="testpass123",
        email_verified=True,
    )

    # Set custom claims for regular user
    auth.set_custom_user_claims(user.uid, {"tenant": "organization"})

    # Store for later use (store unique email, not the scenario email)
    request.regular_user_email = unique_email
    request.regular_user_uid = user.uid


@given(parsers.parse('a second regular user exists with email "{email}"'))
def create_second_regular_user(client: Any, request: Any, email: str) -> None:
    """Create a second regular user in Firebase."""
    uid = get_unique_uid("second-user", request)

    # Use unique email per test to avoid collisions
    unique_email = get_unique_email("second-user", request)

    # Try to delete user first (in case it exists from previous test)
    with suppress(Exception):
        auth.delete_user(uid)

    # Create user in Firebase with unique email
    user = auth.create_user(
        uid=uid,
        email=unique_email,
        password="testpass123",
        email_verified=True,
    )

    # Set custom claims
    auth.set_custom_user_claims(user.uid, {"tenant": "organization"})

    # Store for later use (store unique email, not the scenario email)
    request.second_user_email = unique_email
    request.second_user_uid = user.uid


@given(parsers.parse('the super admin creates an organization named "{org_name}"'))
def super_admin_creates_org_given(client: Any, request: Any, org_name: str) -> None:
    """Super admin creates an organization (Given step)."""
    from tests.test_helpers import sign_in_user

    # Sign in as super admin
    token = sign_in_user("admin@tinyteam.co", "superadmin123")
    headers = {"Authorization": f"Bearer {token}"}

    # Generate unique owner email using test name hash to avoid collisions
    test_hash = hash(request.node.name) % 10000
    owner_email = f"owner-{test_hash}@{org_name.lower().replace(' ', '')}.com"

    # Create organization with owner
    response = client.post(
        "/orgs",
        json={
            "name": org_name.lower().replace(" ", "-"),
            "display_name": org_name,
            "description": f"Test organization: {org_name}",
            "owner_email": owner_email,
        },
        headers=headers,
    )
    assert response.status_code == 201

    # Store org_id for later use
    org_data = response.json()
    request.last_created_org_id = int(org_data["org_id"])
    request.last_created_org_name = org_name


@given(parsers.parse('the regular user is added to "{org_name}" as {role}'))
def add_regular_user_to_org(request: Any, org_name: str, role: str) -> None:
    """Add regular user to organization as a specific role."""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        # Create User record linking Firebase user to org
        user = User(
            firebase_uid=request.regular_user_uid,
            email=request.regular_user_email,
            role=role,
            organization_id=request.last_created_org_id,
        )
        db.add(user)
        db.commit()

        # Store for later use
        request.regular_user_org_id = request.last_created_org_id
        request.regular_user_org_name = org_name


@given(parsers.parse('the second user is added to "{org_name}" as {role}'))
def add_second_user_to_org(request: Any, org_name: str, role: str) -> None:
    """Add second user to organization as a specific role."""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        # Create User record linking Firebase user to org
        user = User(
            firebase_uid=request.second_user_uid,
            email=request.second_user_email,
            role=role,
            organization_id=request.last_created_org_id,
        )
        db.add(user)
        db.commit()

        # Store for later use
        request.second_user_org_id = request.last_created_org_id


@given(parsers.parse('the regular user creates a study titled "{title}" in their organization'))
def regular_user_creates_study(client: Any, request: Any, title: str) -> None:
    """Regular user creates a study in their org."""
    from tests.test_helpers import sign_in_user

    # Sign in as regular user
    token = sign_in_user(request.regular_user_email, "testpass123")
    headers = {"Authorization": f"Bearer {token}"}

    # Create study
    response = client.post("/studies", json={"title": title}, headers=headers)
    assert response.status_code == 201

    # Store study_id for later use
    study_data = response.json()
    request.regular_user_study_id = int(study_data["study_id"])


@given(parsers.parse('an interview with access_token "{access_token}" exists for the study'))
def create_interview_for_study(request: Any, access_token: str) -> None:
    """Create an interview for the regular user's study."""
    with TestingSessionLocal() as db:
        interview = Interview(
            study_id=request.regular_user_study_id,
            access_token=access_token,
            status="pending",
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)

        # Store for later reference
        request.interview_id = interview.id


# When steps


@when(parsers.parse('the super admin creates an organization named "{org_name}"'))
def super_admin_creates_org(client: Any, request: Any, org_name: str) -> None:
    """Super admin creates an organization."""
    from tests.test_helpers import sign_in_user

    # Sign in as super admin (using session-level super admin)
    token = sign_in_user("admin@tinyteam.co", "superadmin123")
    headers = {"Authorization": f"Bearer {token}"}

    # Generate unique owner email using test name hash to avoid collisions
    test_hash = hash(request.node.name) % 10000
    owner_email = f"owner-{test_hash}@{org_name.lower().replace(' ', '')}.com"

    # Create organization with owner
    response = client.post(
        "/orgs",
        json={
            "name": org_name.lower().replace(" ", "-"),
            "display_name": org_name,
            "description": f"Test organization: {org_name}",
            "owner_email": owner_email,
        },
        headers=headers,
    )

    # Store response and org data
    request.response = response
    if response.status_code == 201:
        org_data = response.json()
        request.super_admin_org_id = int(org_data["org_id"])
        request.super_admin_org_name = org_name


@when("the super admin lists all organizations")
def super_admin_lists_orgs(client: Any, request: Any) -> None:
    """Super admin lists all organizations."""
    from tests.test_helpers import sign_in_user

    # Sign in as super admin (using session-level super admin)
    token = sign_in_user("admin@tinyteam.co", "superadmin123")
    headers = {"Authorization": f"Bearer {token}"}

    # List organizations
    response = client.get("/orgs", headers=headers)

    # Store response
    request.response = response
    if response.status_code == 200:
        request.org_list = response.json()


@when(parsers.parse('the super admin creates a study titled "{title}" in "{org_name}"'))
def super_admin_creates_study(client: Any, request: Any, title: str, org_name: str) -> None:
    """Super admin creates a study in a specific organization."""
    from tests.test_helpers import sign_in_user

    # Sign in as super admin (using session-level super admin)
    token = sign_in_user("admin@tinyteam.co", "superadmin123")
    headers = {"Authorization": f"Bearer {token}"}

    # Create study (super admin should be able to access org context)
    response = client.post("/studies", json={"title": title}, headers=headers)

    # Store response
    request.response = response
    if response.status_code == 201:
        study_data = response.json()
        request.super_admin_study_id = int(study_data["study_id"])
        request.super_admin_study_title = title


@when(parsers.parse('the super admin retrieves interview with access_token "{access_token}"'))
def super_admin_retrieves_interview(client: Any, request: Any, access_token: str) -> None:
    """Super admin retrieves an interview by access token."""
    from tests.test_helpers import sign_in_user

    # Sign in as super admin (using session-level super admin)
    token = sign_in_user("admin@tinyteam.co", "superadmin123")
    headers = {"Authorization": f"Bearer {token}"}

    # Get interview using the study_id and interview_id
    response = client.get(
        f"/studies/{request.regular_user_study_id}/interviews/{request.interview_id}",
        headers=headers,
    )

    # Store response
    request.response = response
    if response.status_code == 200:
        request.interview_data = response.json()


@when(parsers.parse('the super admin accesses studies in "{org_name}"'))
def super_admin_accesses_studies(client: Any, request: Any, org_name: str) -> None:
    """Super admin accesses studies in an organization."""
    from tests.test_helpers import sign_in_user

    # Sign in as super admin (using session-level super admin)
    token = sign_in_user("admin@tinyteam.co", "superadmin123")
    headers = {"Authorization": f"Bearer {token}"}

    # Access studies endpoint
    response = client.get("/studies", headers=headers)

    # Store response (don't fail here, we check later)
    request.super_admin_studies_response = response


@when("the regular user lists users in their organization")
def regular_user_lists_users(client: Any, request: Any) -> None:
    """Regular user lists users in their organization."""
    from tests.test_helpers import sign_in_user

    # Sign in as regular user
    token = sign_in_user(request.regular_user_email, "testpass123")
    headers = {"Authorization": f"Bearer {token}"}

    # List users
    response = client.get("/orgs/current/users", headers=headers)

    # Store response
    request.response = response
    if response.status_code == 200:
        request.user_list = response.json()


@when(parsers.parse('the super admin requests organization details for "{org_name}"'))
def super_admin_requests_org_details(client: Any, request: Any, org_name: str) -> None:
    """Super admin requests organization details."""
    from tests.test_helpers import sign_in_user

    # Sign in as super admin (using session-level super admin)
    token = sign_in_user("admin@tinyteam.co", "superadmin123")
    headers = {"Authorization": f"Bearer {token}"}

    # Request org details
    response = client.get("/orgs/current", headers=headers)

    # Store response
    request.response = response
    if response.status_code == 200:
        request.org_details = response.json()


@given(parsers.parse('the second user creates a study titled "{title}" in their organization'))
def second_user_creates_study(client: Any, request: Any, title: str) -> None:
    """Second user creates a study in their organization."""
    from tests.test_helpers import sign_in_user

    # Sign in as second user
    token = sign_in_user(request.second_user_email, "testpass123")
    headers = {"Authorization": f"Bearer {token}"}

    # Create study
    response = client.post("/studies", json={"title": title}, headers=headers)
    assert response.status_code == 201

    # Store study_id for later use
    study_data = response.json()
    request.second_user_study_id = int(study_data["study_id"])
    request.second_user_study_title = title


@when("the regular user lists studies in their organization")
def regular_user_lists_studies(client: Any, request: Any) -> None:
    """Regular user lists studies in their own organization."""
    from tests.test_helpers import sign_in_user

    # Sign in as regular user
    token = sign_in_user(request.regular_user_email, "testpass123")
    headers = {"Authorization": f"Bearer {token}"}

    # List studies (should only see their org's studies)
    response = client.get("/studies", headers=headers)

    # Store response
    request.response = response
    if response.status_code == 200:
        request.study_list = response.json()


# Then steps


@then("the response status is 200")
def check_status_200(request: Any) -> None:
    """Check that response status is 200."""
    assert request.response.status_code == 200


@then("the response status is 201")
def check_status_201(request: Any) -> None:
    """Check that response status is 201."""
    assert request.response.status_code == 201


@then("the response status is 403")
def check_status_403(request: Any) -> None:
    """Check that response status is 403."""
    assert request.response.status_code == 403


@then(parsers.parse('the organization "{org_name}" exists in the database'))
def check_org_exists_in_db(request: Any, org_name: str) -> None:
    """Check that organization exists in database."""
    with TestingSessionLocal() as db:
        org = db.query(Organization).filter(Organization.display_name == org_name).first()
        assert org is not None
        assert org.display_name == org_name


@then(parsers.parse('"{org_name}" appears in the organization list'))
def check_org_in_list(request: Any, org_name: str) -> None:
    """Check that organization appears in list."""
    org_names = [org["name"] for org in request.org_list]
    assert org_name in org_names


@then(parsers.parse('the study "{title}" belongs to "{org_name}"'))
def check_study_belongs_to_org(request: Any, title: str, org_name: str) -> None:
    """Check that study belongs to correct organization."""
    with TestingSessionLocal() as db:
        study = db.query(Study).filter(Study.id == request.super_admin_study_id).first()
        assert study is not None
        assert study.title == title

        # Check organization
        org = db.query(Organization).filter(Organization.id == study.organization_id).first()
        assert org is not None
        assert org.display_name == org_name


@then("the interview data is returned")
def check_interview_data_returned(request: Any) -> None:
    """Check that interview data is returned."""
    assert request.interview_data is not None
    assert "interview_id" in request.interview_data


@then(parsers.parse("the user list has {count:d} user"))
@then(parsers.parse("the user list has {count:d} users"))
def check_user_list_count(request: Any, count: int) -> None:
    """Check that user list has expected count."""
    assert len(request.user_list) == count


@then(parsers.parse('"{email}" does not appear in the user list'))
def check_email_not_in_user_list(request: Any, email: str) -> None:
    """Check that email does not appear in user list."""
    user_emails = [user["email"] for user in request.user_list["items"]]
    assert email not in user_emails


@then(parsers.parse('the organization name is "{org_name}"'))
def check_org_name(request: Any, org_name: str) -> None:
    """Check that organization name matches."""
    assert request.org_details["display_name"] == org_name


@then(parsers.parse('the error message contains "{text}"'))
def check_error_contains(request: Any, text: str) -> None:
    """Check that error message contains text."""
    error_data = request.response.json()
    assert text.lower() in error_data.get("detail", "").lower()


@then("the study list is empty")
def check_study_list_empty(request: Any) -> None:
    """Check that study list is empty."""
    assert len(request.study_list["items"]) == 0


@then(parsers.parse('"{title}" does not appear in the study list'))
def check_study_not_in_list(request: Any, title: str) -> None:
    """Check that study title does not appear in list."""
    study_titles = [study["title"] for study in request.study_list["items"]]
    assert title not in study_titles


@when(parsers.parse('the super admin gets organization by ID for "{org_name}"'))
def super_admin_gets_org_by_id(client: Any, request: Any, org_name: str) -> None:
    """Super admin gets organization by ID."""
    from tests.test_helpers import sign_in_user

    # Sign in as super admin
    token = sign_in_user("admin@tinyteam.co", "superadmin123")
    headers = {"Authorization": f"Bearer {token}"}

    # Get org by ID (use last created org id)
    org_id = request.last_created_org_id
    response = client.get(f"/orgs/{org_id}", headers=headers)

    # Store response
    request.response = response
    if response.status_code == 200:
        request.org_details = response.json()


@when(parsers.parse('the regular user gets organization by ID for "{org_name}"'))
def regular_user_gets_org_by_id(client: Any, request: Any, org_name: str) -> None:
    """Regular user attempts to get organization by ID."""
    from tests.test_helpers import sign_in_user

    # Sign in as regular user
    token = sign_in_user(request.regular_user_email, "testpass123")
    headers = {"Authorization": f"Bearer {token}"}

    # Try to get the "Other Company" org by ID (stored in last_created_org_id)
    org_id = request.last_created_org_id
    response = client.get(f"/orgs/{org_id}", headers=headers)

    # Store response
    request.response = response


# Steps for organization creation with owner


@when(
    parsers.parse(
        'the super admin creates an organization named "{org_name}" with owner "{owner_email}"'
    )
)
def super_admin_creates_org_with_owner(
    client: Any, request: Any, org_name: str, owner_email: str
) -> None:
    """Super admin creates an organization with an owner."""
    from tests.test_helpers import sign_in_user

    # Clean up: Delete Firebase user if it exists from previous tests
    with suppress(Exception):
        existing_user = auth.get_user_by_email(owner_email)
        auth.delete_user(existing_user.uid)

    # Sign in as super admin
    token = sign_in_user("admin@tinyteam.co", "superadmin123")
    headers = {"Authorization": f"Bearer {token}"}

    # Create organization with owner email
    response = client.post(
        "/orgs",
        json={
            "name": org_name.lower().replace(" ", "-"),
            "display_name": org_name,
            "description": f"Test organization: {org_name}",
            "owner_email": owner_email,
        },
        headers=headers,
    )

    # Store response and org data
    request.response = response
    if response.status_code == 201:
        org_data = response.json()
        request.last_created_org_id = int(org_data["org_id"])
        request.last_created_org_name = org_name
        request.last_created_owner_email = owner_email
        request.owner_data = org_data.get("owner", {})


@given(
    parsers.parse(
        'the super admin creates an organization named "{org_name}" with owner "{owner_email}"'
    )
)
def super_admin_creates_org_with_owner_given(
    client: Any, request: Any, org_name: str, owner_email: str
) -> None:
    """Super admin creates an organization with an owner (Given step)."""
    # Call the same implementation as When step
    super_admin_creates_org_with_owner(client, request, org_name, owner_email)


@then(parsers.parse('the owner "{owner_email}" exists in the database'))
def check_owner_exists_in_db(request: Any, owner_email: str) -> None:
    """Check that owner exists in database."""
    with TestingSessionLocal() as db:
        # Check that user with this email exists in User table
        user = db.query(User).filter(User.email == owner_email).first()
        assert user is not None
        assert user.email == owner_email

        # Store owner user_id for later checks
        request.owner_user_id = user.id


@then(parsers.parse('the owner is linked to organization "{org_name}"'))
def check_owner_linked_to_org(request: Any, org_name: str) -> None:
    """Check that owner is linked to the organization."""
    with TestingSessionLocal() as db:
        # Get the owner user
        user = db.query(User).filter(User.id == request.owner_user_id).first()
        assert user is not None

        # Check organization link
        assert user.organization_id == request.last_created_org_id

        # Verify org display_name matches
        org = db.query(Organization).filter(Organization.id == user.organization_id).first()
        assert org is not None
        assert org.display_name == org_name


@then(parsers.parse('the owner has role "{role}"'))
def check_owner_role(request: Any, role: str) -> None:
    """Check that owner has the correct role."""
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.id == request.owner_user_id).first()
        assert user is not None
        assert user.role == role


@then("a password reset link is returned")
def check_password_reset_link_returned(request: Any) -> None:
    """Check that a password reset link is returned in the response."""
    assert "owner" in request.response.json()
    owner_data = request.response.json()["owner"]
    assert "password_reset_link" in owner_data
    assert owner_data["password_reset_link"].startswith("http")

    # Store for potential later use
    request.password_reset_link = owner_data["password_reset_link"]


@when(parsers.parse('the owner "{owner_email}" requests their organization details'))
def owner_requests_own_org_details(client: Any, request: Any, owner_email: str) -> None:
    """Owner requests their own organization details."""
    from tests.test_helpers import sign_in_user

    # Sign in as owner (Firebase user was created during org creation)
    # We need to use the password reset link to set a password first,
    # but for testing purposes, we'll create a password directly
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == owner_email).first()
        assert user is not None

        # Set a password for this user in Firebase
        firebase_user = auth.get_user_by_email(owner_email)
        auth.update_user(firebase_user.uid, password="ownerpass123")

    # Now sign in and request org details
    token = sign_in_user(owner_email, "ownerpass123")
    headers = {"Authorization": f"Bearer {token}"}

    # Get organization details (via /orgs/current endpoint)
    response = client.get("/orgs/current", headers=headers)

    # Store response
    request.response = response
    if response.status_code == 200:
        request.org_details = response.json()


@when(parsers.parse('the owner "{owner_email}" requests organization details for "{org_name}"'))
def owner_requests_other_org_details(
    client: Any, request: Any, owner_email: str, org_name: str
) -> None:
    """Owner attempts to request details for a different organization."""
    from tests.test_helpers import sign_in_user

    # Set password for owner in Firebase (if not already set)
    with suppress(Exception):
        firebase_user = auth.get_user_by_email(owner_email)
        auth.update_user(firebase_user.uid, password="ownerpass123")

    # Sign in as owner
    token = sign_in_user(owner_email, "ownerpass123")
    headers = {"Authorization": f"Bearer {token}"}

    # Try to get the other organization by ID
    response = client.get(f"/orgs/{request.last_created_org_id}", headers=headers)

    # Store response
    request.response = response
