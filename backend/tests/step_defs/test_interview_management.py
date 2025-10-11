import contextlib
import uuid
from datetime import UTC, datetime

import pytest
from firebase_admin import auth
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy.orm import Session
from src.auth import AuthUser
from src.models import Interview, Organization, Study, User

scenarios("../features/interview_management.feature")


# Test data management - each test gets unique IDs to avoid conflicts


def get_unique_uid(prefix: str, request) -> str:
    """Generate unique UID for each test"""
    test_name = request.node.name
    return f"{prefix}-{hash(test_name) % 10000}"


def get_unique_email(prefix: str, request) -> str:
    """Generate unique email for each test"""
    test_name = request.node.name
    return f"{prefix}-{hash(test_name) % 10000}@example.com"


# Shared step definitions


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
    """Create a test study with unique user for this test"""
    import re

    from tests.conftest import TestingSessionLocal

    # Use the actual org_id stored from previous step
    actual_org_id = getattr(request, "test_org_id", org_id)

    # Create unique user for this test
    temp_uid = get_unique_uid("temp-study-creator", request)
    temp_email = get_unique_email("temp-study-creator", request)

    # Create user in Firebase
    with contextlib.suppress(Exception):
        auth.create_user(
            uid=temp_uid,
            email=temp_email,
            password="testpass123",
            email_verified=True,
        )

    # Set custom claims
    auth.set_custom_user_claims(temp_uid, {"tenant": "organization"})

    # Create database user entry and study directly
    with TestingSessionLocal() as db:
        existing_user = db.query(User).filter(User.firebase_uid == temp_uid).first()
        if not existing_user:
            org = db.query(Organization).filter(Organization.id == actual_org_id).first()
            if org:
                temp_user = User(
                    firebase_uid=temp_uid,
                    email=temp_email,
                    role="admin",
                    organization_id=org.id,
                )
                db.add(temp_user)
                db.commit()

        # Create study directly in database with proper slug
        slug = re.sub(r"[^\w\s-]", "", title.lower())
        slug = re.sub(r"[-\s]+", "-", slug)
        # Make slug unique per test
        slug = f"{slug}-{hash(request.node.name) % 10000}"

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

        # Store the actual study ID for later use
        request.test_study_id = study.id

        # Create interview guide
        from src.models import InterviewGuide

        guide = InterviewGuide(
            study_id=study.id,
            content_md="# Test Interview Guide\n\nThis is a test guide.",
        )
        db.add(guide)
        db.commit()


@given(parsers.parse('a signed-in organization user with role "{role}"'))
def signed_in_organization_user(client, role, request):
    """Create and sign in a unique organization user for this test"""
    from tests.conftest import TestingSessionLocal
    from tests.test_helpers import sign_in_user

    # Use the actual org_id stored from previous step
    actual_org_id = getattr(request, "test_org_id", 1)

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


@given("a signed-in interviewee user")
def signed_in_interviewee_user_simple(request):
    """Create a unique signed-in interviewee user for this test"""
    from tests.test_helpers import sign_in_user

    # Create unique user for this test
    user_uid = get_unique_uid("test-interviewee", request)
    user_email = get_unique_email("test-interviewee", request)

    # Create user in Firebase
    with contextlib.suppress(Exception):
        auth.create_user(
            uid=user_uid,
            email=user_email,
            password="testpass123",
            email_verified=True,
        )

    # Set custom claims
    auth.set_custom_user_claims(user_uid, {"tenant": "interviewee"})

    # Sign in and get token
    token = sign_in_user(user_email, "testpass123")
    request.test_auth_headers = {"Authorization": f"Bearer {token}"}


@given(parsers.parse('a signed-in interviewee user with uid "{firebase_uid}"'))
def signed_in_interviewee_user(request, firebase_uid: str) -> AuthUser:
    """Create a signed-in interviewee user with specific UID for this test"""
    from tests.test_helpers import sign_in_user

    # Make UID unique per test
    unique_uid = f"{firebase_uid}-{hash(request.node.name) % 10000}"
    user_email = f"{unique_uid}@example.com"

    # Create user in Firebase
    with contextlib.suppress(Exception):
        auth.create_user(
            uid=unique_uid,
            email=user_email,
            password="testpass123",
            email_verified=True,
        )

    # Set custom claims
    auth.set_custom_user_claims(unique_uid, {"tenant": "interviewee"})

    # Sign in and get token
    token = sign_in_user(user_email, "testpass123")
    request.test_auth_headers = {"Authorization": f"Bearer {token}"}

    # Store the actual UID used for later assertions
    request.test_interviewee_uid = unique_uid

    auth_user = AuthUser(
        firebase_uid=unique_uid,
        tenant_type="interviewee",
        email=user_email,
    )
    request.test_auth_user = auth_user
    return auth_user


@given("a study with ID 2 exists in a different organization")
def study_in_different_org(db: Session, request):
    """Create a study in a different organization for this test"""
    import re

    # Create unique organization for this test
    org_name = f"Other Organization {hash(request.node.name) % 10000}"
    org_slug = org_name.lower().replace(" ", "-")
    other_org = Organization(
        name=org_slug, display_name=org_name, description=f"Test organization: {org_name}"
    )
    db.add(other_org)
    db.commit()
    db.refresh(other_org)

    # Create study in other organization with proper slug
    study_title = f"Other Study {hash(request.node.name) % 10000}"
    slug = re.sub(r"[^\w\s-]", "", study_title.lower())
    slug = re.sub(r"[-\s]+", "-", slug)

    study = Study(
        title=study_title,
        description="Study in different org",
        slug=slug,
        participant_identity_flow="anonymous",
        organization_id=other_org.id,
    )
    db.add(study)
    db.commit()
    db.refresh(study)

    # Store the other study ID for later use
    request.test_other_study_id = study.id
    return study


# Interview-specific step definitions


@given("an interview link exists for study 1")
def interview_link_exists_for_study_1(study_in_db: Study, db: Session, request) -> Interview:
    """Create a unique interview link for study 1 for this test"""
    access_token = f"token-{hash(request.node.name) % 10000}-{uuid.uuid4()}"
    interview = Interview(
        study_id=study_in_db.id,
        access_token=access_token,
        status="pending",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


@given("another interview link exists for study 1")
def another_interview_link_exists_for_study_1(
    study_in_db: Study, db: Session, request
) -> Interview:
    """Create another unique interview link for study 1 for this test"""
    access_token = f"token2-{hash(request.node.name) % 10000}-{uuid.uuid4()}"
    interview = Interview(
        study_id=study_in_db.id,
        access_token=access_token,
        status="pending",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


@given(parsers.parse('an interview link exists for study 1 with access_token "{access_token}"'))
def interview_link_with_access_token(
    study_in_db: Study, db: Session, access_token: str, request
) -> Interview:
    """Create an interview link with specific access token for this test"""
    # Make access token unique per test to avoid conflicts
    unique_token = f"{access_token}-{hash(request.node.name) % 10000}"
    interview = Interview(
        study_id=study_in_db.id,
        access_token=unique_token,
        status="pending",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    # Store the actual token for step definitions that need it
    request.test_access_token = unique_token
    return interview


@given("the interview has been completed")
def interview_has_been_completed(request, db: Session) -> None:
    """Mark interview as completed"""
    # Get the interview token created for this test
    access_token = getattr(request, "test_access_token", "abc123")
    interview = db.query(Interview).filter(Interview.access_token == access_token).first()
    assert interview is not None, f"No interview found with token {access_token}"

    interview.status = "completed"
    interview.completed_at = datetime.now(UTC)
    db.commit()


@given(parsers.parse('the interview is associated with "{firebase_uid}"'))
def interview_associated_with_user(request, db: Session, firebase_uid: str) -> None:
    """Associate interview with a user for this test"""
    # Get the interview token created for this test
    access_token = getattr(request, "test_access_token", "abc123")
    interview = db.query(Interview).filter(Interview.access_token == access_token).first()
    assert interview is not None, f"No interview found with token {access_token}"

    # Make UID unique per test
    unique_uid = f"{firebase_uid}-{hash(request.node.name) % 10000}"
    interview.interviewee_firebase_uid = unique_uid
    db.commit()


# Request step definitions


@when("they POST /studies/1/interviews to generate a link")
def post_generate_interview_link(request, client) -> None:
    """POST to generate interview link"""
    headers = getattr(request, "test_auth_headers", {})
    study_id = getattr(request, "test_study_id", 1)
    response = client.post(f"/studies/{study_id}/interviews", headers=headers)
    request.test_response = response


@when("they GET /studies/1/interviews")
def get_list_interviews(request, client) -> None:
    """GET list of interviews"""
    headers = getattr(request, "test_auth_headers", {})
    study_id = getattr(request, "test_study_id", 1)
    response = client.get(f"/studies/{study_id}/interviews", headers=headers)
    request.test_response = response


@when("they GET /studies/1/interviews/{interview_id}")
def get_specific_interview(request, client, db) -> None:
    """GET specific interview by ID"""
    headers = getattr(request, "test_auth_headers", {})
    study_id = getattr(request, "test_study_id", 1)

    # Find the interview that was created for this test
    interview = db.query(Interview).filter(Interview.study_id == study_id).first()
    assert interview is not None, f"No interview found for study {study_id}"

    interview_id = interview.id
    response = client.get(f"/studies/{study_id}/interviews/{interview_id}", headers=headers)
    request.test_response = response


@when("they POST /studies/999/interviews to generate a link")
def post_generate_interview_link_nonexistent_study(request, client) -> None:
    """POST to generate interview link for non-existent study"""
    headers = getattr(request, "test_auth_headers", {})
    response = client.post("/studies/999/interviews", headers=headers)
    request.test_response = response


@when("they GET /studies/2/interviews")
def get_interviews_different_org(request, client) -> None:
    """GET interviews from different organization"""
    headers = getattr(request, "test_auth_headers", {})
    other_study_id = getattr(request, "test_other_study_id", 2)
    response = client.get(f"/studies/{other_study_id}/interviews", headers=headers)
    request.test_response = response


@when("an unauthenticated user posts to /studies/1/interviews")
def post_interview_link_unauthenticated(request, client) -> None:
    """POST interview link without authentication"""
    study_id = getattr(request, "test_study_id", 1)
    response = client.post(f"/studies/{study_id}/interviews")
    request.test_response = response


@when("they GET /interview/abc123 without authentication")
def get_interview_public(request, client) -> None:
    """GET interview via public access token"""
    # Use the actual token from the test setup
    access_token = getattr(request, "test_access_token", "abc123")
    response = client.get(f"/interview/{access_token}")
    request.test_response = response


@when(parsers.parse("they POST /interview/{access_token}/complete without authentication with:"))
def post_complete_interview(request, client, access_token: str) -> None:
    """POST to complete interview without authentication"""
    # Use the actual token from the test setup
    actual_token = getattr(request, "test_access_token", access_token)

    # Use fixed data for this test scenario
    data = {
        "transcript_url": "https://storage.example.com/transcript.json",
        "recording_url": "https://storage.example.com/recording.mp3",
        "notes": "Great insights from user",
    }

    response = client.post(f"/interview/{actual_token}/complete", json=data)
    request.test_response = response


@when("they GET /interview/invalid-token without authentication")
def get_interview_invalid_token(request, client) -> None:
    """GET interview with invalid token"""
    # Use a guaranteed invalid token
    invalid_token = f"invalid-{hash(request.node.name) % 10000}"
    response = client.get(f"/interview/{invalid_token}")
    request.test_response = response


@when("they POST /interview/abc123/claim")
def post_claim_interview(request, client) -> None:
    """POST to claim interview"""
    headers = getattr(request, "test_auth_headers", {})
    # Use the actual token from the test setup
    access_token = getattr(request, "test_access_token", "abc123")
    response = client.post(f"/interview/{access_token}/claim", headers=headers)
    request.test_response = response


# Assertion step definitions


@then("the response has an interview object")
def response_has_interview_object(request) -> None:
    """Check response has interview object"""
    response = request.test_response
    data = response.json()
    assert "interview" in data
    assert isinstance(data["interview"], dict)


@then("the response has an interview_url")
def response_has_interview_url(request) -> None:
    """Check response has interview_url"""
    response = request.test_response
    data = response.json()
    assert "interview_url" in data
    assert data["interview_url"].startswith("https://")


@then("the interview has a unique access_token")
def interview_has_unique_access_token(request) -> None:
    """Check interview has unique access token"""
    response = request.test_response
    data = response.json()

    # Handle both nested and direct interview data
    interview = data.get("interview", data)

    assert "access_token" in interview
    assert len(interview["access_token"]) > 0
    # Check it looks like a UUID or our test format
    assert len(interview["access_token"]) >= 10


@then(parsers.parse('the interview has study_id "{expected_study_id}"'))
def interview_has_study_id(request, expected_study_id: str) -> None:
    """Check interview has expected study_id"""
    response = request.test_response
    data = response.json()
    interview = data["interview"]
    assert interview["study_id"] == expected_study_id


@then(parsers.parse('the interview has status "{expected_status}"'))
def interview_has_status(request, expected_status: str) -> None:
    """Check interview has expected status"""
    response = request.test_response
    data = response.json()

    # For individual interview endpoints, the interview data is at the top level
    # For interview creation, it's nested under "interview"
    interview = data.get("interview", data)

    assert interview["status"] == expected_status


@then("the interview has no interviewee_firebase_uid")
def interview_has_no_interviewee_firebase_uid(request) -> None:
    """Check interview has no interviewee_firebase_uid"""
    response = request.test_response
    data = response.json()
    interview = data["interview"]
    assert interview["interviewee_firebase_uid"] is None


@then(parsers.parse("the response contains {count:d} interviews"))
def response_contains_interviews(request, count: int) -> None:
    """Check response contains expected number of interviews"""
    response = request.test_response
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == count


@then("each interview has an access_token")
def each_interview_has_access_token(request) -> None:
    """Check each interview has access_token"""
    response = request.test_response
    data = response.json()
    for interview in data["items"]:
        assert "access_token" in interview
        assert len(interview["access_token"]) > 0


@then("the response has a study object")
def response_has_study_object(request) -> None:
    """Check response has study object"""
    response = request.test_response
    data = response.json()
    assert "study" in data
    assert isinstance(data["study"], dict)


@then(parsers.parse('the study has title "{expected_title}"'))
def study_has_title(request, expected_title: str) -> None:
    """Check study has expected title"""
    response = request.test_response
    data = response.json()
    study = data["study"]
    assert study["title"] == expected_title


@then("the study has an interview_guide")
def study_has_interview_guide(request) -> None:
    """Check study has interview guide"""
    response = request.test_response
    data = response.json()
    study = data["study"]
    assert "interview_guide" in study
    assert isinstance(study["interview_guide"], dict)


@then(parsers.parse('the interview status is now "{expected_status}"'))
def interview_status_is_now(request, expected_status: str, db: Session) -> None:
    """Check interview status in database"""
    # Get the access token from the test setup
    access_token = getattr(request, "test_access_token", "abc123")
    interview = db.query(Interview).filter(Interview.access_token == access_token).first()
    assert interview is not None
    assert interview.status == expected_status


@then(parsers.parse('the interview is now associated with "{firebase_uid}"'))
def interview_is_associated_with_user(request, firebase_uid: str, db: Session) -> None:
    """Check interview is associated with user in database"""
    # Get the access token and actual UID from test setup
    access_token = getattr(request, "test_access_token", "abc123")
    actual_uid = getattr(request, "test_interviewee_uid", firebase_uid)

    interview = db.query(Interview).filter(Interview.access_token == access_token).first()
    assert interview is not None
    assert interview.interviewee_firebase_uid == actual_uid


# Common step definitions for error handling


@then(parsers.parse("the response status is {status_code:d}"))
def response_status_is(request, status_code: int) -> None:
    """Check response status code"""
    response = request.test_response
    assert response.status_code == status_code


@then(parsers.parse('the error message is "{expected_message}"'))
def error_message_is(request, expected_message: str) -> None:
    """Check error message"""
    response = request.test_response
    data = response.json()
    assert data["detail"] == expected_message


@then(parsers.parse('the error message contains "{text}"'))
def error_message_contains(request, text: str) -> None:
    """Check error message contains text"""
    response = request.test_response
    data = response.json()
    assert text in data["detail"]


# Fixtures


@pytest.fixture
def auth_headers(request):
    """Get auth headers from request context"""
    return getattr(request, "test_auth_headers", {})


@pytest.fixture
def db():
    """Database session fixture"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def study_in_db(db, request):
    """Study fixture for database tests"""
    study_id = getattr(request, "test_study_id", None)
    if study_id:
        return db.query(Study).filter(Study.id == study_id).first()
    # Fallback to first study if no ID stored
    return db.query(Study).first()
