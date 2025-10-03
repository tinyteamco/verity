"""
Pytest configuration and fixtures for the test suite
"""

import contextlib
import os
from collections.abc import Generator

# Set test environment FIRST, before any imports
os.environ["APP_ENV"] = "local"
os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"

import firebase_admin
import pytest
from fastapi.testclient import TestClient
from firebase_admin import auth
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Clear any existing Firebase apps to ensure clean initialization
firebase_admin._apps = {}

# Force Firebase initialization with test settings before any other imports
if not firebase_admin._apps:
    firebase_admin.initialize_app(credential=None, options={"projectId": "verity-local"})

# Now import the app
from src.api.main import app  # noqa: E402
from src.database import Base, get_db  # noqa: E402


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
def firebase_app():
    """Get Firebase Admin SDK app (already initialized with correct config)"""
    return firebase_admin.get_app()


@pytest.fixture(scope="session")
def super_admin_user(firebase_app):
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
def test_org_user(firebase_app):
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
def test_interviewee_user(firebase_app):
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
