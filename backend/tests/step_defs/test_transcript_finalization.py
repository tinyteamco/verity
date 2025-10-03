"""Step definitions for transcript finalization BDD tests."""

from contextlib import suppress
from typing import Any

from firebase_admin import auth
from pytest_bdd import given, parsers, scenarios, then, when
from src.models import Interview, Organization, Transcript, User
from tests.conftest import TestingSessionLocal

scenarios("../features/transcript_finalization.feature")


# Shared step definitions


@given("a test organization with ID 1 exists")
def create_test_organization(client: Any, super_admin_token: str, request: Any) -> None:
    """Create test organization for the scenarios."""
    headers = {"Authorization": f"Bearer {super_admin_token}"}

    # Use unique name per test to avoid conflicts
    org_name = f"Test Organization {hash(request.node.name) % 10000}"
    owner_email = f"owner@testorg{hash(request.node.name) % 10000}.com"
    response = client.post(
        "/orgs", json={"name": org_name, "owner_email": owner_email}, headers=headers
    )
    assert response.status_code == 201


@given(
    parsers.parse('a study with ID {study_id:d} titled "{title}" exists in organization {org_id:d}')
)
def create_test_study(
    client: Any, super_admin_token: str, study_id: int, title: str, org_id: int, request: Any
) -> None:
    """Create a test study with unique user for this test."""
    from tests.test_helpers import sign_in_user

    # Create unique user for this test
    temp_uid = get_unique_uid("temp-study-creator", request)
    temp_email = get_unique_email("temp-study-creator", request)
    temp_password = "testpass123"

    # Create user in Firebase
    with suppress(Exception):
        auth.create_user(
            uid=temp_uid,
            email=temp_email,
            password=temp_password,
            email_verified=True,
        )

    # Set custom claims
    auth.set_custom_user_claims(temp_uid, {"tenant": "organization"})

    # Create database user entry
    with TestingSessionLocal() as db:
        existing_user = db.query(User).filter(User.firebase_uid == temp_uid).first()
        if not existing_user:
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if not org:
                org = Organization(id=org_id, name="Test Organization")
                db.add(org)
                db.flush()

            user = User(
                firebase_uid=temp_uid,
                email=temp_email,
                role="owner",
                organization_id=org.id,
            )
            db.add(user)
            db.commit()

    # Sign in and create study
    token = sign_in_user(temp_email, temp_password)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/studies", json={"title": title}, headers=headers)
    assert response.status_code == 201


@given(
    parsers.parse('an interview with access_token "{access_token}" exists for study {study_id:d}')
)
def create_test_interview(access_token: str, study_id: int, request: Any) -> None:
    """Create a test interview with specific access token."""
    with TestingSessionLocal() as db:
        interview = Interview(
            study_id=study_id,
            access_token=access_token,
            status="pending",
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)

        # Store for later reference
        request.test_interview_id = interview.id


def get_unique_uid(prefix: str, request: Any) -> str:
    """Generate unique UID for each test."""
    test_name = request.node.name
    return f"{prefix}-{hash(test_name) % 10000}"


def get_unique_email(prefix: str, request: Any) -> str:
    """Generate unique email for each test."""
    test_name = request.node.name
    return f"{prefix}-{hash(test_name) % 10000}@example.com"


@given('a transcript exists for interview with access_token "abc123"')
def create_existing_transcript(request: Any) -> None:
    """Create a transcript for the test interview."""
    from src.models import Interview
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        # Find the interview by access token
        interview = db.query(Interview).filter(Interview.access_token == "abc123").first()
        assert interview, "Interview not found"

        # Create a transcript
        transcript = Transcript(
            interview_id=interview.id,
            language="en",
            source="client",
            full_text="Existing transcript text",
        )
        db.add(transcript)
        db.commit()


@when(
    parsers.parse(
        "I finalize the transcript for interview with access_token "
        '"{token}" with {num_segments:d} segment'
    )
)
@when(
    parsers.parse(
        "I finalize the transcript for interview with access_token "
        '"{token}" with {num_segments:d} segments'
    )
)
def finalize_transcript(client: Any, request: Any, token: str, num_segments: int) -> None:
    """Finalize transcript for an interview."""
    from src.models import Interview

    # Find interview by access token
    with TestingSessionLocal() as db:
        interview = db.query(Interview).filter(Interview.access_token == token).first()
        interview_id = interview.id if interview else 99999

    # Build segments based on num_segments
    segments = []
    for i in range(num_segments):
        segments.append(
            {"start_ms": i * 1000, "end_ms": (i + 1) * 1000, "text": f"This is segment {i + 1}."}
        )

    # Make request
    request_data = {"lang": "en", "source": "client", "segments": segments}

    response = client.post(f"/interviews/{interview_id}/transcript:finalize", json=request_data)

    # Store response for assertions
    request.response = response
    if response.status_code == 201:
        request.transcript_data = response.json()


@then("the response status is 201")
def check_status_201(request: Any) -> None:
    """Check that response status is 201."""
    assert request.response.status_code == 201


@then("the response status is 404")
def check_status_404(request: Any) -> None:
    """Check that response status is 404."""
    assert request.response.status_code == 404


@then("the response status is 400")
def check_status_400(request: Any) -> None:
    """Check that response status is 400."""
    assert request.response.status_code == 400


@then("the response contains transcript_id")
def check_transcript_id(request: Any) -> None:
    """Check that response contains transcript_id."""
    assert "transcript_id" in request.transcript_data
    assert request.transcript_data["transcript_id"]


@then(parsers.parse("the transcript has {count:d} segments"))
def check_segment_count(request: Any, count: int) -> None:
    """Check that transcript has correct number of segments."""
    transcript_id = int(request.transcript_data["transcript_id"])

    with TestingSessionLocal() as db:
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        assert transcript
        assert len(transcript.segments) == count


@then("the full_text contains all segment text concatenated")
def check_full_text(request: Any) -> None:
    """Check that full_text is properly concatenated."""
    full_text = request.transcript_data["full_text"]
    assert "This is segment 1." in full_text
    assert "This is segment 2." in full_text
    assert "This is segment 3." in full_text


@then("the transcript is created successfully")
def check_transcript_created(request: Any) -> None:
    """Check that transcript was created."""
    assert request.response.status_code == 201
    assert request.transcript_data
    assert "transcript_id" in request.transcript_data


@then(parsers.parse('the error message is "{message}"'))
def check_error_message(request: Any, message: str) -> None:
    """Check exact error message."""
    error_data = request.response.json()
    assert error_data.get("detail") == message


@then(parsers.parse('the error message contains "{text}"'))
def check_error_contains(request: Any, text: str) -> None:
    """Check that error message contains text."""
    error_data = request.response.json()
    assert text in error_data.get("detail", "")
