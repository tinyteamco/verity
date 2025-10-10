"""
Pytest configuration and fixtures for the test suite
"""

import contextlib
import os
import socket
import subprocess
import time
from collections.abc import Generator

# Set test environment FIRST, before any imports
os.environ["APP_ENV"] = "local"

# Set dummy LLM API configuration before importing pydantic-ai models
# The actual stub will be started by the fixture, but we need the env var set early
# to ensure the Anthropic client uses the right base URL
os.environ["ANTHROPIC_API_KEY"] = "test-api-key"  # Dummy key for tests

import firebase_admin
import pytest
from fastapi.testclient import TestClient
from firebase_admin import auth
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Import app AFTER setting environment variables
from src.api.main import app
from src.database import Base, get_db


def find_free_port() -> int:
    """Find a free port for the Firebase stub."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest.fixture(scope="session", autouse=True)
def firebase_stub() -> Generator[int, None, None]:
    """
    Start a Firebase Auth stub for this test session on a random free port.
    This ensures each test run (including parallel pre-push hook runs) gets
    its own isolated Firebase stub.
    """
    # Find a free port
    stub_port = find_free_port()

    # Start the stub process
    stub_process = subprocess.Popen(
        ["uv", "run", "python", "scripts/firebase_auth_stub.py"],
        env={**os.environ, "STUB_PORT": str(stub_port)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for stub to be ready
    max_attempts = 30
    for _ in range(max_attempts):
        try:
            import requests

            response = requests.get(f"http://localhost:{stub_port}", timeout=1)
            if response.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.1)
    else:
        stub_process.kill()
        raise RuntimeError(f"Firebase stub failed to start on port {stub_port}")

    # Set environment variable for all tests in this session
    os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = f"localhost:{stub_port}"

    yield stub_port

    # Cleanup
    stub_process.terminate()
    try:
        stub_process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        stub_process.kill()


@pytest.fixture(scope="session", autouse=True)
def llm_stub() -> Generator[int, None, None]:
    """
    Start an LLM API stub for this test session on a random free port.
    This ensures each test run gets its own isolated LLM stub.
    """
    # Find a free port
    stub_port = find_free_port()

    # Start the stub process
    stub_process = subprocess.Popen(
        ["uv", "run", "python", "scripts/llm_stub.py"],
        env={**os.environ, "LLM_STUB_PORT": str(stub_port)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for stub to be ready
    max_attempts = 30
    for _ in range(max_attempts):
        try:
            import requests

            response = requests.get(f"http://localhost:{stub_port}", timeout=1)
            if response.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.1)
    else:
        stub_process.kill()
        raise RuntimeError(f"LLM stub failed to start on port {stub_port}")

    # Set environment variables for pydantic-ai to use the stub
    os.environ["ANTHROPIC_BASE_URL"] = f"http://localhost:{stub_port}/v1"
    # Set a dummy API key (stub doesn't validate it but pydantic-ai requires one)
    os.environ["ANTHROPIC_API_KEY"] = "test-api-key"

    print(f"\n[DEBUG] LLM Stub started on port {stub_port}")
    print(f"[DEBUG] ANTHROPIC_BASE_URL={os.environ['ANTHROPIC_BASE_URL']}")
    print(f"[DEBUG] ANTHROPIC_API_KEY={os.environ['ANTHROPIC_API_KEY']}")

    yield stub_port

    # Cleanup
    stub_process.terminate()
    try:
        stub_process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        stub_process.kill()


@pytest.fixture(scope="session", autouse=True)
def setup_firebase(firebase_stub: int, llm_stub: int) -> None:
    """Initialize Firebase Admin SDK after stub is running."""
    # Clear any existing Firebase apps
    firebase_admin._apps = {}

    # Initialize Firebase Admin SDK to use the emulator (env var is set by firebase_stub)
    firebase_admin.initialize_app(credential=None, options={"projectId": "verity-local"})


# Helper function for step definitions that need direct DB access
def TestingSessionLocal() -> Session:  # noqa: N802
    """
    Get a database session for the current test.
    This works by using the overridden get_db dependency.
    """
    # Import here to avoid circular dependency
    from src.database import get_db

    # Get the override function that was set by the client fixture
    override_fn = app.dependency_overrides.get(get_db)
    if override_fn:
        # Call the generator and get the session
        gen = override_fn()
        session = next(gen)
        return session
    else:
        # Fallback for tests that don't use client fixture
        # This shouldn't happen in practice
        raise RuntimeError("TestingSessionLocal called outside of test context")


@pytest.fixture(scope="session")
def super_admin_user(setup_firebase: None):
    """Create ONE super admin for entire test session"""
    uid = "test-super-admin"
    email = "admin@tinyteam.co"

    # Clean up if exists from previous run
    with contextlib.suppress(Exception):
        auth.delete_user(uid)

    # Create once for all tests
    user = auth.create_user(
        uid=uid,
        email=email,
        password="superadmin123",
        email_verified=True,
    )

    auth.set_custom_user_claims(uid, {"tenant": "organization", "role": "super_admin"})

    yield user

    # Cleanup after all tests
    with contextlib.suppress(Exception):
        auth.delete_user(uid)


@pytest.fixture
def client():
    """FastAPI test client with fresh in-memory database per test"""
    from sqlalchemy.pool import StaticPool

    # Use shared-cache in-memory database that works across threads
    # StaticPool ensures all connections share the same in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Critical: keeps same connection across threads
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create fresh schema
    Base.metadata.create_all(bind=engine)

    # Override DB dependency for this test
    def override_get_db() -> Generator[Session, None, None]:
        try:
            db = session_local()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Create TestClient AFTER setting overrides
    # Use base_url to prepend /api to all requests (routes are now under /api prefix)
    test_client = TestClient(app, base_url="http://testserver/api")

    yield test_client

    # Cleanup
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_org_user(setup_firebase: None):
    """Create a test organization user for this test"""
    try:
        user = auth.create_user(
            uid="test-org-user",
            email="testuser@example.com",
            password="testpass123",
            email_verified=True,
        )
        auth.set_custom_user_claims("test-org-user", {"tenant": "organization", "role": "owner"})
        yield user
    finally:
        # Clean up after test
        with contextlib.suppress(Exception):
            auth.delete_user("test-org-user")


@pytest.fixture
def test_interviewee_user(setup_firebase: None):
    """Create a test interviewee user for this test"""
    try:
        user = auth.create_user(
            uid="test-interviewee",
            email="testinterviewee@example.com",
            password="testpass123",
            email_verified=True,
        )
        auth.set_custom_user_claims("test-interviewee", {"tenant": "interviewee"})
        yield user
    finally:
        # Clean up after test
        with contextlib.suppress(Exception):
            auth.delete_user("test-interviewee")


@pytest.fixture
def ensure_firebase_initialized():
    """Ensure Firebase is initialized for tests that need it"""
    # The app import triggers Firebase initialization
    # This fixture forces that initialization to happen
    from src.api.main import app  # noqa: F401

    return True


@pytest.fixture
def super_admin_token(super_admin_user):
    """Get ID token for the super admin user (seeded in emulator)"""
    from tests.test_helpers import get_super_admin_token

    return get_super_admin_token()


@pytest.fixture
def org_user_token(test_org_user):
    """Get ID token for test organization user"""
    from tests.test_helpers import sign_in_user

    return sign_in_user("testuser@example.com", "testpass123")


@pytest.fixture
def interviewee_token(test_interviewee_user):
    """Get ID token for test interviewee user"""
    from tests.test_helpers import sign_in_user

    return sign_in_user("testinterviewee@example.com", "testpass123")
