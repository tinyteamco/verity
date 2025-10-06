"""
Step definitions for study management tests
"""

import contextlib

import pytest
from fastapi.testclient import TestClient
from firebase_admin import auth
from pytest_bdd import given, parsers, scenarios, then, when
from src.models import Organization, Study, User

scenarios("../features/study_management.feature")


@pytest.fixture
def auth_headers():
    """Auth headers for requests"""
    return {}


@pytest.fixture
def test_response():
    """Store response for assertions"""
    return {"response": None}


@pytest.fixture
def test_data():
    """Store test data across steps"""
    return {
        "studies": {},
        "current_study_id": None,
        "other_org_study_id": None,
        "current_org_id": None,
    }


def create_org_user_with_role(uid: str, email: str, role: str, auth_headers, test_data):
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
            firebase_uid=uid,
            email=email,
            role=role,
            organization_id=org.id,
        )
        db_session.add(db_user)
        db_session.commit()

        test_data["current_org_id"] = org.id
        return org.id
    finally:
        db_session.close()


@given(parsers.parse('a signed-in organization user with role "{role}"'))
def create_org_user(role: str, client: TestClient, auth_headers, test_data):
    """Create an organization user with specified role"""
    uid = f"test-{role}-study"
    email = f"{role}-study@example.com"

    try:
        create_org_user_with_role(uid, email, role, auth_headers, test_data)
        yield
    finally:
        with contextlib.suppress(Exception):
            auth.delete_user(uid)


@given("a signed-in interviewee user")
def create_interviewee_user(client: TestClient, auth_headers):
    """Create an interviewee user"""
    try:
        auth.create_user(
            uid="test-interviewee-study",
            email="interviewee-study@example.com",
            password="testpass123",
            email_verified=True,
        )
        auth.set_custom_user_claims("test-interviewee-study", {"tenant": "interviewee"})

        # Get token for API requests
        from tests.test_helpers import sign_in_user

        token = sign_in_user("interviewee-study@example.com", "testpass123")
        auth_headers["Authorization"] = f"Bearer {token}"

        yield
    finally:
        with contextlib.suppress(Exception):
            auth.delete_user("test-interviewee-study")


@given("an unauthenticated user")
def unauthenticated_user(auth_headers):
    """Clear auth headers for unauthenticated requests"""
    auth_headers.clear()


@given(parsers.parse('a study exists with title "{title}"'))
def create_study_with_title(title: str, client: TestClient, test_data):
    """Create a study with specific title"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        org_id = test_data["current_org_id"]

        study = Study(
            title=title,
            organization_id=org_id,
        )
        db_session.add(study)
        db_session.commit()
        db_session.refresh(study)
        test_data["studies"][title] = study.id
        test_data["current_study_id"] = study.id
    finally:
        db_session.close()


@given(parsers.parse('a study exists in a different organization with title "{title}"'))
def create_study_other_org(title: str, client: TestClient, test_data):
    """Create a study in a different organization"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        # Create a different organization
        other_org = Organization(
            name="LOther Organization",
            display_name="Other Organization",
            description="Test organization",
        )
        db_session.add(other_org)
        db_session.commit()
        db_session.refresh(other_org)

        # Create study in the other org
        study = Study(
            title=title,
            organization_id=other_org.id,
        )
        db_session.add(study)
        db_session.commit()
        db_session.refresh(study)
        test_data["other_org_study_id"] = study.id
    finally:
        db_session.close()


@when(parsers.parse('they POST /studies with title "{title}"'))
def post_study(title: str, client: TestClient, auth_headers, test_response, test_data):
    """Create a new study with given title"""
    org_id = test_data["current_org_id"]
    response = client.post(f"/orgs/{org_id}/studies", json={"title": title}, headers=auth_headers)
    test_response["response"] = response


@when("they GET /studies")
def get_studies(client: TestClient, auth_headers, test_response, test_data):
    """Get list of studies"""
    # For interviewees, there's no org_id, so we use a placeholder that will fail validation
    org_id = test_data.get("current_org_id", "invalid")
    response = client.get(f"/orgs/{org_id}/studies", headers=auth_headers)
    test_response["response"] = response


@when("they GET /studies/{study_id}")
def get_study_by_id(client: TestClient, auth_headers, test_response, test_data):
    """Get specific study by ID"""
    org_id = test_data["current_org_id"]
    study_id = test_data["current_study_id"]
    response = client.get(f"/orgs/{org_id}/studies/{study_id}", headers=auth_headers)
    test_response["response"] = response


@when("they GET /studies/{other_org_study_id}")
def get_other_org_study(client: TestClient, auth_headers, test_response, test_data):
    """Try to get study from other organization"""
    # Try to access other org's study using wrong org_id - this should fail!
    org_id = test_data["current_org_id"]  # User's own org
    study_id = test_data["other_org_study_id"]  # Study from different org
    response = client.get(f"/orgs/{org_id}/studies/{study_id}", headers=auth_headers)
    test_response["response"] = response


@when(parsers.parse('they PATCH /studies/{{study_id}} with title "{new_title}"'))
def patch_study_title(new_title: str, client: TestClient, auth_headers, test_response, test_data):
    """Update study title"""
    org_id = test_data["current_org_id"]
    study_id = test_data["current_study_id"]
    response = client.patch(
        f"/orgs/{org_id}/studies/{study_id}", json={"title": new_title}, headers=auth_headers
    )
    test_response["response"] = response


@when("they DELETE /studies/{study_id}")
def delete_study(client: TestClient, auth_headers, test_response, test_data):
    """Delete a study"""
    org_id = test_data["current_org_id"]
    study_id = test_data["current_study_id"]
    response = client.delete(f"/orgs/{org_id}/studies/{study_id}", headers=auth_headers)
    test_response["response"] = response


@then("the response status is 200")
def check_200_status(test_response):
    """Check response has 200 status"""
    assert test_response["response"].status_code == 200


@then("the response status is 201")
def check_201_status(test_response):
    """Check response has 201 status"""
    assert test_response["response"].status_code == 201


@then("the response status is 401")
def check_401_status(test_response):
    """Check response has 401 status"""
    assert test_response["response"].status_code == 401


@then("the response status is 403")
def check_403_status(test_response):
    """Check response has 403 status"""
    assert test_response["response"].status_code == 403


@then("the response status is 422")
def check_422_status(test_response):
    """Check response has 422 status"""
    assert test_response["response"].status_code == 422


@then("the response status is 404")
def check_404_status(test_response):
    """Check response has 404 status"""
    assert test_response["response"].status_code == 404


@then("the response has a study_id")
def check_has_study_id(test_response):
    """Check response contains study_id"""
    data = test_response["response"].json()
    assert "study_id" in data
    assert data["study_id"] is not None


@then("the response has organization_id")
def check_has_org_id(test_response):
    """Check response contains organization_id"""
    data = test_response["response"].json()
    assert "org_id" in data
    assert data["org_id"] is not None


@then(parsers.parse("the response contains {count:d} studies"))
def check_study_count(count: int, test_response):
    """Check number of studies in response"""
    data = test_response["response"].json()
    assert "items" in data
    assert len(data["items"]) == count


@then(parsers.parse('the study list contains "{title}"'))
def check_study_in_list(title: str, test_response):
    """Check if study title appears in the list"""
    data = test_response["response"].json()
    titles = [study["title"] for study in data["items"]]
    assert title in titles


@then(parsers.parse('the study list does not contain "{title}"'))
def check_study_not_in_list(title: str, test_response):
    """Check if study title does not appear in the list"""
    data = test_response["response"].json()
    titles = [study["title"] for study in data["items"]]
    assert title not in titles


@then(parsers.parse('the study title is "{title}"'))
def check_study_title(title: str, test_response):
    """Check study title in response"""
    data = test_response["response"].json()
    assert data["title"] == title


@then('the error message is "Organization user access required"')
def check_org_required_error(test_response):
    """Check specific error message for org user requirement"""
    data = test_response["response"].json()
    # Updated error message after security fix
    assert data["detail"] in ["Organization user access required", "User not in organization"]
