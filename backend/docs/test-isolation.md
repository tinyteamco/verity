# Test Isolation Strategy

## Problem

Previously, running `make test-ci` (triggered by pre-push git hooks) conflicted with the dev environment:
- Both dev and test wanted Firebase Auth emulator on port 9099
- Tests would fail or be killed (Error 137 - SIGKILL)
- Couldn't push changes without stopping dev servers

## Solution

**Use dynamic port allocation with per-session isolation:**

| Environment | Firebase Port | Backend Port | Type           | Startup Time |
|-------------|---------------|--------------|----------------|--------------|
| Development | 9099 (fixed)  | 8000 (fixed) | Full emulator  | 12-15s       |
| Backend Tests | Random        | N/A          | Stub (pytest)  | <1s          |
| Frontend E2E  | Random×2      | Random       | Stub (per test)| <1s          |

### Architecture

```
┌─────────────────────────────────┐
│  Development Environment        │
│  (manual start: make dev)       │
│                                 │
│  - Backend: localhost:8000      │
│  - Frontend: localhost:5173     │
│  - Firebase: localhost:9099     │
│  - PostgreSQL: Docker (shared)  │
│  - MinIO: Docker (shared)       │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│  Backend Test Session           │
│  (pytest auto-spawns)           │
│                                 │
│  - Backend: TestClient (no port)│
│  - Firebase Stub: Random port   │
│  - SQLite: In-memory per test   │
│  - MinIO: Docker (shared)       │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│  Frontend E2E Test (each test)  │
│  (playwright auto-spawns)       │
│                                 │
│  - Backend: Random port         │
│  - Firebase Stub: Random port   │
│  - SQLite: Temp file per test   │
│  - MinIO: N/A (mocked)          │
└─────────────────────────────────┘
```

### Implementation

**1. Backend Test Isolation (pytest manages stub)**

`tests/conftest.py`:
```python
@pytest.fixture(scope="session", autouse=True)
def firebase_stub() -> Generator[int, None, None]:
    """Start Firebase stub on random port for this test session."""
    stub_port = find_free_port()  # Dynamic allocation

    # Spawn stub process
    stub_process = subprocess.Popen(
        ["uv", "run", "python", "scripts/firebase_auth_stub.py"],
        env={**os.environ, "STUB_PORT": str(stub_port)},
    )

    # Set env var for all tests
    os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = f"localhost:{stub_port}"

    yield stub_port

    # Auto-cleanup
    stub_process.terminate()
```

**Key points:**
- Each pytest session allocates a random port via `socket.socket()`
- Stub lifecycle managed by pytest fixture (auto start/stop)
- No manual management needed
- Multiple test sessions can run in parallel

**2. Frontend E2E Test Isolation (per-test spawning)**

`frontend/tests/support/world.ts`:
```typescript
fixtures: async ({ page }, use) => {
  // Spawn backend+stub with dynamic ports via bash script
  const backendProcess = spawn('bash', ['-c',
    'cd ../backend && ./scripts/start_e2e_backend.sh'
  ])

  // Script outputs: STUB_PORT=<random> BACKEND_PORT=<random>
  // Store PID for cleanup
  (page as any).__backendProcess__ = backendProcess

  await use(fixtures)

  // Cleanup: kill specific process (no global pkill)
  backendProcess.kill('SIGKILL')
}
```

**Key points:**
- Each frontend test spawns its own backend+stub
- Dynamic port allocation via `start_e2e_backend.sh`
- Process tracked by PID for precise cleanup
- No global killing (prevents conflicts)

**3. Makefile**

```makefile
# Development: full Firebase emulator (port 9099)
dev:
    docker compose up -d postgres minio
    $(MAKE) start-firebase
    uv run uvicorn src.api.main:app --port 8000

# Tests: pytest manages Firebase stub on random port
test-ci: .docker-services
    APP_ENV=local uv run pytest
```

### Benefits

✅ **True parallel execution** - Dev, backend tests, and frontend tests all run simultaneously
✅ **10x faster tests** - Firebase stub (<1s) vs full emulator (12-15s)
✅ **Zero conflicts** - Dynamic ports prevent port collisions
✅ **CI-friendly** - No Firebase CLI dependency needed
✅ **Better isolation** - Each test session has clean Firebase state
✅ **Push without stopping dev** - Pre-push hooks work while dev servers run
✅ **Multiple test runs** - Run tests in parallel (e.g., frontend E2E across 6 workers)

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
make clean  # Full cleanup: orphans + Firebase + Docker + cache
```

### Manual Cleanup

If tests crash and leave orphaned processes (rare with auto-cleanup, but can happen):

```bash
make kill-orphans
```

This kills:
- All Firebase Auth stubs (any port)
- All Firebase emulators
- All uvicorn processes
- Processes on ports 8000, 9099, 9199

Then restart your dev environment:
```bash
make dev
```

**When you might need this:**
- Tests crashed due to SIGKILL or CTRL+C
- "Port already in use" errors
- Stale processes from interrupted test runs

### Troubleshooting

**Port already in use (dev environment):**
```bash
# Check what's using standard dev ports
lsof -i:8000   # Backend
lsof -i:9099   # Firebase emulator
lsof -i:5173   # Frontend

# Quick cleanup
make kill-orphans

# Then restart
make dev
```

**Tests failing with random errors after crashes:**
```bash
# Full cleanup
make kill-orphans

# Run tests again
make test-ci
```

**Pre-push hook failing:**
```bash
# Ensure no orphaned processes
make kill-orphans

# Retry push
git push
```

**Multiple test runs interfering:**
- Should not happen with random port allocation
- If it does, ensure frontend tests aren't using global `pkill` commands
- Check `frontend/tests/support/world.ts` for process cleanup code
