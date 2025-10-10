"""
Step definitions for study settings tests
"""

import contextlib

import pytest
from firebase_admin import auth
from pytest_bdd import given, parsers, scenarios, then, when
from src.models import Organization, Study, User

scenarios("../features/study_settings.feature")


# Helper functions


def get_unique_uid(prefix: str, request) -> str:
    """Generate unique UID for each test"""
    test_name = request.node.name
    return f"{prefix}-{hash(test_name) % 10000}"


def get_unique_email(prefix: str, request) -> str:
    """Generate unique email for each test"""
    test_name = request.node.name
    return f"{prefix}-{hash(test_name) % 10000}@example.com"


# Given steps


@given(parsers.parse('a signed-in organization user with role "{role}"'))
def signed_in_organization_user(client, role, request):
    """Create and sign in a unique organization user for this test"""
    from tests.conftest import TestingSessionLocal
    from tests.test_helpers import sign_in_user

    # Create unique user for this test
    user_uid = get_unique_uid(f"test-{role}-settings", request)
    user_email = get_unique_email(f"test-{role}-settings", request)

    # Create user in Firebase
    with contextlib.suppress(Exception):
        auth.create_user(
            uid=user_uid,
            email=user_email,
            password="testpass123",
            email_verified=True,
        )

    # Set custom claims
    auth.set_custom_user_claims(user_uid, {"tenant": "organization"})

    # Create database user entry
    with TestingSessionLocal() as db:
        # Create organization first
        org_name = f"Test Organization {hash(request.node.name) % 10000}"
        org = Organization(
            name=org_name.lower().replace(" ", "-"),
            display_name=org_name,
            description="Test organization",
        )
        db.add(org)
        db.commit()
        db.refresh(org)

        # Create user
        existing_user = db.query(User).filter(User.firebase_uid == user_uid).first()
        if not existing_user:
            user = User(
                firebase_uid=user_uid,
                email=user_email,
                role=role,
                organization_id=org.id,
            )
            db.add(user)
            db.commit()

        request.test_org_id = org.id

    # Sign in and get token
    token = sign_in_user(user_email, "testpass123")
    request.test_auth_headers = {"Authorization": f"Bearer {token}"}


@given(parsers.parse('a study exists with slug "{slug}"'))
def study_exists_with_slug(client, slug, request):
    """Create a study with specific slug"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        org_id = getattr(request, "test_org_id", 1)

        # Make slug unique per test
        unique_slug = f"{slug}-{hash(request.node.name) % 10000}"

        study = Study(
            title="Test Study",
            description="Test study with slug",
            slug=unique_slug,
            participant_identity_flow="anonymous",
            organization_id=org_id,
        )
        db_session.add(study)
        db_session.commit()
        db_session.refresh(study)

        request.test_study_id = study.id
        request.test_study_slug = unique_slug

    finally:
        db_session.close()


# When steps


@when("they GET /studies/{study_id}")
def get_study_by_id(client, request):
    """GET specific study by ID"""
    headers = getattr(request, "test_auth_headers", {})
    org_id = getattr(request, "test_org_id", 1)
    study_id = getattr(request, "test_study_id", 1)

    response = client.get(f"/orgs/{org_id}/studies/{study_id}", headers=headers)
    request.test_response = response


# Then steps


@then("the response status is 200")
def response_status_is_200(request):
    """Check response status is 200"""
    response = request.test_response
    assert response.status_code == 200


@then("the response has a slug field")
def response_has_slug_field(request):
    """Check response has slug field"""
    response = request.test_response
    data = response.json()
    assert "slug" in data


@then(parsers.parse('the slug is "{expected_slug}"'))
def slug_is(request, expected_slug: str):
    """Check slug matches expected value"""
    response = request.test_response
    data = response.json()

    # The actual slug has been made unique, so we check if it starts with expected
    actual_slug = data["slug"]
    # Remove the unique suffix to compare
    base_slug = actual_slug.rsplit("-", 1)[0]
    assert base_slug == expected_slug or actual_slug.startswith(expected_slug)


# Fixtures


@pytest.fixture
def db():
    """Database session fixture"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as session:
        yield session
