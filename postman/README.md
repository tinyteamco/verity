# Verity API Postman Collection

A comprehensive Postman collection for testing the Verity UXR platform API with Newman.

## Prerequisites

- Newman installed globally: `npm install -g newman`
- Backend services running: `make dev` from backend directory
- Firebase emulator running (started automatically by `make dev`)

## Files

- `verity-api.postman_collection.json` - Complete API test collection with auto-auth
- `local.postman_environment.json` - Local development environment variables

## Features

### Automatic Firebase Authentication
The collection includes a pre-request script that automatically:
- Authenticates with Firebase emulator using test credentials
- Caches the JWT token in environment variables
- Refreshes the token when it expires (55-minute TTL)

### Request Chaining
Tests are organized in sequence to create dependencies:
1. Create Organization → saves `org_id`
2. Create Study → saves `study_id`
3. Generate Interview → saves `interview_id` and `access_token`
4. Finalize Transcript → uses `interview_id`

### Test Coverage
The collection includes 16 API endpoint tests across 7 feature areas:
- Health Check (no auth)
- Organizations (create, get current, list users)
- Studies (create, list, get)
- Interview Guides (create/update, get)
- Interviews (generate link, list, get details)
- Public Interview Access (access via token, claim interview)
- Transcripts (finalize with segments)

## Running Tests

### Basic Run
```bash
newman run postman/verity-api.postman_collection.json \
  -e postman/local.postman_environment.json
```

### With Options
```bash
# Add delays between requests (helps with race conditions)
newman run postman/verity-api.postman_collection.json \
  -e postman/local.postman_environment.json \
  --delay-request 200

# Increase timeout for slow endpoints
newman run postman/verity-api.postman_collection.json \
  -e postman/local.postman_environment.json \
  --timeout-request 10000

# Save results to file
newman run postman/verity-api.postman_collection.json \
  -e postman/local.postman_environment.json \
  --reporters cli,json \
  --reporter-json-export results.json
```

### CI/CD Integration
```bash
# Fail fast on first error
newman run postman/verity-api.postman_collection.json \
  -e postman/local.postman_environment.json \
  --bail

# Quiet output for CI logs
newman run postman/verity-api.postman_collection.json \
  -e postman/local.postman_environment.json \
  --silent
```

## Current Status

### Working ✅
- Health check endpoint
- Firebase emulator authentication
- Organization creation (super admin)
- Token caching and auto-refresh

### Known Issues ⚠️
- After creating an org, the super admin user needs to be explicitly linked to the org in the database
- Some endpoints return 403 because the user-org association isn't automatic
- These are expected behaviors for the current API implementation

### Not Yet Implemented ❌
- Audio recording upload (requires multipart/form-data with actual file)
- Interview summary generation (async job endpoints)
- Study summary generation
- Job status polling

## Environment Variables

The `local.postman_environment.json` file includes:

| Variable | Value | Description |
|----------|-------|-------------|
| `api_base_url` | `http://localhost:8000` | Backend API URL |
| `firebase_emulator_url` | `http://localhost:9099` | Firebase Auth emulator |
| `test_email` | `admin@tinyteam.co` | Super admin email |
| `test_password` | `superadmin123` | Super admin password |
| `firebase_token` | (auto-populated) | Cached JWT token |
| `token_expiry` | (auto-populated) | Token expiration timestamp |
| `org_id` | (auto-populated) | Created organization ID |
| `study_id` | (auto-populated) | Created study ID |
| `interview_id` | (auto-populated) | Created interview ID |
| `access_token` | (auto-populated) | Interview access token (UUID) |
| `transcript_id` | (auto-populated) | Created transcript ID |

## Importing to Postman Desktop

1. Open Postman Desktop
2. Click "Import" button
3. Select both `verity-api.postman_collection.json` and `local.postman_environment.json`
4. Select "Local Development" environment from dropdown
5. Run requests manually or use Collection Runner

## Troubleshooting

### Authentication Errors
- Ensure Firebase emulator is running: `http://localhost:9099`
- Check that super admin user exists (seeded by `make dev`)
- Token is auto-refreshed, but you can clear it manually in environment variables

### Connection Refused
- Ensure backend is running: `make dev` from backend directory
- Check health endpoint: `curl http://localhost:8000/health`

### 403 Forbidden After Creating Org
- This is expected - the super admin user needs to be linked to the org
- Currently requires manual database association
- Future improvement: auto-link user on org creation

## Example Output

```
newman

Verity API

❏ 01 - Health Check
↳ Health Check
  GET http://localhost:8000/health [200 OK, 230B, 9ms]
  ✓  Status code is 200
  ✓  Response has healthy field

❏ 02 - Organizations
↳ Create Organization
  POST http://localhost:8000/orgs [201 Created, 226B, 35ms]
  ✓  Status code is 201
  ✓  Response has org_id

...

┌─────────────────────────┬─────────────────┬─────────────────┐
│                         │        executed │          failed │
├─────────────────────────┼─────────────────┼─────────────────┤
│              iterations │               1 │               0 │
├─────────────────────────┼─────────────────┼─────────────────┤
│                requests │              16 │               0 │
├─────────────────────────┼─────────────────┼─────────────────┤
│            test-scripts │              15 │               0 │
├─────────────────────────┼─────────────────┼─────────────────┤
│              assertions │              29 │               4 │
└─────────────────────────┴─────────────────┴─────────────────┘
```

## Future Enhancements

- [ ] Add audio file upload with actual WAV file
- [ ] Add async job polling tests
- [ ] Add share link flow tests
- [ ] Add data cleanup/teardown scripts
- [ ] Add performance benchmarks
- [ ] Add negative test cases (invalid data, unauthorized access)