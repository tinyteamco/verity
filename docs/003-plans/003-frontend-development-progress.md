# Frontend Development Progress

**Last Updated:** 2025-10-06
**Status:** Phase 3 Complete - shadcn/ui Integration & Single-Page UX

## 🎯 Current Objective

Building out the UX to validate backend implementation, following a super admin → organization admin → user workflow (working inward from platform administration).

## ✅ Completed

### E2E Test Infrastructure
- **Real-mode only testing** - Removed all mock mode logic
- **Complete test isolation** - Each test gets unique database + backend + Firebase stub
- **Dynamic port allocation** - Atomic port locking prevents race conditions
- **Fast parallel execution** - 1s setup per test, runs with 2 workers (13 tests in 14s)
- **Hydration for speed** - Accumulate test data + real API calls for fast setup
- **Firebase Auth Stub** - Lightweight FastAPI replacement for emulator (<1s startup vs 12-15s)
- **All tests passing** - 13 frontend E2E (14s total) + 107 backend BDD tests
- **Pre-push validation** - Build + tests run before allowing push to prevent CI failures
- **Modal UX testing** - Tests updated to work with shadcn Dialog components (Radix UI primitives)

### Frontend Stack
- **React** + TypeScript + Vite
- **Jotai** for state management
- **shadcn/ui** + Tailwind CSS for UI components
- **Radix UI** primitives (via shadcn/ui) for accessible components
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

#### 6. Study Management ✅
- Create study in organization (modal-based)
- View studies list in organization detail page
- Edit study details (click study → modal)
- Delete study with confirmation
- Full E2E test coverage

#### 7. shadcn/ui Design System Integration ✅
- **Component library:** shadcn/ui with Tailwind CSS utility classes
- **Accessible primitives:** Radix UI for Dialog, Select, Input components
- **Complete refactor:** LoginPage, Dashboard, OrganizationDetailPage
- **Modal pattern:** All CRUD operations use Dialog components (accessible, keyboard navigable)
- **Consistent styling:** Card containers, proper spacing, muted text colors
- **Form patterns:** Label + Input/Textarea/Select with proper focus states

#### 8. Single-Page UX Pattern ✅
- **Design decision:** Consolidate all organization features onto OrganizationDetailPage
- **Rationale:** Avoid creating separate pages for each feature (users, studies)
- **Implementation:** Modal-based interactions instead of route navigation
- **Benefits:**
  - Faster interactions (no page loads)
  - Better context retention (stay on same page)
  - Simpler routing structure
  - More cohesive UX
- **Pattern applied to:** Add User, Create/Edit/Delete Study

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
Scenario: View empty studies list for organization
Scenario: Create a new study
Scenario: Edit study details
Scenario: Delete study
Scenario: View multiple studies
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

### Phase 3: Study Management & Design System (completed ✅)

1. ✅ **shadcn/ui Integration**
   - Installed Tailwind CSS, PostCSS, Autoprefixer
   - Initialized shadcn/ui with New York style
   - Added components: Button, Card, Dialog, Input, Label, Select, Textarea
   - Refactored all pages: LoginPage, Dashboard, OrganizationDetailPage

2. ✅ **Single-Page UX Refactor**
   - Consolidated organization features onto OrganizationDetailPage
   - Modal-based interactions (no separate pages for users/studies)
   - Updated E2E tests to work with modal UX

3. ✅ **Study CRUD Implementation**
   - Create study modal with title + description
   - Edit study modal (click study title)
   - Delete study confirmation modal
   - All modals use shadcn Dialog components
   - Full E2E test coverage (5 scenarios)

### Phase 4: Interview Flow
- Generate interview link
- Test interview as participant (link-based access)
- View interview results

## 📁 File Structure

```
frontend/
├── src/
│   ├── App.tsx                         # Main app with routing + Dashboard
│   ├── components/ui/                  # shadcn/ui components
│   │   ├── button.tsx                 # Button component
│   │   ├── card.tsx                   # Card container component
│   │   ├── dialog.tsx                 # Modal/Dialog component
│   │   ├── input.tsx                  # Text input component
│   │   ├── label.tsx                  # Form label component
│   │   ├── select.tsx                 # Dropdown select component
│   │   └── textarea.tsx               # Multi-line text input
│   ├── atoms/
│   │   ├── auth.ts                    # User auth state (Jotai)
│   │   └── organizations.ts           # Organizations list state
│   ├── lib/
│   │   ├── firebase.ts                # Firebase config + stub detection
│   │   ├── auth-persistence.ts        # Auth state persistence
│   │   └── utils.ts                   # Tailwind utility helpers
│   └── pages/
│       ├── LoginPage.tsx              # Login UI (shadcn styled)
│       └── OrganizationDetailPage.tsx # Single-page org view with modals
│
├── tests/
│   ├── features/
│   │   ├── org-management.feature     # Organization BDD scenarios
│   │   └── study-management.feature   # Study BDD scenarios
│   ├── steps/
│   │   ├── org-management.steps.ts    # Org step implementations
│   │   └── study-management.steps.ts  # Study step implementations
│   └── support/
│       ├── world.ts                   # Test fixture with backend orchestration
│       ├── fixtures.ts                # Test helpers (login, seed data)
│       ├── hydration-registry.ts      # Hydration schemas
│       └── bdd-hydration.ts           # Hydration accumulator
│
├── tailwind.config.js                  # Tailwind CSS configuration
├── components.json                     # shadcn/ui configuration
└── postcss.config.js                   # PostCSS configuration

backend/
├── scripts/
│   ├── start_e2e_backend.sh           # E2E test orchestration script
│   └── firebase_auth_stub.py          # Lightweight Firebase emulator replacement
└── src/api/main.py                    # API endpoints
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

### shadcn Dialog Modal Pattern
```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

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

return (
  <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
    <DialogContent data-testid="create-modal">
      <DialogHeader>
        <DialogTitle>Create Item</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="title">Title</Label>
          <Input id="title" data-testid="title-input" autoFocus />
        </div>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
            Cancel
          </Button>
          <Button type="submit" disabled={creating}>
            {creating ? 'Creating...' : 'Create'}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
)
```

### Single-Page UX Pattern
**Design Decision:** Consolidate related features onto one page using modals instead of creating separate routes.

```tsx
// ❌ Before: Separate pages requiring navigation
/orgs/:id → Organization details
/orgs/:id/users → User management
/orgs/:id/studies → Study list
/orgs/:id/studies/:studyId → Study edit

// ✅ After: Single page with modal interactions
/orgs/:id → Organization details (all features)
  - Click "Add User" → Modal
  - Click "Create Study" → Modal
  - Click study title → Edit modal
  - Click "Delete" → Confirmation modal

// Benefits:
// - Faster (no page loads)
// - Better context retention
// - Simpler routing
// - More cohesive UX
```

### Hydration Pattern (E2E Tests)
```typescript
// Accumulate data for fast setup
this.hydration?.accumulate('organizations', [...])

// Also create via real API so backend has the data
await this.page.request.post(`http://localhost:${port}/api/orgs`, ...)
```

## 📊 Test Status

**Frontend E2E:** 13/13 passing (14s total, 2 workers) - Org management (8) + Study management (5)
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
