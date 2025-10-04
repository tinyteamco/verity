#!/usr/bin/env bash
set -e

# Start backend for E2E testing with dynamic ports for complete test isolation
# Usage: ./start_e2e_backend.sh [output_file]
# Outputs: STUB_PORT=<port> BACKEND_PORT=<port> to stdout or output_file

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Find available port and reserve it with a lock file
# This prevents TOCTOU race conditions in parallel test execution
find_and_reserve_port() {
  local max_attempts=50
  for attempt in $(seq 1 $max_attempts); do
    local port=$(python3 -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1]); s.close()')
    local lockfile="/tmp/port_${port}.lock"

    # Try to create lock file atomically
    if mkdir "$lockfile" 2>/dev/null; then
      # Successfully reserved this port
      echo "$port"
      return 0
    fi
    # Port was taken by another process, try again
  done

  echo "Failed to find free port after $max_attempts attempts" >&2
  return 1
}

# Generate unique test ID to prevent collisions
# Use sh -c to get this script's actual PID + nanosecond timestamp
# Note: $$ in main script is parent PID (same for all), but in subshell it's unique
TEST_ID="$(sh -c 'echo $$')_$(date +%s%N)"

# Allocate dynamic ports with locks
STUB_PORT=$(find_and_reserve_port)
BACKEND_PORT=$(find_and_reserve_port)

# Output port information immediately so test harness doesn't wait
echo "STUB_PORT=$STUB_PORT"
echo "BACKEND_PORT=$BACKEND_PORT"

echo "🔍 Test ID: $TEST_ID, Stub: $STUB_PORT, Backend: $BACKEND_PORT" >&2

echo "🚀 Starting E2E test stack with dynamic ports..." >&2
echo "  - Firebase Auth Stub (port $STUB_PORT)" >&2
echo "  - Backend API (port $BACKEND_PORT)" >&2
echo "" >&2

# Start Firebase Auth Stub on dynamic port
echo "Starting Firebase Auth Stub on port $STUB_PORT..." >&2
cd "$BACKEND_DIR"
STUB_PORT=$STUB_PORT mise exec -- uv run python scripts/firebase_auth_stub.py > /tmp/stub_${STUB_PORT}.log 2>&1 &
STUB_PID=$!

# Wait for stub to be ready
echo "Waiting for Firebase Auth Stub to be ready..." >&2
for i in {1..30}; do
  if curl -s http://localhost:$STUB_PORT/ >/dev/null 2>&1; then
    echo "✅ Firebase Auth Stub is ready on port $STUB_PORT!" >&2
    break
  fi
  if [ $i -eq 30 ]; then
    echo "❌ Firebase Auth Stub failed to start" >&2
    kill $STUB_PID 2>/dev/null || true
    exit 1
  fi
  sleep 0.1
done

# Seed super admin user in stub
echo "Seeding super admin user..." >&2
curl -s -X POST http://localhost:$STUB_PORT/identitytoolkit.googleapis.com/v1/projects/verity-local/accounts \
  -H "Content-Type: application/json" \
  -d '{"localId":"test-super-admin","email":"admin@tinyteam.co","password":"superadmin123","emailVerified":true}' >/dev/null

curl -s -X POST http://localhost:$STUB_PORT/identitytoolkit.googleapis.com/v1/projects/verity-local/accounts:update \
  -H "Content-Type: application/json" \
  -d '{"localId":"test-super-admin","customAttributes":"{\"tenant\":\"organization\",\"role\":\"super_admin\"}"}' >/dev/null

echo "✅ Super admin user seeded" >&2

# Use unique temp database file for complete isolation
# Cannot use :memory: due to SQLAlchemy connection pooling sharing the same DB
# Use TEST_ID instead of port to avoid collisions if ports are reused
DB_FILE="/tmp/verity_e2e_test_${TEST_ID}.db"

# Delete any existing database file
rm -f "$DB_FILE"

# Set environment variables for E2E test mode
export APP_ENV="test"
export DATABASE_URL="sqlite:///$DB_FILE"
export FIREBASE_AUTH_EMULATOR_HOST="localhost:$STUB_PORT"
export USE_FIREBASE_STUB="true"

# Create database schema
echo "Creating database schema for $DATABASE_URL..." >&2
cd "$BACKEND_DIR"
if ! mise exec -- env DATABASE_URL="$DATABASE_URL" uv run python -c "
from src.database import engine
from src.models import Base
Base.metadata.create_all(engine)
print('Database schema created')
" 2>&1 >&2; then
  echo "❌ Failed to create database schema" >&2
  kill $STUB_PID 2>/dev/null || true
  exit 1
fi

# Verify database file was created
if [ ! -f "$DB_FILE" ]; then
  echo "❌ Database file not created: $DB_FILE" >&2
  kill $STUB_PID 2>/dev/null || true
  exit 1
fi

# Ensure database file has correct permissions
chmod 666 "$DB_FILE" 2>/dev/null || true
echo "✅ Database ready at $DB_FILE" >&2

# Cleanup function
cleanup() {
  echo "" >&2
  echo "Shutting down E2E test stack (ports $STUB_PORT, $BACKEND_PORT)..." >&2
  kill $STUB_PID 2>/dev/null || true

  # Release port locks
  rmdir "/tmp/port_${STUB_PORT}.lock" 2>/dev/null || true
  rmdir "/tmp/port_${BACKEND_PORT}.lock" 2>/dev/null || true

  exit
}
trap cleanup EXIT INT TERM

# Start uvicorn on dynamic port (use exec to replace shell process)
echo "Starting backend API on port $BACKEND_PORT with DATABASE_URL=$DATABASE_URL..." >&2
exec mise exec -- env DATABASE_URL="$DATABASE_URL" APP_ENV="$APP_ENV" FIREBASE_AUTH_EMULATOR_HOST="$FIREBASE_AUTH_EMULATOR_HOST" USE_FIREBASE_STUB="$USE_FIREBASE_STUB" uv run uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port $BACKEND_PORT \
    --log-level debug > /tmp/backend_${BACKEND_PORT}.log 2>&1
