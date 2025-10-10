# Quickstart: Study Management UI

**Feature**: Study Management UI
**Target Audience**: Developers implementing this feature
**Prerequisites**: Verity development environment set up (`make bootstrap` completed)

## Setup

```bash
# Navigate to project root
cd /Users/jkp/Work/tinyteam/verity

# Ensure on feature branch
git checkout 001-study-management-ui

# Start backend + services (in terminal 1)
make backend-dev

# Start frontend dev server (in terminal 2)
make frontend-dev
```

## Development Workflow (BDD-First)

### Step 1: Write BDD Scenarios

Create `frontend/tests/features/study-generation.feature`:

```gherkin
Feature: Automated Study Generation
  As an organization user
  I want to generate a study from a research topic
  So I can quickly create interview guides

  Background:
    Given I am logged in as super admin "admin@tinyteam.co"
    And organization "Research Corp" exists

  Scenario: Generate study from topic
    When I navigate to organization "Research Corp" studies page
    And I click "Generate Study"
    And I enter "How do people shop in supermarkets?" as the topic
    And I submit the generation form
    Then I see a loading indicator
    And after generation completes, I see a new study with generated title
    And I see the interview guide content

  Scenario: Edit interview guide
    Given organization "Research Corp" has a study with an interview guide
    When I navigate to the study detail page
    And I click "Edit Guide"
    And I modify the interview guide content
    And I click "Save"
    Then I see "Guide saved successfully"
    And the updated content is displayed
```

### Step 2: Run Tests (Watch Them Fail)

```bash
# Run frontend E2E tests
make frontend-test

# Expected: New scenarios fail (not implemented)
```

### Step 3: Implement Components

**3a. Add Generate Button to StudyListPage**

```typescript
// frontend/src/pages/StudyListPage.tsx
<button onClick={() => setShowGenerateModal(true)}>
  Generate Study
</button>
```

**3b. Create StudyGeneratePage Component**

```typescript
// frontend/src/pages/StudyGeneratePage.tsx
export function StudyGeneratePage() {
  const [topic, setTopic] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  async function handleGenerate() {
    // Call POST /api/orgs/{orgId}/studies/generate
  }

  return (
    <div>
      <h1>What do you want to learn?</h1>
      <textarea value={topic} onChange={...} />
      <button onClick={handleGenerate}>Generate</button>
    </div>
  );
}
```

**3c. Create StudyGuideEditor Component**

```typescript
// frontend/src/components/StudyGuideEditor.tsx
export function StudyGuideEditor({ guide, onSave }) {
  const [content, setContent] = useState(guide.content_md);
  const [showPreview, setShowPreview] = useState(false);

  return (
    <div>
      <textarea value={content} onChange={...} />
      {showPreview && <ReactMarkdown>{content}</ReactMarkdown>}
      <button onClick={handleSave}>Save</button>
    </div>
  );
}
```

### Step 4: Run Tests Again (Watch Them Pass)

```bash
make frontend-test

# Expected: All scenarios pass
```

### Step 5: Code Quality Checks

```bash
# Run all quality checks
make frontend-check

# Fix any issues
make frontend-format  # Auto-fix formatting
```

### Step 6: Run Full Test Suite

```bash
# Run all tests (frontend + backend)
make test

# Ensure nothing broken
```

## Key Files to Modify

### Frontend

**Pages**:
- `frontend/src/pages/StudyListPage.tsx` - Add "Generate Study" button
- `frontend/src/pages/StudyDetailPage.tsx` - Add guide display + edit mode
- `frontend/src/pages/StudyGeneratePage.tsx` - NEW - topic input form

**Components**:
- `frontend/src/components/StudyGuideEditor.tsx` - NEW - markdown editor
- `frontend/src/components/StudyGuideViewer.tsx` - NEW - rendered markdown

**API Client**:
- `frontend/src/lib/api.ts` - Add `generateStudy()`, `getGuide()`, `updateGuide()`

**Tests**:
- `frontend/tests/features/study-generation.feature` - NEW - BDD scenarios
- `frontend/tests/step_defs/study_generation_steps.ts` - NEW - step implementations

### Backend (Only if Needed)

If you need to modify backend endpoints:

**Models** (if schema changes):
- `backend/src/models.py` - Study, InterviewGuide models

**API Routes**:
- `backend/src/api/main.py` - Endpoints at lines ~498, ~714, ~758

**Tests**:
- `backend/tests/features/study_guides.feature` - Update scenarios if endpoints change

## API Endpoints (Current Implementation)

**Generate Study**:
```bash
curl -X POST http://localhost:8000/api/orgs/{orgId}/studies/generate \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"topic": "How do people shop in supermarkets?"}'
```

**Get Guide**:
```bash
curl http://localhost:8000/api/studies/{studyId}/guide \
  -H "Authorization: Bearer {token}"
```

**Update Guide**:
```bash
curl -X PUT http://localhost:8000/api/studies/{studyId}/guide \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"content_md": "# New content..."}'
```

## Common Issues & Solutions

### Issue: Generation Takes Too Long

**Solution**: Add client-side timeout + retry logic

```typescript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 60000);

try {
  const response = await fetch(url, {
    signal: controller.signal,
    // ... other options
  });
} catch (error) {
  if (error.name === 'AbortError') {
    // Show timeout error + retry button
  }
}
```

### Issue: Unsaved Changes Lost on Navigation

**Solution**: Add beforeunload warning

```typescript
useEffect(() => {
  const handleBeforeUnload = (e) => {
    if (isDirty) {
      e.preventDefault();
      e.returnValue = '';
    }
  };

  window.addEventListener('beforeunload', handleBeforeUnload);
  return () => window.removeEventListener('beforeunload', handleBeforeUnload);
}, [isDirty]);
```

### Issue: Markdown Not Rendering Correctly

**Solution**: Use `react-markdown` with proper sanitization

```typescript
import ReactMarkdown from 'react-markdown';

<ReactMarkdown>{content}</ReactMarkdown>
```

## Testing Tips

### Manual Testing Flow

1. **Generate Study**:
   - Navigate to studies page
   - Click "Generate Study"
   - Enter topic: "How do freelancers choose tools?"
   - Wait for generation (~30s)
   - Verify redirected to new study detail page

2. **View Guide**:
   - Check study detail page shows interview guide
   - Verify markdown is rendered (not raw text)
   - Check for welcome message, sections, questions

3. **Edit Guide**:
   - Click "Edit Guide"
   - Modify content in textarea
   - Toggle preview to see rendered markdown
   - Click "Save"
   - Verify content persists after page reload

4. **Error Handling**:
   - Test with empty topic (validation error)
   - Test with network disconnected (save error)
   - Test navigation away with unsaved changes (warning)

### BDD Testing with Playwright

```bash
# Run specific feature file
npm test -- study-generation.feature

# Run with headed browser (see what's happening)
npm test -- --headed

# Run with debug mode
npm test -- --debug

# Generate Playwright report
npx playwright show-report
```

## Deployment

### Push & Monitor CI/CD

```bash
# Commit changes
git add .
git commit -m "feat: add study generation UI"

# Push and wait for CI
git push origin 001-study-management-ui

# Monitor GitHub Actions
gh run watch

# If CI passes, verify deployment
curl https://verity-backend-xyz.run.app/healthz
```

### Manual Deployment Check

After CI completes:
1. Check GitHub Actions logs for deployment success
2. Verify health check: `curl https://{deployed-url}/healthz`
3. Test generation endpoint manually with curl
4. Smoke test in staging environment

## Next Steps

After this feature is complete, see `/speckit.tasks` for task breakdown and implementation order.

## Getting Help

- **BDD Testing**: See `frontend/tests/README.md`
- **API Docs**: http://localhost:8000/api/docs (when backend running)
- **Component Library**: Radix UI docs at https://radix-ui.com
- **Markdown**: react-markdown docs at https://github.com/remarkjs/react-markdown
