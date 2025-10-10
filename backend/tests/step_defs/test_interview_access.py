"""
Step definitions for interview access tests
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pytest_bdd import given, scenarios, then, when
from sqlalchemy.orm import Session
from src.models import Interview, InterviewGuide, Organization, Study

scenarios("../features/interview_access.feature")


# Helper functions


def get_unique_slug(base_slug: str, request) -> str:
    """Generate unique slug for each test"""
    test_name = request.node.name
    return f"{base_slug}-{hash(test_name) % 10000}"


# Background steps


@given('a study exists with slug "mobile-banking-study" and has an interview guide')
def study_with_slug_and_guide(db: Session, request):
    """Create a study with slug and interview guide"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
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

    finally:
        db_session.close()


# Scenario steps


@when("a participant accesses GET /study/{slug}/start?pid=prolific_abc123")
def participant_accesses_link_with_pid(request, client):
    """Participant accesses reusable link with pid"""
    slug = getattr(request, "test_study_slug", "mobile-banking-study")
    response = client.get(f"/study/{slug}/start?pid=prolific_abc123", follow_redirects=False)
    request.test_response = response


@when("a participant accesses GET /study/{slug}/start")
def participant_accesses_link_without_pid(request, client):
    """Participant accesses reusable link without pid"""
    slug = getattr(request, "test_study_slug", "mobile-banking-study")
    response = client.get(f"/study/{slug}/start", follow_redirects=False)
    request.test_response = response


@when("a participant accesses GET /study/non-existent-study/start")
def participant_accesses_nonexistent_slug(request, client):
    """Participant accesses non-existent study slug"""
    # Use a truly random slug that won't exist
    nonexistent_slug = f"nonexistent-{uuid.uuid4()}"
    response = client.get(f"/study/{nonexistent_slug}/start", follow_redirects=False)
    request.test_response = response


@given('an interview already exists for study "mobile-banking-study" with pid "prolific_abc123"')
def interview_exists_with_pid(request, db: Session):
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
def interview_created_with_pid(request, db: Session):
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
def interview_platform_source_is_prolific(request, db: Session):
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
def interview_created_without_pid(request, db: Session):
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
def no_new_interview_created(request, db: Session):
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


@then('the error message contains "Study not found"')
def error_message_contains_study_not_found(request):
    """Check error message contains 'Study not found'"""
    response = request.test_response
    data = response.json()
    assert "Study not found" in data["detail"]


# Fixtures


@pytest.fixture
def db():
    """Database session fixture"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as session:
        yield session
