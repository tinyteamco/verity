import contextlib

import pytest
from firebase_admin import auth
from pytest_bdd import given, parsers, scenarios, then, when
from src.models import User

scenarios("../features/study_guides.feature")


@pytest.fixture
def response_data():
    return {}


@pytest.fixture
def current_user_headers():
    """Headers for the current user - will be set by step definitions"""
    return {}


# Shared step definitions (similar to other test files)


@given("a test organization with ID 1 exists")
def create_test_organization(client, super_admin_token):
    """Create test organization for the scenarios"""
    import uuid

    headers = {"Authorization": f"Bearer {super_admin_token}"}
    unique_id = str(uuid.uuid4())[:8]
    response = client.post(
        "/orgs",
        json={
            "name": "test-organization",
            "display_name": "Test Organization",
            "description": "Test organization for study guides",
            "owner_email": f"owner-{unique_id}@testorganization.com",
        },
        headers=headers,
    )
    assert response.status_code == 201


@given(
    parsers.parse('a study with ID {study_id:d} titled "{title}" exists in organization {org_id:d}')
)
def create_test_study(client, super_admin_token, study_id, title, org_id):
    """Create a test study - we'll use the conftest testing session"""
    from firebase_admin import auth
    from src.models import Organization, User
    from tests.conftest import TestingSessionLocal
    from tests.test_helpers import sign_in_user

    # Create a temporary user to create the study
    try:
        auth.create_user(
            uid="temp-study-creator",
            email="temp@example.com",
            password="testpass123",
            email_verified=True,
        )
        auth.set_custom_user_claims(
            "temp-study-creator", {"tenant": "organization", "role": "owner"}
        )

        # Use the testing session instead of get_db()
        db_session = TestingSessionLocal()
        try:
            # Find the test organization
            org = (
                db_session.query(Organization)
                .filter(Organization.display_name == "Test Organization")
                .first()
            )
            if not org:
                # If not found, create it
                org = Organization(
                    name="test-organization",
                    display_name="Test Organization",
                    description="Test organization",
                )
                db_session.add(org)
                db_session.commit()
                db_session.refresh(org)

            user = User(
                firebase_uid="temp-study-creator",
                email="temp@example.com",
                role="owner",
                organization_id=org.id,
            )
            db_session.add(user)
            db_session.commit()

            # Create study using this temp user
            temp_token = sign_in_user("temp@example.com", "testpass123")
            headers = {"Authorization": f"Bearer {temp_token}"}
            response = client.post(
                f"/orgs/{org_id}/studies", json={"title": title}, headers=headers
            )
            assert response.status_code == 201

        finally:
            db_session.close()
    finally:
        # Clean up temp user
        with contextlib.suppress(Exception):
            auth.delete_user("temp-study-creator")


@given(parsers.parse('a signed-in organization user with role "{role}"'))
def set_org_user_with_role(client, current_user_headers, org_user_token, test_org_user, role):
    """Set current user to organization user with specific role"""
    # Update the user's role in the database
    from src.models import Organization, User
    from tests.conftest import TestingSessionLocal

    # Use the testing session
    db_session = TestingSessionLocal()
    try:
        # Find the test organization (should be the first one created)
        org = (
            db_session.query(Organization)
            .filter(Organization.display_name == "Test Organization")
            .first()
        )
        if not org:
            raise RuntimeError(
                "Test organization not found - "
                "ensure 'a test organization with ID 1 exists' step runs first"
            )

        # Find or create the user in our database
        existing_user = db_session.query(User).filter(User.firebase_uid == "test-org-user").first()
        if not existing_user:
            user = User(
                firebase_uid="test-org-user",
                email="testuser@example.com",
                role=role,
                organization_id=org.id,
            )
            db_session.add(user)
        else:
            existing_user.role = role
            existing_user.organization_id = org.id
        db_session.commit()
    finally:
        db_session.close()

    current_user_headers["Authorization"] = f"Bearer {org_user_token}"


@given("a signed-in interviewee user")
def set_interviewee_user(current_user_headers, interviewee_token):
    """Set current user to interviewee"""
    current_user_headers["Authorization"] = f"Bearer {interviewee_token}"


@given(parsers.parse("a study with ID {study_id:d} exists in a different organization"))
def create_study_different_org(client, super_admin_token, study_id):
    """Create a study in a different organization"""
    # Create another organization first
    import uuid

    headers = {"Authorization": f"Bearer {super_admin_token}"}
    unique_id = str(uuid.uuid4())[:8]
    org_response = client.post(
        "/orgs",
        json={
            "name": "other-organization",
            "display_name": "Other Organization",
            "description": "Other organization for testing",
            "owner_email": f"owner-{unique_id}@otherorganization.com",
        },
        headers=headers,
    )
    assert org_response.status_code == 201

    # Create user in that org (we'll use a different user for this)
    try:
        auth.create_user(
            uid="other-org-user",
            email="otheruser@example.com",
            password="testpass123",
            email_verified=True,
        )
        auth.set_custom_user_claims("other-org-user", {"tenant": "organization", "role": "owner"})

        # Sign in and create study
        from tests.test_helpers import sign_in_user

        other_token = sign_in_user("otheruser@example.com", "testpass123")

        # Add user to database
        from tests.conftest import TestingSessionLocal

        db_session = TestingSessionLocal()
        try:
            # Get the actual organization ID that was just created
            other_org_data = org_response.json()
            other_org_id = int(other_org_data["org_id"])

            user = User(
                firebase_uid="other-org-user",
                email="otheruser@example.com",
                role="owner",
                organization_id=other_org_id,
            )
            db_session.add(user)
            db_session.commit()
        finally:
            db_session.close()

        # Create study
        study_headers = {"Authorization": f"Bearer {other_token}"}
        response = client.post(
            f"/orgs/{other_org_id}/studies", json={"title": "Other Study"}, headers=study_headers
        )
        assert response.status_code == 201

    finally:
        with contextlib.suppress(Exception):
            auth.delete_user("other-org-user")


@given(parsers.parse('a study guide exists for study {study_id:d} with content "{content}"'))
def create_study_guide(client, org_user_token, study_id, content):
    """Create a study guide with the given content"""
    headers = {"Authorization": f"Bearer {org_user_token}"}
    response = client.put(
        f"/studies/{study_id}/guide",
        json={"content_md": content},
        headers=headers,
    )
    assert response.status_code == 200


@when(parsers.parse('they PUT /studies/{study_id}/guide with content "{content}"'))
def put_study_guide(client, response_data, current_user_headers, study_id, content):
    response = client.put(
        f"/studies/{study_id}/guide",
        json={"content_md": content},
        headers=current_user_headers,
    )
    response_data["response"] = response
    response_data["json"] = response.json() if response.status_code in [200, 201] else None


@when(parsers.parse("they GET /studies/{study_id}/guide"))
def get_study_guide(client, response_data, current_user_headers, study_id):
    response = client.get(f"/studies/{study_id}/guide", headers=current_user_headers)
    response_data["response"] = response
    response_data["json"] = response.json() if response.status_code == 200 else None


@when(parsers.parse("an unauthenticated user gets /studies/{study_id}/guide"))
def get_study_guide_unauthenticated(client, response_data, study_id):
    response = client.get(f"/studies/{study_id}/guide")
    response_data["response"] = response
    response_data["json"] = response.json() if response.status_code == 200 else None


@then(parsers.parse('the response has a study_id "{study_id}"'))
def check_study_id(response_data, study_id):
    json_data = response_data["json"]
    assert json_data is not None
    assert json_data["study_id"] == study_id


@then(parsers.parse('the response has content_md containing "{text}"'))
def check_content_md_contains(response_data, text):
    json_data = response_data["json"]
    assert json_data is not None
    assert text in json_data["content_md"]


@then("the response has an updated_at timestamp")
def check_updated_at_timestamp(response_data):
    json_data = response_data["json"]
    assert json_data is not None
    assert "updated_at" in json_data
    # Validate it's a proper timestamp format
    from datetime import datetime

    datetime.fromisoformat(json_data["updated_at"].replace("Z", "+00:00"))


@then("the response contains an error message")
def check_error_message(response_data):
    json_data = response_data["response"].json()
    assert "detail" in json_data or "error" in json_data


# Common status code assertions
@then("the response status is 200")
def check_200_status(response_data):
    assert response_data["response"].status_code == 200


@then("the response status is 201")
def check_201_status(response_data):
    assert response_data["response"].status_code == 201


@then("the response status is 401")
def check_401_status(response_data):
    assert response_data["response"].status_code == 401


@then("the response status is 403")
def check_403_status(response_data):
    assert response_data["response"].status_code == 403


@then("the response status is 404")
def check_404_status(response_data):
    assert response_data["response"].status_code == 404


@then("the response status is 500")
def check_500_status(response_data):
    assert response_data["response"].status_code == 500


# New steps for AI-generated study creation


@given("a signed-in super admin user")
def set_super_admin_user(current_user_headers, super_admin_token):
    """Set current user to super admin"""
    current_user_headers["Authorization"] = f"Bearer {super_admin_token}"


@when(parsers.parse('they POST /orgs/{org_id:d}/studies/generate with topic "{topic}"'))
def post_generate_study(client, response_data, current_user_headers, org_id, topic):
    response = client.post(
        f"/orgs/{org_id}/studies/generate",
        json={"topic": topic},
        headers=current_user_headers,
    )
    response_data["response"] = response
    response_data["json"] = response.json() if response.status_code in [200, 201] else None


@then("the response has a study object")
def check_has_study_object(response_data):
    json_data = response_data["json"]
    assert json_data is not None
    assert "study" in json_data
    assert "study_id" in json_data["study"]
    assert "title" in json_data["study"]
    assert "description" in json_data["study"]


@then("the response has a guide object")
def check_has_guide_object(response_data):
    json_data = response_data["json"]
    assert json_data is not None
    assert "guide" in json_data
    assert "study_id" in json_data["guide"]
    assert "content_md" in json_data["guide"]
    assert "updated_at" in json_data["guide"]


@then("the study title is a slug")
def check_study_title_is_slug(response_data):
    """Verify the study title is a lowercase slug with hyphens"""
    json_data = response_data["json"]
    assert json_data is not None
    title = json_data["study"]["title"]
    # Should be lowercase
    assert title == title.lower()
    # Should only contain alphanumeric + hyphens
    import re

    assert re.match(r"^[a-z0-9-]+$", title)
    # Should not start or end with hyphen
    assert not title.startswith("-")
    assert not title.endswith("-")


@then(parsers.parse('the study description is "{expected_description}"'))
def check_study_description(response_data, expected_description):
    json_data = response_data["json"]
    assert json_data is not None
    assert json_data["study"]["description"] == expected_description


@then(parsers.parse('the guide content_md contains "{text}" or "{alt_text}"'))
def check_guide_content_contains_either(response_data, text, alt_text):
    """Check if guide content contains either text or alt_text (case insensitive)"""
    json_data = response_data["json"]
    assert json_data is not None
    content = json_data["guide"]["content_md"].lower()
    assert text.lower() in content or alt_text.lower() in content


@then(parsers.parse("the guide content_md length is greater than {min_length:d}"))
def check_guide_content_length(response_data, min_length):
    json_data = response_data["json"]
    assert json_data is not None
    content = json_data["guide"]["content_md"]
    assert len(content) > min_length


@given("the LLM service will fail when generating interview guides")
def mock_llm_failure(monkeypatch):
    """Mock the LLM service to raise an exception when generating interview guides"""

    def failing_guide_generator(topic: str) -> str:
        raise RuntimeError("Simulated LLM failure")

    # Patch where the function is imported in api/main.py
    monkeypatch.setattr("src.api.main.generate_interview_guide", failing_guide_generator)


@then(parsers.parse('no study was created with description "{description}"'))
def check_no_study_created(client, org_user_token, description):
    """Verify that no study with this description exists (rollback worked)"""
    from src.models import Study
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        study = db_session.query(Study).filter(Study.description == description).first()
        assert study is None, (
            f"Study with description '{description}' should not exist after rollback"
        )
    finally:
        db_session.close()
