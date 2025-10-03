# Frontend Architecture & Testing Strategy

## Overview

The Verity frontend is a React-based web application for UXR (User Experience Research) platform administration and interview management. The architecture prioritizes **fast, reliable E2E testing** that can run on every commit while maintaining confidence in production behavior.

## Core Principles

1. **BDD-First Development** - All features start with Gherkin scenarios before implementation
2. **Dual-Mode Testing** - Tests run against mocked or real backend without code changes
3. **State Hydration** - Complex UI states can be injected directly for fast test setup using [@tinyteamco/hydration-test-utils](https://github.com/tinyteamco/hydration-test-utils)
4. **User-Facing Validation** - Every commit validates user-visible behavior
5. **Type Safety** - TypeScript throughout, validated at build time

## Technology Stack

### Core Framework
- **Vite** - Build tool (fast HMR, optimized production builds)
- **React 18** - UI library
- **TypeScript** - Type safety and IDE support

### State Management
- **Jotai** - Atomic state management (hydration-friendly, minimal boilerplate)
- **TanStack Query** - Server state management (caching, refetching, optimistic updates)

**Why Jotai:**
- Atoms are serializable (enables state hydration for tests)
- Minimal boilerplate compared to Redux/Zustand
- Excellent TypeScript support
- Works seamlessly with React Suspense
- **Required for hydration-test-utils compatibility**

**State Architecture:**
```typescript
// Jotai atoms = source of truth for UI state
const userAtom = atom<User | null>(null)
const studiesAtom = atom<Study[]>([])

// TanStack Query = API fetching layer
const useStudies = () => {
  const [, setStudies] = useAtom(studiesAtom)

  return useQuery({
    queryKey: ['studies'],
    queryFn: fetchStudies,
    onSuccess: (data) => setStudies(data)  // Write to Jotai
  })
}

// Components = read from Jotai
function StudiesList() {
  const [studies] = useAtom(studiesAtom)
  return <div>{studies.map(...)}</div>
}
```

### Routing
- **TanStack Router** - Type-safe routing with excellent TypeScript inference

### UI Components
- **shadcn/ui** - Copy-paste component library (Radix UI + Tailwind CSS)
- **Tailwind CSS** - Utility-first CSS framework

**Why shadcn:**
- Components copied into your codebase (full ownership/customization)
- Built on accessible primitives (Radix UI)
- Modern aesthetic
- No runtime CSS-in-JS overhead

### Authentication
- **Firebase Auth SDK** - Client-side authentication
- **JWT tokens** - Passed to backend API in `Authorization: Bearer` header

### Testing
- **Playwright** - Browser automation
- **@cucumber/cucumber + playwright-bdd** - BDD test framework
- **@tinyteamco/hydration-test-utils** - State injection for fast test setup (IMPORTANT: Use this library, do NOT reimplement)
- **Playwright route interception** - API mocking

## Testing Architecture

### The Dual-Mode Pattern

Tests can run in two modes without changing test code:

#### Mock Mode (Default)
```bash
E2E_BACKEND=mock npm run test:e2e
```
- API requests intercepted and mocked
- State hydrated directly via **hydration-test-utils**
- **Fast:** 2-5 seconds per test
- **Reliable:** No network dependencies
- **Flexible:** Easy to test edge cases
- **Use case:** Pre-commit hooks, CI on every PR

#### Real Mode
```bash
E2E_BACKEND=real npm run test:e2e
```
- API requests hit actual backend (local or deployed)
- State created through real API calls
- **Slow:** 10-30 seconds per test
- **High confidence:** Validates full integration
- **Use case:** Nightly builds, pre-deployment validation

### Test Structure

```
frontend/
├── tests/
│   ├── features/              # Gherkin feature files
│   │   ├── org-management.feature
│   │   ├── study-creation.feature
│   │   └── interview-flow.feature
│   ├── steps/                 # Step definitions (Playwright actions)
│   │   ├── org-management.steps.ts
│   │   ├── study-creation.steps.ts
│   │   └── common.steps.ts
│   ├── support/
│   │   ├── fixtures.ts        # Test fixture API (mode-agnostic)
│   │   ├── hydration-registry.ts  # Hydration registry for hydration-test-utils
│   │   ├── mocks.ts           # API mock handlers
│   │   └── world.ts           # Cucumber world context
│   └── playwright.config.ts
```

### Feature File Example

```gherkin
Feature: Study Management
  As a researcher
  I want to create and manage studies
  So I can organize my research projects

  Background:
    Given I am logged in as "alice@acme.com" in organization "Acme Corp"

  Scenario: Create first study
    Given I am on the dashboard page
    When I click "New Study"
    And I enter study title "Onboarding Research"
    And I click "Create"
    Then I see "Onboarding Research" in my studies list

  @smoke @real-backend
  Scenario: Create study with real backend
    # This scenario runs in both mock and real mode
    # Validates end-to-end integration
    Given I am on the dashboard page
    When I create a new study via the UI
    Then the study appears in the backend database
```

## State Hydration with hydration-test-utils

### Overview

We use [@tinyteamco/hydration-test-utils](https://github.com/tinyteamco/hydration-test-utils) to inject application state directly in tests. **DO NOT reimplement this library - use it as a dependency.**

### Why Hydration?

**Without hydration (slow):**
```typescript
// Must click through entire flow
await page.goto('/login')
await page.fill('[name=email]', 'alice@acme.com')
await page.click('button:has-text("Sign In")')
await page.waitForURL('/dashboard')
await page.click('text=New Study')
await page.fill('[name=title]', 'Study 1')
await page.click('button:has-text("Create")')
// 15 seconds elapsed
await page.click('text=Study 1')  // Finally test the actual feature
```

**With hydration (fast):**
```typescript
// Inject state directly
await hydratePage(page, {
  data: {
    user: { email: 'alice@acme.com', orgId: 1, role: 'owner' },
    studies: [{ id: 1, title: 'Study 1', orgId: 1 }]
  }
})
await page.goto('/studies/1')  // Go directly to feature under test
// 2 seconds elapsed
```

### Setup

#### 1. Install the library

```bash
npm install @tinyteamco/hydration-test-utils zod
```

#### 2. Define Hydration Registry

Create schemas and map them to your Jotai atoms:

```typescript
// tests/support/hydration-registry.ts
import { z } from 'zod'
import { atom } from 'jotai'
import type { HydrationRegistry } from '@tinyteamco/hydration-test-utils'

// Define schemas matching your app state
const userSchema = z.object({
  id: z.number(),
  email: z.string().email(),
  orgId: z.number(),
  organizationName: z.string(),
  role: z.enum(['owner', 'admin', 'member', 'super_admin']),
  firebaseUid: z.string()
})

const studySchema = z.object({
  id: z.number(),
  title: z.string(),
  orgId: z.number(),
  createdAt: z.string()
})

const interviewSchema = z.object({
  id: z.number(),
  studyId: z.number(),
  accessToken: z.string(),
  status: z.enum(['pending', 'completed']),
  createdAt: z.string()
})

// Import your atoms (these should be defined in your src/ code)
import {
  userIdAtom,
  userEmailAtom,
  userOrgIdAtom,
  userOrganizationNameAtom,
  userRoleAtom,
  userFirebaseUidAtom,
  studiesAtom,
  interviewsAtom
} from '../../src/atoms'

// Create the hydration registry
export const hydrationRegistry: HydrationRegistry = {
  user: {
    schema: userSchema,
    atoms: {
      id: userIdAtom,
      email: userEmailAtom,
      orgId: userOrgIdAtom,
      organizationName: userOrganizationNameAtom,
      role: userRoleAtom,
      firebaseUid: userFirebaseUidAtom
    }
  },
  studies: {
    schema: z.array(studySchema),
    atoms: {
      // For array data, use a single atom that holds the array
      _data: studiesAtom  // Convention: _data for array atoms
    }
  },
  interviews: {
    schema: z.array(interviewSchema),
    atoms: {
      _data: interviewsAtom
    }
  }
}

export type User = z.infer<typeof userSchema>
export type Study = z.infer<typeof studySchema>
export type Interview = z.infer<typeof interviewSchema>
```

#### 3. Bootstrap in Application

Initialize hydration in your app entry point (only runs in dev/test):

```typescript
// src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { bootstrapHydration } from '@tinyteamco/hydration-test-utils'
import { hydrationRegistry } from '../tests/support/hydration-registry'
import App from './App'

// Bootstrap hydration BEFORE rendering
// This checks for hydration data and applies it to atoms
// Only runs when hydration data is present (safe for production)
await bootstrapHydration(hydrationRegistry, {
  strict: true,  // Enforce schema-atom consistency
  timeoutMs: 3000  // Wait for persisted atoms
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
```

### Usage in Tests

#### Basic Hydration

```typescript
// tests/steps/study.steps.ts
import { Given, When, Then } from '@cucumber/cucumber'
import { hydratePage } from '@tinyteamco/hydration-test-utils/playwright'

Given('I am logged in as {string} in organization {string}',
  async ({ page }, email: string, orgName: string) => {
    await hydratePage(page, {
      data: {
        user: {
          id: 1,
          email,
          orgId: 1,
          organizationName: orgName,
          role: 'owner',
          firebaseUid: 'test-user-1'
        }
      },
      url: '/dashboard'  // Navigate after hydration
    })
  }
)

Given('a study {string} exists', async ({ page }, title: string) => {
  // Hydrate studies data
  await hydratePage(page, {
    data: {
      studies: [{
        id: 1,
        title,
        orgId: 1,
        createdAt: new Date().toISOString()
      }]
    }
  })
})
```

#### Complex State Example

```typescript
test('view completed interview with transcript', async ({ page }) => {
  await hydratePage(page, {
    data: {
      user: {
        id: 1,
        email: 'alice@acme.com',
        role: 'owner',
        orgId: 1,
        organizationName: 'Acme Corp',
        firebaseUid: 'test-uid-1'
      },
      studies: [{
        id: 1,
        title: 'Research',
        orgId: 1,
        createdAt: new Date().toISOString()
      }],
      interviews: [{
        id: 1,
        studyId: 1,
        status: 'completed',
        accessToken: 'abc123',
        createdAt: new Date().toISOString()
      }],
      transcripts: [{
        id: 1,
        interviewId: 1,
        fullText: 'Mock transcript content...',
        segments: []
      }]
    },
    url: '/studies/1/interviews/1'
  })

  // State is already loaded - test immediately
  await expect(page.getByTestId('transcript')).toBeVisible()
  await expect(page.getByTestId('transcript')).toContainText('Mock transcript content')
})
```

### Dual-Mode Fixture API

Wrap hydration in a fixture API that works in both mock and real modes:

```typescript
// tests/support/fixtures.ts
import { Page } from '@playwright/test'
import { hydratePage } from '@tinyteamco/hydration-test-utils/playwright'
import type { User, Study, Interview } from './hydration-registry'

type BackendMode = 'mock' | 'real'

export class TestFixtures {
  constructor(
    private page: Page,
    private mode: BackendMode = process.env.E2E_BACKEND as BackendMode || 'mock'
  ) {}

  async loginAs(email: string, orgName: string = 'Test Org'): Promise<void> {
    if (this.mode === 'mock') {
      // Use hydration-test-utils
      await hydratePage(this.page, {
        data: {
          user: {
            id: 1,
            email,
            orgId: 1,
            organizationName: orgName,
            role: 'owner',
            firebaseUid: 'test-uid-1'
          }
        },
        url: '/dashboard'
      })

      // Mock Firebase auth token
      await this.page.evaluate(() => {
        localStorage.setItem('firebase_token', 'mock-jwt-token')
      })
    } else {
      // Real Firebase sign-in
      await this.page.goto('/login')
      await this.page.fill('[name=email]', email)
      await this.page.fill('[name=password]', 'test-password')
      await this.page.click('button:has-text("Sign In")')
      await this.page.waitForURL('/dashboard')
    }
  }

  async createStudy(title: string): Promise<Study> {
    if (this.mode === 'mock') {
      // Use hydration-test-utils
      const study: Study = {
        id: randomId(),
        title,
        orgId: 1,
        createdAt: new Date().toISOString()
      }

      await hydratePage(this.page, {
        data: { studies: [study] }
      })

      await this.page.reload()
      return study
    } else {
      // Real API call
      const response = await fetch('http://localhost:8000/api/studies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title })
      })
      return response.json()
    }
  }

  async createInterview(studyId: number): Promise<Interview> {
    if (this.mode === 'mock') {
      const interview: Interview = {
        id: randomId(),
        studyId,
        status: 'pending',
        accessToken: generateToken(),
        createdAt: new Date().toISOString()
      }

      await hydratePage(this.page, {
        data: { interviews: [interview] }
      })

      await this.page.reload()
      return interview
    } else {
      // Real API call
      const response = await fetch(`http://localhost:8000/api/studies/${studyId}/interviews/generate-link`, {
        method: 'POST'
      })
      return response.json()
    }
  }
}

function randomId(): number {
  return Math.floor(Math.random() * 1000000)
}

function generateToken(): string {
  return Math.random().toString(36).substring(7)
}
```

### Step Definitions Use Fixtures

```typescript
// tests/steps/common.steps.ts
import { Given, When, Then, Before } from '@cucumber/cucumber'
import { TestFixtures } from '../support/fixtures'

// Create fixtures instance for each scenario
Before(async function() {
  this.fixtures = new TestFixtures(this.page)
})

Given('I am logged in as {string}', async function(email: string) {
  await this.fixtures.loginAs(email)
})

Given('a study {string} exists', async function(title: string) {
  await this.fixtures.createStudy(title)
})

Given('an interview link exists for study {int}', async function(studyId: number) {
  this.interview = await this.fixtures.createInterview(studyId)
})
```

### Important Notes

1. **DO NOT reimplement hydration** - Always use `hydratePage()` from `@tinyteamco/hydration-test-utils/playwright`
2. **Bootstrap in app entry point** - Call `bootstrapHydration()` before rendering React
3. **Define proper schemas** - Use Zod for validation (catches test data errors)
4. **Map schemas to atoms** - Registry must match your Jotai atom structure
5. **Use fixtures for mode abstraction** - Tests don't know if they're in mock or real mode

## API Mocking (Mock Mode)

When in mock mode, intercept API calls with Playwright route handlers:

```typescript
// tests/support/mocks.ts
import { Page, Route } from '@playwright/test'

export async function setupApiMocks(page: Page): Promise<void> {
  await page.route('**/api/**', async (route) => {
    const url = new URL(route.request().url())
    const method = route.request().method()
    const path = url.pathname.replace('/api', '')
    const key = `${method} ${path}` as MockKey

    const handler = mockHandlers[key]

    if (handler) {
      const response = await handler(route)
      await route.fulfill(response)
    } else {
      console.warn(`No mock handler for ${method} ${path}`)
      await route.abort('failed')
    }
  })
}

type MockKey = keyof typeof mockHandlers

const mockHandlers = {
  'GET /studies': async (route: Route) => ({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ studies: [] })
  }),

  'POST /studies': async (route: Route) => {
    const body = await route.request().postDataJSON()
    return {
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        id: randomId(),
        ...body,
        createdAt: new Date().toISOString()
      })
    }
  },

  'POST /studies/*/interviews/generate-link': async (route: Route) => ({
    status: 201,
    contentType: 'application/json',
    body: JSON.stringify({
      id: randomId(),
      studyId: 1,
      accessToken: generateToken(),
      status: 'pending',
      link: `http://localhost:5173/interview/${generateToken()}`
    })
  })
}

function randomId(): number {
  return Math.floor(Math.random() * 1000000)
}

function generateToken(): string {
  return Math.random().toString(36).substring(7)
}
```

Setup mocks in Cucumber world:

```typescript
// tests/support/world.ts
import { Before } from '@cucumber/cucumber'
import { setupApiMocks } from './mocks'

Before(async function() {
  const mode = process.env.E2E_BACKEND || 'mock'

  if (mode === 'mock') {
    await setupApiMocks(this.page)
  }
})
```

## CI/CD Strategy

### Pre-commit Hooks
```bash
# .hk/pre-commit (runs via hk + mise)
cd frontend
E2E_BACKEND=mock npm run test:e2e  # Fast mock mode tests only
```

### GitHub Actions - PR Validation
```yaml
jobs:
  frontend-tests-fast:
    runs-on: ubuntu-latest
    steps:
      - run: npm ci
      - run: E2E_BACKEND=mock npm run test:e2e
      # Takes 1-2 minutes for full suite
```

### GitHub Actions - Nightly Integration Tests
```yaml
jobs:
  frontend-tests-integration:
    runs-on: ubuntu-latest
    steps:
      - run: docker compose up -d  # Start backend
      - run: E2E_BACKEND=real npm run test:e2e
      # Takes 10-15 minutes, catches integration issues
```

### GitHub Actions - Pre-deployment
```yaml
jobs:
  frontend-tests-smoke:
    runs-on: ubuntu-latest
    steps:
      - run: docker compose up -d
      - run: E2E_BACKEND=real npm run test:e2e -- --grep @smoke
      # Run critical paths against real backend before deploy
```

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx                 # App entry point (bootstrapHydration here)
│   ├── App.tsx                  # Root component with providers
│   ├── routes/                  # TanStack Router routes
│   │   ├── __root.tsx          # Root layout
│   │   ├── index.tsx           # Home/redirect
│   │   ├── login.tsx           # Public login page
│   │   ├── _authenticated/     # Protected routes
│   │   │   ├── dashboard.tsx
│   │   │   ├── studies/
│   │   │   │   ├── index.tsx   # Studies list
│   │   │   │   └── $id.tsx     # Study detail
│   │   │   └── organizations/  # Super admin only
│   │   │       └── index.tsx
│   │   └── interview/
│   │       └── $token.tsx      # Public interviewee page
│   ├── components/
│   │   ├── ui/                 # shadcn components
│   │   ├── layout/             # Layout components
│   │   └── features/           # Feature-specific components
│   ├── lib/
│   │   ├── api.ts              # API client (axios/fetch)
│   │   ├── firebase.ts         # Firebase Auth setup
│   │   └── utils.ts            # Utility functions
│   ├── hooks/
│   │   ├── useAuth.ts          # Auth state hooks
│   │   ├── useStudies.ts       # TanStack Query hooks
│   │   └── useInterviews.ts
│   └── atoms/
│       ├── auth.ts             # Jotai atoms for auth
│       ├── studies.ts          # Jotai atoms for studies
│       └── interviews.ts       # Jotai atoms for interviews
├── tests/
│   ├── features/               # Gherkin scenarios
│   ├── steps/                  # Step definitions
│   └── support/
│       ├── fixtures.ts         # Test fixture API (mode-agnostic)
│       ├── hydration-registry.ts  # Registry for hydration-test-utils
│       ├── mocks.ts            # API mock handlers
│       └── world.ts            # Cucumber world context
├── public/
├── playwright.config.ts
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

## Development Workflow

### 1. Write Gherkin Feature
```gherkin
Feature: Interview Link Generation
  Scenario: Researcher generates link
    Given I have a study "Research"
    When I click "Generate Link"
    Then I see a shareable interview URL
```

### 2. Generate Step Skeletons
```bash
npm run test:e2e -- --dry-run
# Outputs missing step definitions
```

### 3. Implement Steps (using fixtures)
```typescript
Given('I have a study {string}', async ({ fixtures }, title) => {
  await fixtures.createStudy(title)
})

When('I click {string}', async ({ page }, buttonText) => {
  await page.click(`button:has-text("${buttonText}")`)
})

Then('I see a shareable interview URL', async ({ page }) => {
  await expect(page.locator('[data-testid=interview-link]')).toBeVisible()
})
```

### 4. Run Tests (they fail - red)
```bash
E2E_BACKEND=mock npm run test:e2e
```

### 5. Implement UI Components
```tsx
// src/components/features/InterviewLinkGenerator.tsx
export function InterviewLinkGenerator({ studyId }: Props) {
  const [link, setLink] = useState<string>()

  const generateLink = async () => {
    const response = await apiClient.post(`/studies/${studyId}/interviews/generate-link`)
    setLink(response.data.link)
  }

  return (
    <div>
      <button onClick={generateLink}>Generate Link</button>
      {link && <div data-testid="interview-link">{link}</div>}
    </div>
  )
}
```

### 6. Tests Pass (green)
```bash
E2E_BACKEND=mock npm run test:e2e  # ✅ All tests pass
```

### 7. Validate Against Real Backend
```bash
E2E_BACKEND=real npm run test:e2e  # ✅ Integration validated
```

### 8. Commit (pre-commit hook runs mock tests)
```bash
git add .
git commit -m "feat: add interview link generation"
# Hook runs: E2E_BACKEND=mock npm run test:e2e
# ✅ Passes, commit succeeds
```

## Key Architectural Decisions

### 1. Why Jotai over Redux/Zustand?
- **Hydration-friendly:** Required for hydration-test-utils compatibility
- **Minimal boilerplate:** No reducers, actions, or middleware
- **React-first:** Built for hooks, works with Suspense
- **TypeScript:** Excellent type inference

### 2. Why TanStack Query with Jotai?
- **TanStack Query** handles fetching, caching, revalidation
- **Jotai** stores the data for UI consumption
- **Separation of concerns:** Query = server sync, Jotai = client state

### 3. Why Use hydration-test-utils?
- **Battle-tested:** Proven pattern in production
- **Avoid reinventing:** Complex edge cases already handled
- **Maintained:** Updates for new Jotai/Playwright versions
- **Type-safe:** Full TypeScript support with Zod validation

### 4. Why Mock AND Real modes?
- **Fast feedback loop:** Mock mode enables testing on every commit
- **High confidence:** Real mode catches integration bugs before production
- **Flexibility:** Test edge cases easily in mock mode

### 5. Why Cucumber for Frontend?
- **Consistency:** Same BDD workflow as backend
- **Agent-friendly:** Gherkin is clear specification language
- **Forces discipline:** Given/When/Then structure prevents sloppy tests

## Performance Considerations

### Bundle Size
- **shadcn components:** Only ship what you use (tree-shakeable)
- **Jotai:** ~3kb gzipped
- **TanStack Query:** ~12kb gzipped
- **hydration-test-utils:** 0kb in production (dev-only)
- **Target:** <150kb initial bundle (gzipped)

### Test Speed
- **Mock mode:** Target <5 seconds per test
- **Real mode:** Target <30 seconds per test
- **Full suite (mock):** Target <3 minutes on CI

### Development Experience
- **Vite HMR:** <200ms hot reload
- **TypeScript checking:** Background process
- **Test watch mode:** Re-run only changed tests

## Security

### Authentication Flow
1. User signs in via Firebase Auth (client-side)
2. Firebase returns JWT token
3. Frontend stores token in memory (not localStorage)
4. Token passed in `Authorization: Bearer` header
5. Backend validates JWT

### Hydration Security
- `bootstrapHydration()` is safe - no-op when data not present
- No special production configuration needed
- hydration-test-utils only activates when test data injected

### CORS Configuration
Backend must allow frontend origin:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://app.verity.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## References

- [TanStack Router](https://tanstack.com/router)
- [TanStack Query](https://tanstack.com/query)
- [Jotai](https://jotai.org)
- [Playwright](https://playwright.dev)
- [shadcn/ui](https://ui.shadcn.com)
- [Firebase Auth](https://firebase.google.com/docs/auth)
- [hydration-test-utils](https://github.com/tinyteamco/hydration-test-utils) - **REQUIRED, do not reimplement**
