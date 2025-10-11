import uuid
from datetime import UTC, datetime

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from src.models import Interview, InterviewGuide, Organization, Study

scenarios("../features/interview_completion.feature")


# Helper functions


def get_unique_uid(prefix: str, request) -> str:
    """Generate unique UID for each test"""
    test_name = request.node.name
    return f"{prefix}-{hash(test_name) % 10000}"


def get_unique_email(prefix: str, request) -> str:
    """Generate unique email for each test"""
    test_name = request.node.name
    return f"{prefix}-{hash(test_name) % 10000}@example.com"


# Setup step definitions


@given("I am a super admin user")
def super_admin_user(super_admin_token, request):
    """Set up super admin user headers"""
    request.test_auth_headers = {"Authorization": f"Bearer {super_admin_token}"}


@given(parsers.parse('an organization exists with name "{name}" and display_name "{display_name}"'))
def organization_exists(client, request, name: str, display_name: str):
    """Create an organization"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        # Create unique organization for this test
        unique_name = f"{name}-{hash(request.node.name) % 10000}"

        org = Organization(
            name=unique_name,
            display_name=display_name,
            description="Test organization",
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        request.test_org_id = org.id


@given(parsers.parse('the organization has a study with title "{title}"'))
def organization_has_study(client, request, title: str):
    """Create a study in the organization"""
    import re

    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        org_id = request.test_org_id

        # Generate slug from title (same logic as LLM service)
        slug = re.sub(r"[^a-z0-9-]", "", title.lower().replace(" ", "-"))
        slug = re.sub(r"-+", "-", slug)  # Remove duplicate hyphens
        slug = slug.strip("-")  # Remove leading/trailing hyphens

        # Make slug unique per test
        unique_slug = f"{slug}-{hash(request.node.name) % 10000}"

        study = Study(
            title=title,
            description="Test study",
            slug=unique_slug,
            organization_id=org_id,
        )
        db.add(study)
        db.commit()
        db.refresh(study)
        request.test_study_id = study.id
        request.test_study_slug = study.slug


@given(parsers.parse('the study has an interview guide with content "{content}"'))
def study_has_interview_guide(request, content: str):
    """Create an interview guide for the study"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        study_id = request.test_study_id
        guide = InterviewGuide(
            study_id=study_id,
            content_md=content,
        )
        db.add(guide)
        db.commit()


@given(
    parsers.parse(
        'the study has a pending interview with external_participant_id "{external_participant_id}"'
    )
)
def study_has_pending_interview(request, external_participant_id: str):
    """Create a pending interview for the study"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        study_id = request.test_study_id
        access_token = str(uuid.uuid4())
        interview = Interview(
            study_id=study_id,
            access_token=access_token,
            status="pending",
            external_participant_id=external_participant_id,
            platform_source="prolific",
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)
        request.test_access_token = access_token
        request.test_interview_id = interview.id


@given("I have the access token for the pending interview")
def have_access_token(request):
    """Store access token for use in subsequent steps"""
    # Access token already stored in request.test_access_token by previous step
    assert hasattr(request, "test_access_token"), "No access token found in test context"


@given(parsers.parse("I have completed the interview with:"))
def have_completed_interview(request, datatable):
    """Complete the interview with initial data"""
    from tests.conftest import TestingSessionLocal

    # Parse datatable into dict (datatable is a list of lists: [['key', 'value'], ...])
    data = {}
    for row in datatable:
        if isinstance(row, list) and len(row) == 2:
            key, value = row
            data[key] = value

    with TestingSessionLocal() as db:
        access_token = request.test_access_token
        interview = db.query(Interview).filter(Interview.access_token == access_token).first()
        assert interview is not None, f"No interview found with token {access_token}"

        interview.status = "completed"
        interview.completed_at = datetime.now(UTC)
        interview.transcript_url = data.get("transcript_url")
        interview.recording_url = data.get("recording_url")
        interview.notes = data.get("notes")
        db.commit()


# Action step definitions


@when(parsers.parse('I POST to "/api/interview/{{access_token}}/complete" with:'))
def post_complete_interview(request, client, datatable):
    """POST to complete interview endpoint"""
    access_token = request.test_access_token

    # Parse datatable into dict (datatable is a list of lists: [['key', 'value'], ...])
    data = {}
    for row in datatable:
        if isinstance(row, list) and len(row) == 2:
            key, value = row
            data[key] = value

    # Note: client has base_url="http://testserver/api", so we don't include /api prefix
    url = f"/interview/{access_token}/complete"
    response = client.post(url, json=data)
    request.test_response = response


# Assertion step definitions


@then(parsers.parse("the response status code should be {status_code:d}"))
def response_status_code_should_be(request, status_code: int):
    """Check response status code"""
    response = request.test_response
    assert response.status_code == status_code, (
        f"Expected status {status_code}, got {response.status_code}. Response: {response.text}"
    )


@then(parsers.parse('the response should contain "{key}"'))
def response_should_contain(request, key: str):
    """Check response contains key"""
    response = request.test_response
    data = response.json()
    assert key in data, f"Expected key '{key}' not found in response: {data}"


@then(parsers.parse('the interview status should be "{expected_status}"'))
def interview_status_should_be(request, expected_status: str):
    """Check interview status in database"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        access_token = request.test_access_token
        interview = db.query(Interview).filter(Interview.access_token == access_token).first()
        assert interview is not None, f"No interview found with token {access_token}"
        assert interview.status == expected_status, (
            f"Expected status '{expected_status}', got '{interview.status}'"
        )


@then("the interview completed_at should be set")
def interview_completed_at_should_be_set(request):
    """Check interview completed_at is set"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        access_token = request.test_access_token
        interview = db.query(Interview).filter(Interview.access_token == access_token).first()
        assert interview is not None, f"No interview found with token {access_token}"
        assert interview.completed_at is not None, "Expected completed_at to be set"


@then(parsers.parse('the interview transcript_url should be "{expected_url}"'))
def interview_transcript_url_should_be(request, expected_url: str):
    """Check interview transcript_url"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        access_token = request.test_access_token
        interview = db.query(Interview).filter(Interview.access_token == access_token).first()
        assert interview is not None, f"No interview found with token {access_token}"
        assert interview.transcript_url == expected_url, (
            f"Expected transcript_url '{expected_url}', got '{interview.transcript_url}'"
        )


@then(parsers.parse('the interview recording_url should be "{expected_url}"'))
def interview_recording_url_should_be(request, expected_url: str):
    """Check interview recording_url"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        access_token = request.test_access_token
        interview = db.query(Interview).filter(Interview.access_token == access_token).first()
        assert interview is not None, f"No interview found with token {access_token}"
        assert interview.recording_url == expected_url, (
            f"Expected recording_url '{expected_url}', got '{interview.recording_url}'"
        )


@then("the interview recording_url should be None")
def interview_recording_url_should_be_none(request):
    """Check interview recording_url is None"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        access_token = request.test_access_token
        interview = db.query(Interview).filter(Interview.access_token == access_token).first()
        assert interview is not None, f"No interview found with token {access_token}"
        assert interview.recording_url is None, (
            f"Expected recording_url to be None, got '{interview.recording_url}'"
        )


@then(parsers.parse('the interview notes should be "{expected_notes}"'))
def interview_notes_should_be(request, expected_notes: str):
    """Check interview notes"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        access_token = request.test_access_token
        interview = db.query(Interview).filter(Interview.access_token == access_token).first()
        assert interview is not None, f"No interview found with token {access_token}"
        assert interview.notes == expected_notes, (
            f"Expected notes '{expected_notes}', got '{interview.notes}'"
        )


# Fixtures


@pytest.fixture
def db():
    """Database session fixture"""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as session:
        yield session
