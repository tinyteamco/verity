import contextlib
from datetime import UTC, datetime

import pytest
from firebase_admin import auth
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy.orm import Session
from src.models import Interview, Organization, Study, User

scenarios("../features/researcher_interview_list.feature")


# Test data management - each test gets unique IDs to avoid conflicts


def get_unique_uid(prefix: str, request) -> str:
    """Generate unique UID for each test"""
    test_name = request.node.name
    return f"{prefix}-{hash(test_name) % 10000}"


def get_unique_email(prefix: str, request) -> str:
    """Generate unique email for each test"""
    test_name = request.node.name
    return f"{prefix}-{hash(test_name) % 10000}@example.com"


# Background step definitions


@given("a test organization with ID 1 exists")
def create_test_organization(client, super_admin_token, request):
    """Create test organization for the scenarios"""
    from tests.conftest import TestingSessionLocal

    headers = {"Authorization": f"Bearer {super_admin_token}"}

    # Use unique name per test to avoid conflicts
    org_name = f"Test Organization {hash(request.node.name) % 10000}"
    owner_email = f"owner@testorg{hash(request.node.name) % 10000}.com"
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

    # Get the actual org ID from database
    with TestingSessionLocal() as db:
        org = (
            db.query(Organization)
            .filter(Organization.name == org_name.lower().replace(" ", "-"))
            .first()
        )
        assert org is not None
        request.test_org_id = org.id


@given(
    parsers.parse('a study with ID {study_id:d} titled "{title}" exists in organization {org_id:d}')
)
def create_test_study(client, super_admin_token, study_id, title, org_id, request):
    """Create a test study directly in database"""
    from tests.conftest import TestingSessionLocal

    # Use the actual org_id stored from previous step
    actual_org_id = getattr(request, "test_org_id", org_id)

    with TestingSessionLocal() as db:
        # Generate unique slug for this test
        slug = title.lower().replace(" ", "-") + f"-{hash(request.node.name) % 10000}"

        # Create study directly in database
        study = Study(
            title=title,
            description="Test study description",
            slug=slug,
            participant_identity_flow="anonymous",
            organization_id=actual_org_id,
        )
        db.add(study)
        db.commit()
        db.refresh(study)
        request.test_study_id = study.id


@given("a completed interview exists for study 1 with transcript and recording")
def completed_interview_with_artifacts(db: Session, request):
    """Create a completed interview with transcript and recording URLs"""
    import uuid

    # Use the actual study_id stored from previous step
    actual_study_id = getattr(request, "test_study_id", 1)

    interview = Interview(
        study_id=actual_study_id,
        access_token=f"token-{uuid.uuid4()}",
        status="completed",
        completed_at=datetime.now(UTC),
        transcript_url="https://storage.googleapis.com/verity-artifacts/iv_1/transcript.txt",
        recording_url="https://storage.googleapis.com/verity-artifacts/iv_1/recording.wav",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    request.test_interview_id = interview.id


@given(parsers.parse("a study with ID {study_id:d} exists in organization {org_id:d}"))
def create_study_in_org(client, super_admin_token, study_id, org_id, request, db):
    """Create a study in a specific organization"""
    # First, create the organization if it doesn't exist
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        org_name = f"Test Org {org_id} {hash(request.node.name) % 10000}"
        owner_email = f"owner-org{org_id}@testorg{hash(request.node.name) % 10000}.com"
        headers = {"Authorization": f"Bearer {super_admin_token}"}
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

    # Create study directly in database
    slug = f"study-org{org_id}-{hash(request.node.name) % 10000}"
    study = Study(
        title=f"Study in Org {org_id}",
        description="Test study",
        slug=slug,
        participant_identity_flow="anonymous",
        organization_id=org_id,
    )
    db.add(study)
    db.commit()
    db.refresh(study)


@given(parsers.parse("a completed interview exists for study {study_id:d}"))
def completed_interview_for_study(db: Session, study_id: int, request):
    """Create a completed interview for a specific study"""
    import uuid

    # Use the actual study_id stored from previous step
    actual_study_id = getattr(request, "test_study_id", study_id)

    interview = Interview(
        study_id=actual_study_id,
        access_token=f"token-{uuid.uuid4()}",
        status="completed",
        completed_at=datetime.now(UTC),
        transcript_url=f"https://storage.googleapis.com/verity-artifacts/iv_{actual_study_id}/transcript.txt",
        recording_url=f"https://storage.googleapis.com/verity-artifacts/iv_{actual_study_id}/recording.wav",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)


@given(
    parsers.parse("a completed interview with ID {interview_id:d} exists for study {study_id:d}")
)
def completed_interview_with_id_for_study(db: Session, interview_id: int, study_id: int, request):
    """Create a completed interview with specific ID for a study"""
    import uuid

    # Use the actual study_id stored from previous step
    actual_study_id = getattr(request, "test_study_id", study_id)

    interview = Interview(
        study_id=actual_study_id,
        access_token=f"token-{uuid.uuid4()}",
        status="completed",
        completed_at=datetime.now(UTC),
        transcript_url=f"https://storage.googleapis.com/verity-artifacts/iv_{interview_id}/transcript.txt",
        recording_url=f"https://storage.googleapis.com/verity-artifacts/iv_{interview_id}/recording.wav",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    # Store the actual interview ID
    request.test_interview_id = interview.id


@given(parsers.parse("a pending interview exists for study {study_id:d}"))
def pending_interview_for_study(db: Session, study_id: int, request):
    """Create a pending interview for a study"""
    import uuid

    # Use the actual study_id stored from previous step
    actual_study_id = getattr(request, "test_study_id", study_id)

    interview = Interview(
        study_id=actual_study_id,
        access_token=f"pending-{uuid.uuid4()}",
        status="pending",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)


@given(parsers.parse('a signed-in organization user with role "{role}"'))
def signed_in_organization_user(client, role, request):
    """Create and sign in a unique organization user for this test"""
    from tests.conftest import TestingSessionLocal
    from tests.test_helpers import sign_in_user

    # Create unique user for this test
    user_uid = get_unique_uid(f"test-{role}", request)
    user_email = get_unique_email(f"test-{role}", request)

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
        existing_user = db.query(User).filter(User.firebase_uid == user_uid).first()
        if not existing_user:
            # Use the actual org_id stored from previous step
            actual_org_id = getattr(request, "test_org_id", 1)
            org = db.query(Organization).filter(Organization.id == actual_org_id).first()
            if org:
                user = User(
                    firebase_uid=user_uid,
                    email=user_email,
                    role=role,
                    organization_id=org.id,
                )
                db.add(user)
                db.commit()

    # Sign in and get token
    token = sign_in_user(user_email, "testpass123")
    request.test_auth_headers = {"Authorization": f"Bearer {token}"}


@given(parsers.parse('a signed-in organization user with role "{role}" in organization {org_id:d}'))
def signed_in_organization_user_in_org(client, role, org_id, request):
    """Create and sign in a unique organization user for a specific organization"""
    from tests.conftest import TestingSessionLocal
    from tests.test_helpers import sign_in_user

    # Create unique user for this test
    user_uid = get_unique_uid(f"test-{role}-org{org_id}", request)
    user_email = get_unique_email(f"test-{role}-org{org_id}", request)

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
        existing_user = db.query(User).filter(User.firebase_uid == user_uid).first()
        if not existing_user:
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if org:
                user = User(
                    firebase_uid=user_uid,
                    email=user_email,
                    role=role,
                    organization_id=org.id,
                )
                db.add(user)
                db.commit()

    # Sign in and get token
    token = sign_in_user(user_email, "testpass123")
    request.test_auth_headers = {"Authorization": f"Bearer {token}"}


@given(parsers.parse("an interview with ID {interview_id:d} has a transcript stored in GCS"))
def interview_with_transcript(db: Session, interview_id: int, request):
    """Ensure interview has transcript URL (already set in background)"""
    # Interview already created in background with transcript URL


@given(parsers.parse("an interview with ID {interview_id:d} has a recording stored in GCS"))
def interview_with_recording(db: Session, interview_id: int, request):
    """Ensure interview has recording URL (already set in background)"""
    # Interview already created in background with recording URL


# When step definitions


@when(parsers.parse("they GET /api/orgs/{org_id:d}/studies/{study_id:d}/interviews"))
def get_study_interviews(request, client, org_id: int, study_id: int):
    """GET list of interviews for a study"""
    headers = getattr(request, "test_auth_headers", {})
    # Use org_id and study_id from URL parameters (not from stored values)
    # This allows testing cross-org access control
    # Note: client has base_url="http://testserver/api", so don't include /api prefix
    response = client.get(f"/orgs/{org_id}/studies/{study_id}/interviews", headers=headers)
    request.test_response = response


@when(
    parsers.parse("they GET /api/orgs/{org_id:d}/interviews/{interview_id:d}/artifacts/{filename}")
)
def get_interview_artifact(request, client, org_id: int, interview_id: int, filename: str):
    """GET artifact for an interview"""
    headers = getattr(request, "test_auth_headers", {})
    # Use org_id and interview_id from URL parameters (not from stored values)
    # This allows testing cross-org access control
    # Note: client has base_url="http://testserver/api", so don't include /api prefix
    response = client.get(
        f"/orgs/{org_id}/interviews/{interview_id}/artifacts/{filename}",
        headers=headers,
    )
    request.test_response = response


# Then step definitions


@then("the response contains a list of interviews")
def response_contains_interview_list(request):
    """Check response contains interview list"""
    response = request.test_response
    data = response.json()
    assert "interviews" in data
    assert isinstance(data["interviews"], list)


@then(parsers.parse('each interview has status "{expected_status}"'))
def each_interview_has_status(request, expected_status: str):
    """Check each interview has expected status"""
    response = request.test_response
    data = response.json()
    for interview in data["interviews"]:
        assert interview["status"] == expected_status


@then("each interview has transcript and recording flags")
def each_interview_has_artifact_flags(request):
    """Check each interview has has_transcript and has_recording flags"""
    response = request.test_response
    data = response.json()
    for interview in data["interviews"]:
        assert "has_transcript" in interview
        assert "has_recording" in interview
        assert isinstance(interview["has_transcript"], bool)
        assert isinstance(interview["has_recording"], bool)


@then(parsers.parse('the response content type is "{content_type}"'))
def response_content_type_is(request, content_type: str):
    """Check response content type"""
    response = request.test_response
    assert content_type in response.headers.get("content-type", "")


@then("the response body contains transcript text")
def response_contains_transcript_text(request):
    """Check response contains transcript text"""
    response = request.test_response
    # For now, just verify we got some text content
    assert len(response.content) > 0


@then("the response contains audio data")
def response_contains_audio_data(request):
    """Check response contains audio data"""
    response = request.test_response
    # For now, just verify we got some binary content
    assert len(response.content) > 0


@then(parsers.parse("the response contains {count:d} interview"))
def response_contains_count_interviews(request, count: int):
    """Check response contains expected number of interviews"""
    response = request.test_response
    data = response.json()
    assert len(data["interviews"]) == count


@then('all interviews have status "completed"')
def all_interviews_completed(request):
    """Check all interviews have completed status"""
    response = request.test_response
    data = response.json()
    for interview in data["interviews"]:
        assert interview["status"] == "completed"


@then(parsers.parse("the response status is {status_code:d}"))
def response_status_is(request, status_code: int):
    """Check response status code"""
    response = request.test_response
    assert response.status_code == status_code


@then(parsers.parse('the error message is "{expected_message}"'))
def error_message_is(request, expected_message: str):
    """Check error message"""
    response = request.test_response
    data = response.json()
    assert data["detail"] == expected_message


# Fixtures


@pytest.fixture
def db():
    """Database session fixture"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as session:
        yield session
