# Interview Guide Implementation Plan

**Last Updated:** 2025-10-07
**Status:** Phase 1 Complete ✅

## 🎯 Objective

Build an end-to-end study creation flow that matches the designer's vision: a single continuous flow from topic input → AI-generated interview guide → participant management.

## 📋 Design Philosophy

### Key Decisions

1. **Flexible Schema**: Use TEXT (or JSONB) storage to allow schema evolution during early development
2. **LLM-Powered UX Mapping**: When UX changes, use LLM prompts to map between storage format and UI (no schema migrations needed)
3. **Incremental Build**: Start with minimal flow (topic → generated guide → display), add interactivity later
4. **End-to-End First**: Build complete flow early to validate the experience, then add editing/refinement

### Storage Strategy

**Interview Guide Storage:**
```sql
-- interview_guides table
id: int (PK)
study_id: int (unique, FK to studies)
content: text  -- Start simple, can move to JSONB later if needed
created_at: timestamp
updated_at: timestamp
```

**Why TEXT for now:**
- Schema is not finalized
- LLM can parse/flatten any structure
- Easy to evolve without migrations
- Can migrate to JSONB later if structured queries needed

## 🎨 User Flow (Target Experience)

Based on designer mockup from Figma/Loom:

### Phase 1: Topic Input → Study Creation
1. User lands on simple interface
2. Prompt: **"What do you want to learn today?"**
3. User enters research topic (e.g., "How do freelancers choose project management tools?")
4. Submit button triggers:
   - LLM generates study slug from topic
   - Create study record (title=slug, description=topic)
   - LLM generates interview guide from topic
   - Store guide in `interview_guides` table
   - Navigate to guide preview

### Phase 2: Guide Preview (Display Only)
1. Show generated interview guide (readonly)
2. Structure includes:
   - Study title
   - Welcome message
   - Themed sections with questions
3. Button: **"Next → add participants"** (placeholder for now)

### Phase 3: Guide Editing (Future)
1. "Edit Guide" button
2. LLM decomposes text → structured UI
3. User makes changes
4. LLM flattens back → TEXT storage

### Phase 4: Advanced Refinement (Future)
- Goal selection (changes question framing)
- Tone adjustment
- Add competitor questions
- AI chat interface for refinements

### Phase 5: Participant Management (Future)
- Generate interview links
- Invite participants
- Track responses

## 🚧 Implementation Phases

### Phase 1: Backend Foundation ✅ COMPLETE

**Completed 2025-10-07**

**Database:**
- ✅ `interview_guides` table already existed with correct schema
- ✅ Foreign key to `studies.id` with unique constraint (1:1 relationship)
- ✅ Field name: `content_md` (not `content`)

**API Endpoints:**
```python
✅ POST /orgs/{org_id}/studies/generate
  Request: { "topic": "How do freelancers..." }
  Response: { "study": {...}, "guide": {...} }
  # Creates study + generates guide in one transaction

✅ GET /studies/{study_id}/guide
  Response: { "study_id": "1", "content_md": "...", "updated_at": "..." }

✅ PUT /studies/{study_id}/guide
  Request: { "content_md": "..." }
  Response: { "study_id": "1", "content_md": "...", "updated_at": "..." }
```

**LLM Integration:**
- ✅ Using Pydantic AI with Anthropic Claude 3.5 Sonnet Latest
- ✅ Service: `generate_study_title(topic)` → slug (2-5 words, lowercase, hyphens)
- ✅ Service: `generate_interview_guide(topic)` → markdown text
- ✅ Test mocking: Auto-detects test mode (no real API calls in tests)
- ✅ Async/sync bridge: `nest-asyncio` for FastAPI compatibility
- ✅ Transaction-safe: Proper rollback on LLM failures

**BDD Tests (17 scenarios, all passing):**
```gherkin
✅ Organization users can create study guides (owner/admin/member)
✅ Update an existing study guide
✅ Organization users can retrieve study guides (owner/admin/member)
✅ Get study guide when none exists (404)
✅ Cannot access study guide from different organization
✅ Cannot create study guide for non-existent study
✅ Interviewee users cannot access study guides (403)
✅ Unauthenticated users cannot access study guides (401)
✅ Generate study with AI-generated interview guide from topic (owner/admin/member)
✅ Super admin can generate study for any organization
✅ Study creation is rolled back when interview guide generation fails (NEW)
```

**Code Quality:**
- ✅ Zero linting errors (ruff)
- ✅ Zero type errors (ty)
- ✅ Zero warnings (Pydantic deprecation warning suppressed)
- ✅ All type annotations complete

**Key Implementation Details:**
- `src/llm_service.py`: Pydantic AI integration with test mocking
- `src/api/main.py:495-570`: Generation endpoint with transaction safety
- `tests/features/study_guides.feature`: 17 BDD scenarios
- `tests/step_defs/test_study_guides.py`: 431 lines of step definitions
- Test mocking: `APP_ENV=local` && no `ANTHROPIC_API_KEY` → TestModel
- Rollback coverage: Interview guide generation failure tested

### Phase 2: Frontend Flow (Display Only) ⏭️ NEXT

**UI Changes:**
1. Replace "Create Study" modal with new flow:
   - Single input: "What do you want to learn today?"
   - Submit → Loading state ("Generating your study...")
   - Navigate to guide preview page

2. Guide Preview Page (`/studies/{study_id}/guide`):
   - Display study title (generated slug)
   - Display guide content (markdown rendering)
   - Button: "Next → add participants" (disabled/placeholder)
   - Button: "Back to Organization" (working)

**API Integration:**
- Call `POST /orgs/{org_id}/studies/generate` with topic
- Handle loading states and errors
- Navigate to guide preview on success

**E2E Tests:**
```gherkin
Scenario: Create study from topic with generated guide
  Given I am on organization "Research Corp" page
  When I click "Create Study"
  And I enter topic "Freelancer project management decisions"
  And I submit
  Then I see a loading indicator
  And I am redirected to the guide preview page
  And I see the generated interview guide
  And I see "Next → add participants" button
```

### Phase 3: Guide Editing (Future)

**Backend:**
- Endpoint: `POST /api/studies/{study_id}/guide/decompose` (LLM parses text → JSON structure)
- Endpoint: `POST /api/studies/{study_id}/guide/flatten` (LLM flattens edits → text)

**Frontend:**
- "Edit Guide" button → Guide editor page
- LLM-powered decomposition for structured editing
- Save → Flatten back to text

**Tests:**
- Edit guide content
- Changes persist
- Can switch between display/edit modes

### Phase 4: Advanced Refinement (Future)

**Features from Designer Mockup:**
- Two-panel UI (control panel + live preview)
- Goal selection dropdown → Regenerate questions
- Tone adjustment ("Make it more friendly")
- Add competitor questions
- AI chat interface for custom refinements

### Phase 5: Interview Execution (Future)

**Features:**
- Generate unique interview links
- Participant access (no auth required)
- Response collection
- Results viewing

## 🔧 Technical Notes

### LLM Provider Selection

**Options:**
1. **Anthropic Claude** (Recommended)
   - Already using for Claude Code
   - Strong at following structured prompts
   - Good at markdown generation

2. **OpenAI GPT-4**
   - Widely used
   - Well-documented
   - More expensive

**Decision:** Start with Anthropic Claude (familiarity + quality)

### LLM Prompt Design

**Study Title Generation:**
```
Given this research topic, generate a short, descriptive slug (2-5 words, lowercase, hyphens):

Topic: {user_topic}

Return only the slug, no explanation.
```

**Interview Guide Generation:**
```
You are a UX researcher creating an interview guide.

Research topic: {user_topic}

Generate a comprehensive interview guide with:
1. A welcoming introduction (2-3 sentences)
2. 4-5 thematic sections
3. 3-5 questions per section
4. Questions should be open-ended and conversational

Format as markdown with clear section headers.
```

### Migration Strategy

**Current Study Creation Flow:**
```gherkin
# OLD: Modal with title + description
Scenario: Create a new study
  When I click "Create Study"
  And I enter "Onboarding Feedback" as title
  And I enter "Understanding user experience" as description
  And I submit
  Then I see study in list
```

**New Flow:**
```gherkin
# NEW: Single topic input → AI generation
Scenario: Generate study from topic
  When I click "Create Study"
  And I enter "What do users think about onboarding?"
  And I submit
  Then study is created with AI-generated title
  And interview guide is generated
  And I see guide preview
```

**Breaking Changes:**
- All existing study creation E2E tests need updates
- Study creation endpoint changes (or add new endpoint)
- Frontend completely replaces study modal

**Migration Plan:**
1. Add new `POST /api/orgs/{org_id}/studies/generate` endpoint (keep old endpoint)
2. Add new frontend flow (keep old for comparison)
3. Update all E2E tests to use new flow
4. Remove old study creation modal
5. Deprecate old endpoint (or keep for API users)

## 📊 Success Criteria

**Phase 1 Complete When:**
- ✅ `interview_guides` table exists
- ✅ Can generate study + guide from topic
- ✅ Can fetch guide for study
- ✅ Can update guide content
- ✅ All BDD tests passing
- ✅ Zero warnings (ruff + ty)

**Phase 2 Complete When:**
- ✅ Frontend flow works end-to-end (topic → guide preview)
- ✅ Generated guide displays correctly (markdown rendering)
- ✅ All E2E tests passing
- ✅ Old study creation flow removed
- ✅ Zero TypeScript errors

## 🔗 Related Documentation

- [Frontend Development Progress](/docs/003-plans/003-frontend-development-progress.md)
- [Frontend Architecture](/docs/002-architecture/004-frontend-architecture.md)
- [MVP Information Architecture](/docs/001-overview/mvp_information_architecture.md)
- [Designer Mockup] - Figma/Loom (reference screenshots provided)

## 🎬 Next Steps

**Current Status:** Phase 1 Complete ✅

**Next:** Phase 2 - Frontend Flow (Display Only)
1. Update organization page with new study creation flow
2. Create topic input UI ("What do you want to learn today?")
3. Implement loading states during AI generation
4. Create guide preview page with markdown rendering
5. Write E2E tests for new flow
6. Remove old study creation modal
