"""
Step definitions for interview data API tests (pipecat integration)
"""

import uuid
from datetime import UTC, datetime, timedelta

from pytest_bdd import given, scenarios, then, when
from src.models import Interview, InterviewGuide, Organization, Study

scenarios("../features/interview_data_api.feature")


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
    request.test_guide_content = guide.content_md


@given('an interview exists for the study with access_token and status "pending"')
def interview_exists_with_access_token(client, request):
    """Create an interview with access_token"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        study_id = getattr(request, "test_study_id", 1)

        # Create interview with access_token
        access_token = str(uuid.uuid4())
        interview = Interview(
            study_id=study_id,
            access_token=access_token,
            status="pending",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(interview)
        db_session.commit()
        db_session.refresh(interview)

        # Store access_token for later use
        request.test_access_token = access_token
        request.test_interview_id = interview.id

    finally:
        db_session.close()


# Given steps


@given('the interview status is "completed"')
def interview_status_is_completed(client, request):
    """Set interview status to completed"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        interview_id = getattr(request, "test_interview_id", None)
        if interview_id:
            interview = db_session.query(Interview).filter(Interview.id == interview_id).first()
            if interview:
                interview.status = "completed"
                interview.completed_at = datetime.now(UTC)
                db_session.commit()

    finally:
        db_session.close()


@given("the interview expires_at is in the past")
def interview_expires_at_is_past(client, request):
    """Set interview expires_at to past"""
    from tests.conftest import TestingSessionLocal

    db_session = TestingSessionLocal()
    try:
        interview_id = getattr(request, "test_interview_id", None)
        if interview_id:
            interview = db_session.query(Interview).filter(Interview.id == interview_id).first()
            if interview:
                # Set expires_at to 1 day ago
                interview.expires_at = datetime.now(UTC) - timedelta(days=1)
                db_session.commit()

    finally:
        db_session.close()


# When steps


@when("pipecat calls GET /interview/{access_token}")
def pipecat_calls_get_interview(request, client):
    """Pipecat calls GET /interview/{access_token}"""
    access_token = getattr(request, "test_access_token", "")
    response = client.get(f"/interview/{access_token}", follow_redirects=False)
    request.test_response = response


@when("pipecat calls GET /interview/invalid-token-12345")
def pipecat_calls_get_interview_with_invalid_token(request, client):
    """Pipecat calls GET /interview/ with invalid token"""
    response = client.get("/interview/invalid-token-12345", follow_redirects=False)
    request.test_response = response


# Then steps


@then("the response status is 200")
def response_status_is_200(request):
    """Check response status is 200"""
    response = request.test_response
    assert response.status_code == 200


@then("the response status is 410")
def response_status_is_410(request):
    """Check response status is 410 Gone"""
    response = request.test_response
    assert response.status_code == 410


@then("the response status is 404")
def response_status_is_404(request):
    """Check response status is 404"""
    response = request.test_response
    assert response.status_code == 404


@then('the response contains study title "Mobile Banking App Usability Study"')
def response_contains_study_title(request):
    """Check response contains study title"""
    response = request.test_response
    data = response.json()
    assert "study" in data
    assert data["study"]["title"] == "Mobile Banking App Usability Study"


@then("the response contains interview guide markdown content")
def response_contains_interview_guide(request):
    """Check response contains interview guide markdown"""
    response = request.test_response
    data = response.json()
    expected_content = getattr(request, "test_guide_content", "")
    assert "study" in data
    assert "interview_guide" in data["study"]
    assert data["study"]["interview_guide"]["content_md"] == expected_content


@then("the response contains the access_token")
def response_contains_access_token(request):
    """Check response contains access_token"""
    response = request.test_response
    data = response.json()
    expected_token = getattr(request, "test_access_token", "")
    assert "interview" in data
    assert data["interview"]["access_token"] == expected_token


@then('the response contains interview status "pending"')
def response_contains_status_pending(request):
    """Check response contains status pending"""
    response = request.test_response
    data = response.json()
    assert "interview" in data
    assert data["interview"]["status"] == "pending"


@then('the error message contains "Interview already completed"')
def error_message_contains_already_completed(request):
    """Check error message contains 'Interview already completed'"""
    response = request.test_response
    data = response.json()
    assert "detail" in data
    assert "Interview already completed" in data["detail"]


@then('the error message contains "Interview not found"')
def error_message_contains_interview_not_found(request):
    """Check error message contains 'Interview not found'"""
    response = request.test_response
    data = response.json()
    assert "detail" in data
    assert "Interview not found" in data["detail"]


@then('the error message contains "expired"')
def error_message_contains_expired(request):
    """Check error message contains 'expired'"""
    response = request.test_response
    data = response.json()
    assert "detail" in data
    assert "expired" in data["detail"].lower()
