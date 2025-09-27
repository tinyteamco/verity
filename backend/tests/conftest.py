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

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def firebase_app():
    """Get Firebase Admin SDK app (already initialized with correct config)"""
    return firebase_admin.get_app()


@pytest.fixture
def client():
    """FastAPI test client with fresh database"""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


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
def super_admin_token():
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
