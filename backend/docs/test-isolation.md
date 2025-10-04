# Test Isolation Strategy

## Problem

Previously, running `make test-ci` (triggered by pre-push git hooks) conflicted with the dev environment:
- Both dev and test wanted Firebase Auth emulator on port 9099
- Tests would fail or be killed (Error 137 - SIGKILL)
- Couldn't push changes without stopping dev servers

## Solution

**Use separate Firebase instances with port isolation:**

| Environment | Firebase Port | Type           | Startup Time |
|-------------|---------------|----------------|--------------|
| Development | 9099          | Full emulator  | 12-15s       |
| Tests (CI)  | 9199          | Lightweight stub | <1s       |

### Architecture

```
┌─────────────────────────────────┐
│  Development Environment        │
│                                 │
│  - Backend: localhost:8000      │
│  - Frontend: localhost:5173     │
│  - Firebase: localhost:9099     │
│  - PostgreSQL: Docker           │
│  - MinIO: Docker                │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│  Test Environment (CI)          │
│                                 │
│  - Backend: TestClient (no port)│
│  - Firebase Stub: localhost:9199│
│  - SQLite: In-memory            │
│  - MinIO: Mocked                │
└─────────────────────────────────┘
```

### Implementation

**1. Makefile Changes**

```makefile
# Development: uses full Firebase emulator (port 9099)
dev:
    docker compose up -d postgres minio
    $(MAKE) start-firebase
    uv run uvicorn ...

# Tests: uses Firebase stub (port 9199)
test-ci: .firebase-stub-seeded
    APP_ENV=local FIREBASE_AUTH_EMULATOR_HOST=localhost:9199 uv run pytest

# Firebase stub management
start-firebase-stub:
    STUB_PORT=9199 uv run python scripts/firebase_auth_stub.py &
    # Wait for startup...

stop-firebase-stub:
    pkill -f "firebase_auth_stub.py"
```

**2. Test Configuration**

`tests/conftest.py`:
```python
# Respect FIREBASE_AUTH_EMULATOR_HOST from environment
if "FIREBASE_AUTH_EMULATOR_HOST" not in os.environ:
    os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"
```

`tests/test_helpers.py`:
```python
# Use port from environment variable
FIREBASE_EMULATOR_HOST = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")
```

**3. Git Hook Integration**

Pre-push hook (managed by hk) runs:
```bash
cd backend && mise run test-ci
```

This automatically:
1. Checks if Firebase stub is running on 9199
2. Starts it if needed (<1s startup)
3. Seeds super admin user
4. Runs pytest with `FIREBASE_AUTH_EMULATOR_HOST=localhost:9199`
5. Completes without touching dev environment on 9099

### Benefits

✅ **Parallel execution** - Dev and test run simultaneously without conflicts
✅ **10x faster tests** - Firebase stub (<1s) vs full emulator (12-15s)
✅ **CI-friendly** - No Firebase CLI dependency needed
✅ **Better isolation** - Each test run has clean Firebase state
✅ **Push without stopping dev** - Pre-push hooks work while dev servers run

### Firebase Auth Stub

Located in `scripts/firebase_auth_stub.py`, this is a minimal FastAPI application that implements only the Firebase Auth endpoints used by our tests:

- User creation (Admin SDK + Client SDK)
- Sign in with password
- Custom claims management
- User lookup
- Token generation (JWT)

Endpoints implemented:
- `POST /identitytoolkit.googleapis.com/v1/projects/{project}/accounts` (create user)
- `POST /identitytoolkit.googleapis.com/v1/accounts:signInWithPassword` (sign in)
- `POST /identitytoolkit.googleapis.com/v1/projects/{project}/accounts:update` (set claims)
- `POST /identitytoolkit.googleapis.com/v1/accounts:lookup` (get user)
- `GET /robot/v1/metadata/x509/securetoken@system.gserviceaccount.com` (public keys)

### Usage

**Run tests locally (with Firebase stub):**
```bash
make test-ci
```

**Run tests with full emulator (slower, but matches dev exactly):**
```bash
make test
```

**Start dev environment:**
```bash
make dev  # Uses port 9099
```

**Clean up all processes:**
```bash
make clean  # Stops both Firebase emulator and stub
```

### Troubleshooting

**Port already in use:**
```bash
# Check what's using the port
lsof -i:9199  # or :9099

# Kill specific stub processes
make stop-firebase-stub

# Kill specific emulator processes
make stop-firebase

# Kill all Firebase-related processes
pkill -f firebase
```

**Tests failing with "connection refused":**
- Stub may not have started
- Run `curl http://localhost:9199` to verify
- Check logs at `/tmp/firebase-stub.log`

**Tests using wrong port:**
- Verify `FIREBASE_AUTH_EMULATOR_HOST` environment variable
- Check `tests/conftest.py` and `tests/test_helpers.py`
