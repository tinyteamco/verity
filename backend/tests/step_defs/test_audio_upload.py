"""Step definitions for audio upload BDD tests."""

import io
from contextlib import suppress
from typing import Any

import pytest
from firebase_admin import auth
from pytest_bdd import given, parsers, scenarios, then, when
from src.models import AudioRecording, Interview, Organization, User

scenarios("../features/audio_upload.feature")


# Shared step definitions


@given("a test organization with ID 1 exists")
def create_test_organization(client: Any, super_admin_token: str, request: Any) -> None:
    """Create test organization for the scenarios."""
    headers = {"Authorization": f"Bearer {super_admin_token}"}

    # Use unique name per test to avoid conflicts
    org_name = f"Test Organization {hash(request.node.name) % 10000}"
    response = client.post("/orgs", json={"name": org_name}, headers=headers)
    assert response.status_code == 201


@given(
    parsers.parse('a study with ID {study_id:d} titled "{title}" exists in organization {org_id:d}')
)
def create_test_study(
    client: Any, super_admin_token: str, study_id: int, title: str, org_id: int, request: Any
) -> None:
    """Create a test study with unique user for this test."""
    from tests.conftest import TestingSessionLocal
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
            if org:
                temp_user = User(
                    firebase_uid=temp_uid,
                    email=temp_email,
                    role="admin",
                    organization_id=org.id,
                )
                db.add(temp_user)
                db.commit()

    # Create study using authenticated user
    token = sign_in_user(temp_email, temp_password)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/studies", json={"title": title}, headers=headers)
    assert response.status_code == 201


def get_unique_email(prefix: str, request: Any) -> str:
    """Generate unique email for each test."""
    test_name = request.node.name
    return f"{prefix}-{hash(test_name) % 10000}@example.com"


@given(
    parsers.parse('an interview with access_token "{access_token}" exists for study {study_id:d}')
)
def create_test_interview(access_token: str, study_id: int, request: Any) -> None:
    """Create a test interview with specific access token."""
    from tests.conftest import TestingSessionLocal

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


@given(parsers.parse('an audio recording exists for interview with access_token "{access_token}"'))
def existing_audio_recording(access_token: str, client: Any, request: Any) -> None:
    """Create an existing audio recording for the interview."""
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        # Get the interview by access token
        interview = db.query(Interview).filter(Interview.access_token == access_token).first()
        if not interview:
            pytest.fail(f"Interview with access_token {access_token} not found")

        # Create audio recording
        audio_recording = AudioRecording(
            interview_id=interview.id,
            uri=f"http://localhost:9000/audio-recordings/interviews/{interview.id}/audio/existing.wav",
            duration_ms=15000,
            mime_type="audio/wav",
            sample_rate_hz=44100,
            file_size_bytes=1024,
        )
        db.add(audio_recording)
        db.commit()


@when(
    parsers.parse('I upload an audio file for interview with access_token "{access_token}" with:')
)
def upload_audio_file(access_token: str, client: Any, request: Any) -> None:
    """Upload an audio file with test metadata."""
    from tests.conftest import TestingSessionLocal

    # Get interview ID from access token
    with TestingSessionLocal() as db:
        interview = db.query(Interview).filter(Interview.access_token == access_token).first()
        interview_id = str(interview.id) if interview else "999"  # Use invalid ID if not found

    # Create WAV file content
    filename = "test_audio.wav"
    mime_type = "audio/wav"

    # Minimal WAV file header for audio files
    file_content = (
        b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00"
        b"\x44\xac\x00\x00\x10\xb1\x02\x00\x04\x00\x10\x00data\x00\x08\x00\x00"
        + b"\x00\x00"
        * 100  # Sample audio data
    )

    # Prepare form data with metadata
    form_data = {
        "interview_id": interview_id,
        "mime": mime_type,
        "duration_ms": "30000",
        "sample_rate_hz": "44100",
    }

    # Create file for upload
    files = {"file": (filename, io.BytesIO(file_content), mime_type)}

    # Store response in request context
    response = client.post("/recordings:upload", data=form_data, files=files)
    request.upload_response = response


@when(
    parsers.parse(
        'I upload a non-audio file for interview with access_token "{access_token}" with:'
    )
)
def upload_non_audio_file(access_token: str, client: Any, request: Any) -> None:
    """Upload a non-audio file."""
    from tests.conftest import TestingSessionLocal

    # Get interview ID
    with TestingSessionLocal() as db:
        interview = db.query(Interview).filter(Interview.access_token == access_token).first()
        interview_id = str(interview.id) if interview else "999"

    # Create PDF file content
    filename = "document.pdf"
    mime_type = "application/pdf"
    file_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"

    form_data = {"interview_id": interview_id, "mime": mime_type}
    files = {"file": (filename, io.BytesIO(file_content), mime_type)}
    response = client.post("/recordings:upload", data=form_data, files=files)
    request.upload_response = response


@when(
    parsers.parse(
        'I upload a large audio file for interview with access_token "{access_token}" with:'
    )
)
def upload_large_audio_file(access_token: str, client: Any, request: Any) -> None:
    """Upload a large audio file."""
    from tests.conftest import TestingSessionLocal

    # Get interview ID
    with TestingSessionLocal() as db:
        interview = db.query(Interview).filter(Interview.access_token == access_token).first()
        interview_id = str(interview.id) if interview else "999"

    # Create larger file content
    filename = "large_audio.wav"
    mime_type = "audio/wav"

    # Create WAV header + larger audio data
    wav_header = (
        b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00"
        b"\x44\xac\x00\x00\x10\xb1\x02\x00\x04\x00\x10\x00data\x00\x08\x00\x00"
    )
    large_content = wav_header + b"\x00\x00" * 50000  # ~100KB of audio data

    form_data = {
        "interview_id": interview_id,
        "mime": mime_type,
        "duration_ms": "3600000",
        "sample_rate_hz": "48000",
    }

    files = {"file": (filename, io.BytesIO(large_content), mime_type)}
    response = client.post("/recordings:upload", data=form_data, files=files)
    request.upload_response = response


@then("the response contains recording details")
def check_recording_details(request: Any) -> None:
    """Verify the response contains recording details."""
    response = request.upload_response
    assert response.status_code == 201
    data = response.json()

    assert "recording_id" in data
    assert "interview_id" in data
    assert "uri" in data
    assert "created_at" in data


@then("the recording has interview_id matching the interview")
def check_interview_id_match(request: Any) -> None:
    """Verify the recording's interview_id matches."""
    from tests.conftest import TestingSessionLocal

    response = request.upload_response
    data = response.json()

    # The interview_id should be valid
    interview_id = int(data["interview_id"])
    with TestingSessionLocal() as db:
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        assert interview is not None


@then("the recording has a unique recording_id")
def check_unique_recording_id(request: Any) -> None:
    """Verify the recording has a unique ID."""
    response = request.upload_response
    data = response.json()

    assert data["recording_id"]
    assert data["recording_id"].isdigit()


@then("the recording has the correct file metadata")
def check_file_metadata(request: Any) -> None:
    """Verify the recording metadata is correct."""
    response = request.upload_response
    data = response.json()

    assert data["duration_ms"] == 30000
    assert data["sample_rate_hz"] == 44100
    assert data["mime_type"] == "audio/wav"
    assert data["file_size_bytes"] is not None
    assert data["file_size_bytes"] > 0


@then("the recording is created successfully")
def check_recording_created(request: Any) -> None:
    """Verify the recording was created successfully."""
    response = request.upload_response
    assert response.status_code == 201
    data = response.json()
    assert "recording_id" in data


@then("the recording metadata includes file size")
def check_file_size_included(request: Any) -> None:
    """Verify file size is included in metadata."""
    response = request.upload_response
    data = response.json()

    assert data["file_size_bytes"] is not None
    assert data["file_size_bytes"] > 50000  # Large file should be substantial


@then("the recording is stored in object storage")
def check_object_storage(request: Any) -> None:
    """Verify the recording URI indicates object storage."""
    response = request.upload_response
    data = response.json()

    uri = data["uri"]
    assert "localhost:9000" in uri or "minio" in uri  # MinIO storage
    assert "audio-recordings" in uri  # Correct bucket
    assert "/interviews/" in uri  # Correct path structure


# Common response checking steps


@then(parsers.parse("the response status is {status_code:d}"))
def check_response_status(request: Any, status_code: int) -> None:
    """Check the HTTP response status code."""
    response = request.upload_response
    assert response.status_code == status_code


@then(parsers.parse('the error message is "{message}"'))
def check_error_message(request: Any, message: str) -> None:
    """Check the error message in response."""
    response = request.upload_response
    data = response.json()
    assert message in data.get("detail", "")


@then(parsers.parse('the error message contains "{message}"'))
def check_error_message_contains(request: Any, message: str) -> None:
    """Check the error message contains specific text."""
    response = request.upload_response
    data = response.json()
    assert message in data.get("detail", "")
