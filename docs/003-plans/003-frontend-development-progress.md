# Frontend Development Progress

**Last Updated:** 2025-10-04
**Status:** Backend Organization Model Refactored - Ready for Phase 3

## 🎯 Current Objective

Building out the UX to validate backend implementation, following a super admin → organization admin → user workflow (working inward from platform administration).

## ✅ Completed

### E2E Test Infrastructure
- **Real-mode only testing** - Removed all mock mode logic
- **Complete test isolation** - Each test gets unique database + backend + Firebase stub
- **Dynamic port allocation** - Atomic port locking prevents race conditions
- **Fast parallel execution** - 1s setup per test, runs with 2 workers (8 tests in 8s)
- **Hydration for speed** - Accumulate test data + real API calls for fast setup
- **Firebase Auth Stub** - Lightweight FastAPI replacement for emulator (<1s startup vs 12-15s)
- **All tests passing** - 8 frontend E2E (8s total) + 95 backend BDD tests
- **Pre-push validation** - Build + tests run before allowing push to prevent CI failures

### Frontend Stack
- **React** + TypeScript + Vite
- **Jotai** for state management
- **Firebase Auth** with stub support for E2E tests
- **Playwright + playwright-bdd** for BDD-style E2E tests
- **Hydration test utils** for fast intermediate state setup (tree-shaken from production)
- **Zod v4** for schema validation (upgraded for compatibility)
- **Production build:** 369KB gzipped (test utilities excluded via tree-shaking)

### Super Admin Features Implemented

#### 1. Authentication ✅
- Login page with email/password (Firebase Auth)
- Session persistence with localStorage
- Auto-restore auth state on page load

#### 2. Organization List ✅
- View all organizations (super admin only)
- Empty state: "No organizations yet"
- GET `/api/orgs` endpoint

#### 3. Create Organization with Owner ✅
- Modal UI with org name + owner email fields
- **Automatic owner provisioning** via Firebase Auth (mandatory)
- Owner receives password reset link (Firebase built-in flow)
- **Unique organization names** enforced (database constraint + API validation)
- POST `/api/orgs` endpoint with owner creation
- Success modal showing password reset link
- Refresh list after creation
- Full E2E test coverage

**Backend Constraints:**
- `owner_email` is required (non-nullable) - every org must have an owner
- `organizations.name` (slug) has unique constraint in database
- `organizations.display_name` is required (human-readable name)
- `organizations.description` is optional (can be null)
- Slug validation: lowercase, alphanumeric, hyphens only (enforced via Pydantic)
- IntegrityError returns 400: "Organization with name 'X' already exists"
- Owner role cannot be changed - one owner per organization
- Soft delete: Sets `deleted_at` timestamp instead of hard delete
- Deleted orgs filtered from all queries (invisible to users)

#### 4. Organization Detail Page ✅
- Click org → navigate to `/orgs/{id}`
- View organization details (name, created date)
- Organization users section (UI placeholder)
- Organization studies section (UI placeholder)
- "Add User" and "Create Study" buttons
- Full E2E test coverage

#### 5. Organization Users Management ✅
- View users in an organization
- Add admin users to organization
- Add member users to organization
- Full E2E test coverage

**Test Coverage:**
```gherkin
Scenario: View empty organizations list
Scenario: View existing organizations
Scenario: Create a new organization with owner
Scenario: View organization details
Scenario: Refresh on organization details page
Scenario: View organization users
Scenario: Add admin user to organization
Scenario: Add member user to organization
```

## 🚧 In Progress / Next Steps

Following the super admin workflow (working inward):

### Phase 2: Organization Management (completed ✅)
1. ✅ **Backend API for Organization Detail View**
   - `/api/orgs/{id}/users` endpoint (super admin can view any org's users)
   - Studies endpoint already exists at `/api/studies?org_id={id}`

2. ✅ **Add Additional Users to Organization** - Super admin provisions org admins/members
   - Modal with email + role selection (admin/member)
   - Create Firebase user + User record in database
   - Associate user with organization
   - Owner is automatically created when organization is created

3. ✅ **Organization Model Refactoring** - GitHub-style slugs and soft delete
   - Organization name → slug (unique, lowercase, hyphens only: `tinyteam`)
   - Added display_name for human-readable names (`TinyTeam`)
   - Added description for optional text descriptions
   - Added deleted_at for soft delete functionality
   - Added updated_at tracking for pruning deleted accounts
   - DELETE `/api/orgs/{id}` endpoint for soft deletes
   - Slug validation: lowercase, alphanumeric, hyphens (no spaces/uppercase/special chars)
   - All organization queries filter out soft-deleted records
   - Destructive Alembic migration with data migration (name → display_name)
   - **Breaking change:** No backward compatibility (production migration applied)

4. ✅ **Frontend Token Auto-Refresh** - Fixed production auth expiration
   - Automatic token refresh every 50 minutes (before 1-hour expiration)
   - Prevents "Invalid token: Token expired" errors in production
   - Uses `onIdTokenChanged` listener for seamless refresh

### Phase 3: Study Management (Next)
Transition to org admin workflow:

**Prerequisites (Backend Ready):**
- ✅ Study CRUD endpoints exist (`/api/studies`)
- ✅ Interview guide endpoints exist (`/api/studies/{id}/guide`)
- ✅ Authorization enforced (org-scoped access)

**Frontend Work Required:**
1. **Create study in organization**
   - Study creation form (title field)
   - POST `/api/studies` with auth token
   - Associate study with organization (automatic via auth)
   - E2E test coverage

2. **View study details**
   - Study detail page with metadata
   - Interview guide display
   - Edit interview guide (markdown textarea)
   - E2E test coverage

3. **Study list in organization view**
   - Show studies on organization detail page
   - Click to navigate to study details
   - E2E test coverage

### Phase 4: Interview Flow
- Generate interview link
- Test interview as participant (link-based access)
- View interview results

## 📁 File Structure

```
frontend/
├── src/
│   ├── App.tsx                    # Main app with routing + Dashboard
│   ├── atoms/
│   │   ├── auth.ts               # User auth state (Jotai)
│   │   └── organizations.ts      # Organizations list state
│   ├── lib/
│   │   ├── firebase.ts           # Firebase config + stub detection
│   │   └── auth-persistence.ts  # Auth state persistence
│   └── pages/
│       ├── LoginPage.tsx                # Login UI
│       └── OrganizationDetailPage.tsx   # Organization detail view
│
├── tests/
│   ├── features/
│   │   └── org-management.feature  # BDD scenarios
│   ├── steps/
│   │   └── org-management.steps.ts # Step implementations
│   └── support/
│       ├── world.ts              # Test fixture with backend orchestration
│       ├── fixtures.ts           # Test helpers (login, seed data)
│       ├── hydration-registry.ts # Hydration schemas
│       └── bdd-hydration.ts      # Hydration accumulator

backend/
├── scripts/
│   ├── start_e2e_backend.sh      # E2E test orchestration script
│   └── firebase_auth_stub.py     # Lightweight Firebase emulator replacement
└── src/api/main.py               # GET/POST /orgs endpoints
```

## 🔧 Technical Notes

### E2E Port Detection
- Tests set `__E2E_BACKEND_PORT__` in localStorage via initScript
- Frontend reads from localStorage for all API calls
- Firebase SDK connects to stub using localStorage port

### CORS Configuration
```python
# backend/src/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Test Performance & Reliability
- **Setup:** ~1s per test (backend + stub startup)
- **Execution:** Parallel with 2 workers (8 tests in 8s)
- **Isolation:** Each test gets unique database file + ports
- **Port allocation:** Atomic locking prevents race conditions
- **Scalability:** Can handle 500+ tests before needing test pyramid
- **CI/CD:** Pre-push hooks validate build + tests before allowing push

## 🎨 UI Patterns Established

### Modal Pattern
```tsx
const [showCreateModal, setShowCreateModal] = useState(false)
const [creating, setCreating] = useState(false)

// Form submission
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault()
  setCreating(true)
  try {
    const res = await fetch(...)
    if (!res.ok) throw new Error(...)
    setShowCreateModal(false) // Close on success
    fetchData() // Refresh
  } catch (err) {
    console.error(err)
    alert(`Failed: ${err.message}`)
  } finally {
    setCreating(false)
  }
}
```

### Hydration Pattern (E2E Tests)
```typescript
// Accumulate data for fast setup
this.hydration?.accumulate('organizations', [...])

// Also create via real API so backend has the data
await this.page.request.post(`http://localhost:${port}/api/orgs`, ...)
```

## 📊 Test Status

**Frontend E2E:** 8/8 passing (8s total, 2 workers)
**Backend BDD:** 107/107 passing (2.75s) - includes all organization model tests
**Code Quality:** Zero warnings (ruff + ty)
**Production Build:** ✅ 369KB (test utilities tree-shaken)
**Pre-push Validation:** ✅ Build + tests must pass before push
**Production Deployment:** ✅ Successfully deployed with migration applied

## 🚀 Running the Stack

```bash
# Start backend dev server
cd backend && make dev

# Start frontend dev server
cd frontend && make dev

# Run E2E tests
cd frontend && make test

# Run backend BDD tests
cd backend && make test-ci
```

## 🔗 Related Documentation

- [Frontend Architecture](/docs/002-architecture/004-frontend-architecture.md)
- [MVP Information Architecture](/docs/001-overview/mvp_information_architecture.md)
- [Self-Led Interviews Design](/docs/003-plans/001-initial-plan/02_self_led_interviews.md)
