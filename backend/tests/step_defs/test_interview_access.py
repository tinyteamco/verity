"""
Step definitions for interview access tests
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when
from src.models import Interview, InterviewGuide, Organization, Study

scenarios("../features/interview_access.feature")


# Helper functions


def get_unique_slug(base_slug: str, request) -> str:
    """Generate unique slug for each test"""
    test_name = request.node.name
    return f"{base_slug}-{hash(test_name) % 10000}"


# Background steps


@given('a study exists with slug "mobile-banking-study" and has an interview guide')
def study_with_slug_and_guide(client, request):
    """Create a study with slug and interview guide"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()

    # Create organization first
    org_name = f"Test Organization {hash(request.node.name) % 10000}"
    org = Organization(
        name=org_name.lower().replace(" ", "-"),
        display_name=org_name,
        description="Test organization",
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    # Create study with unique slug
    unique_slug = get_unique_slug("mobile-banking-study", request)
    study = Study(
        title="Mobile Banking App Usability Study",
        description="Test study",
        slug=unique_slug,
        participant_identity_flow="anonymous",
        organization_id=org.id,
    )
    db_session.add(study)
    db_session.commit()
    db_session.refresh(study)

    # Create interview guide
    guide = InterviewGuide(
        study_id=study.id,
        content_md="# Interview Guide\n\n## Learning Goals\n1. Understand user needs",
    )
    db_session.add(guide)
    db_session.commit()
    db_session.refresh(guide)

    # Store slug and study for use in tests
    request.test_study_slug = unique_slug
    request.test_study_id = study.id
    request.test_org_id = org.id


# Scenario steps


def _get_public_client(client) -> TestClient:
    """Get a test client for public endpoints (no /api prefix) with same DB session"""
    from src.api.main import app

    # The app already has the database override from the client fixture
    # Just create a new TestClient without base_url prefix
    return TestClient(app, base_url="http://testserver")


@when("a participant accesses GET /study/{slug}/start?pid=prolific_abc123")
def participant_accesses_link_with_pid(request, client):
    """Participant accesses reusable link with pid"""
    public_client = _get_public_client(client)
    slug = getattr(request, "test_study_slug", "mobile-banking-study")
    response = public_client.get(f"/study/{slug}/start?pid=prolific_abc123", follow_redirects=False)
    request.test_response = response


@when("a participant accesses GET /study/{slug}/start?pid=prolific_completed")
def participant_accesses_link_with_completed_pid(request, client):
    """Participant accesses reusable link with completed pid"""
    public_client = _get_public_client(client)
    slug = getattr(request, "test_study_slug", "mobile-banking-study")
    response = public_client.get(
        f"/study/{slug}/start?pid=prolific_completed", follow_redirects=False
    )
    request.test_response = response


@when("a participant accesses GET /study/{slug}/start")
def participant_accesses_link_without_pid(request, client):
    """Participant accesses reusable link without pid"""
    public_client = _get_public_client(client)
    slug = getattr(request, "test_study_slug", "mobile-banking-study")
    response = public_client.get(f"/study/{slug}/start", follow_redirects=False)
    request.test_response = response


@when("a participant accesses GET /study/non-existent-study/start")
def participant_accesses_nonexistent_slug(request, client):
    """Participant accesses non-existent study slug"""
    public_client = _get_public_client(client)
    # Use a truly random slug that won't exist
    nonexistent_slug = f"nonexistent-{uuid.uuid4()}"
    response = public_client.get(f"/study/{nonexistent_slug}/start", follow_redirects=False)
    request.test_response = response


@given('an interview already exists for study "mobile-banking-study" with pid "prolific_abc123"')
def interview_exists_with_pid(client, request):
    """Create an interview with pid"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        study_id = getattr(request, "test_study_id", 1)

        # Create interview with external_participant_id
        interview = Interview(
            study_id=study_id,
            access_token=str(uuid.uuid4()),
            status="pending",
            external_participant_id="prolific_abc123",
            platform_source="prolific",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(interview)
        db_session.commit()
        db_session.refresh(interview)

        # Store interview for later checks
        request.test_existing_interview_id = interview.id
        request.test_existing_access_token = interview.access_token
        request.initial_interview_count = (
            db_session.query(Interview).filter(Interview.study_id == study_id).count()
        )

    finally:
        db_session.close()


# Then steps


@then("the response is a 302 redirect")
def response_is_302_redirect(request):
    """Check response is a 302 redirect"""
    response = request.test_response
    assert response.status_code == 302


@then('the redirect Location header contains "access_token="')
def redirect_contains_access_token(request):
    """Check redirect Location header contains access_token"""
    response = request.test_response
    location = response.headers.get("Location", "")
    assert "access_token=" in location


@then('the redirect Location header contains "verity_api="')
def redirect_contains_verity_api(request):
    """Check redirect Location header contains verity_api"""
    response = request.test_response
    location = response.headers.get("Location", "")
    assert "verity_api=" in location


@then('an interview is created with external_participant_id "prolific_abc123"')
def interview_created_with_pid(client, request):
    """Check interview was created with external_participant_id"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        study_id = getattr(request, "test_study_id", 1)

        # Find the interview created by this request
        interview = (
            db_session.query(Interview)
            .filter(
                Interview.study_id == study_id,
                Interview.external_participant_id == "prolific_abc123",
            )
            .first()
        )

        assert interview is not None
        assert interview.external_participant_id == "prolific_abc123"

        # Store interview for further assertions
        request.test_created_interview_id = interview.id

    finally:
        db_session.close()


@then('the interview platform_source is "prolific"')
def interview_platform_source_is_prolific(client, request):
    """Check interview platform_source is prolific"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        interview_id = getattr(request, "test_created_interview_id", None)
        if interview_id:
            interview = db_session.query(Interview).filter(Interview.id == interview_id).first()
            assert interview is not None
            assert interview.platform_source == "prolific"

    finally:
        db_session.close()


@then("an interview is created with external_participant_id null")
def interview_created_without_pid(client, request):
    """Check interview was created without external_participant_id"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        # Extract access_token from redirect Location header
        response = request.test_response
        location = response.headers.get("Location", "")

        # Parse access_token from URL
        access_token = None
        if "access_token=" in location:
            token_part = location.split("access_token=")[1]
            access_token = token_part.split("&")[0] if "&" in token_part else token_part

        assert access_token is not None

        # Find the interview by access_token
        interview = (
            db_session.query(Interview).filter(Interview.access_token == access_token).first()
        )

        assert interview is not None
        assert interview.external_participant_id is None

    finally:
        db_session.close()


@then("no new interview is created")
def no_new_interview_created(client, request):
    """Check no new interview was created"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        study_id = getattr(request, "test_study_id", 1)
        initial_count = getattr(request, "initial_interview_count", 0)

        # Count interviews for the study
        current_count = db_session.query(Interview).filter(Interview.study_id == study_id).count()

        assert current_count == initial_count

    finally:
        db_session.close()


@then("the redirect uses the existing interview access_token")
def redirect_uses_existing_token(request):
    """Check redirect uses existing interview access_token"""
    response = request.test_response
    location = response.headers.get("Location", "")
    existing_token = getattr(request, "test_existing_access_token", "")

    assert existing_token in location


@then("the response status is 404")
def response_status_is_404(request):
    """Check response status is 404"""
    response = request.test_response
    assert response.status_code == 404


@then("the response status is 400")
def response_status_is_400(request):
    """Check response status is 400"""
    response = request.test_response
    assert response.status_code == 400


@then('the error message contains "Study not found"')
def error_message_contains_study_not_found(request):
    """Check error message contains 'Study not found'"""
    response = request.test_response
    data = response.json()
    assert "Study not found" in data["detail"]


# Fixtures


@given(
    'an interview already exists for study "mobile-banking-study" '
    'with pid "prolific_completed" and status "completed"'
)
def interview_exists_with_completed_status(client, request):
    """Create a completed interview with pid"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        study_id = getattr(request, "test_study_id", 1)

        # Create completed interview with external_participant_id
        interview = Interview(
            study_id=study_id,
            access_token=str(uuid.uuid4()),
            status="completed",
            external_participant_id="prolific_completed",
            platform_source="prolific",
            expires_at=datetime.now(UTC) + timedelta(days=7),
            completed_at=datetime.now(UTC),
        )
        db_session.add(interview)
        db_session.commit()
        db_session.refresh(interview)

        # Store interview for later checks
        request.test_existing_interview_id = interview.id
        request.test_existing_access_token = interview.access_token

    finally:
        db_session.close()


@when("a participant accesses GET /interview/invalid-token-12345")
def participant_accesses_invalid_interview_token(request, client):
    """Participant accesses interview with invalid token"""
    response = client.get("/api/interview/invalid-token-12345", follow_redirects=False)
    request.test_response = response


@then("the response is HTML content")
def response_is_html_content(request):
    """Check response is HTML content"""
    response = request.test_response
    content_type = response.headers.get("Content-Type", "")
    assert "text/html" in content_type


@then('the error page contains "Interview Already Completed"')
def error_page_contains_already_completed(request):
    """Check error page contains 'Interview Already Completed'"""
    response = request.test_response
    assert "Interview Already Completed" in response.text


@then('the error page contains "Interview Not Found"')
def error_page_contains_not_found(request):
    """Check error page contains 'Interview Not Found'"""
    response = request.test_response
    assert "Interview Not Found" in response.text
