# Research: Study Management UI

**Feature**: Study Management UI
**Date**: 2025-10-07
**Status**: Complete

## Research Summary

**No research needed** - all technology stack decisions already made and implemented in the existing codebase.

## Technology Stack (Existing)

### Frontend
- **React 18.3** with TypeScript 5.6 - Already configured
- **Vite** - Build tool, already in use
- **Tanstack Router** - Routing, already in use
- **Tailwind CSS + Radix UI** - Styling, already in use
- **Playwright + playwright-bdd** - E2E testing with Gherkin, already configured

### Backend (Existing - Can Modify if Needed)
- **FastAPI + Pydantic** - REST API framework
- **PostgreSQL 16 + SQLAlchemy** - Database
- **Firebase Auth** - Authentication
- **LLM service** (pydantic-ai) - Study generation

Required endpoints already exist and are tested, but can be modified if frontend needs differ from current implementation.

## Key Decisions

### Decision 1: Markdown Editor Approach

**Decision**: Use native HTML textarea for markdown editing with side-by-side preview

**Rationale**:
- Simplicity - no heavy WYSIWYG editor dependency
- Users who write interview guides likely comfortable with markdown
- Easy to integrate markdown preview (use existing library like `marked` or `react-markdown`)
- Aligns with "lightweight sketches" philosophy from team

**Alternatives Considered**:
- Rich text editor (TipTap, ProseMirror) - Too complex for MVP
- WYSIWYG markdown (like Notion) - Over-engineering for initial release

**Implementation**:
- Textarea for editing
- Preview pane using `react-markdown` or similar
- Toggle between edit/preview or split view

### Decision 2: Study Generation UX Flow

**Decision**: Modal dialog for topic input → full page for viewing/editing result

**Rationale**:
- Modal keeps user in context (studies list page)
- Lightweight prompt matches "What do you want to learn?" design concept
- After generation, navigate to study detail page to show full result
- Consistent with existing "Create Study" modal pattern

**Alternatives Considered**:
- Dedicated wizard page - Too heavy for simple topic input
- Inline generation on list page - Clutters the studies list
- Slide-over panel - Harder to show long interview guides

**Implementation**:
- "Generate Study" button on StudyListPage
- Modal with textarea for topic input + loading state (30-60s)
- On success, navigate to `/orgs/{orgId}/studies/{newStudyId}`
- On failure, show error with retry option

### Decision 3: Interview Guide Display

**Decision**: Show guide on study detail page, with "Edit" button to enter edit mode

**Rationale**:
- Keeps all study information in one place
- Read-only view by default (prevent accidental edits)
- Edit mode opens markdown editor component
- Matches existing "Edit Study" button pattern

**Alternatives Considered**:
- Separate /guides/{id} route - Adds unnecessary navigation
- Always editable - Risk of accidental changes
- Modal editor - Too cramped for long interview guides

**Implementation**:
- StudyDetailPage shows `<StudyGuideViewer guide={guide} />`
- "Edit Guide" button opens `<StudyGuideEditor guide={guide} onSave={...} />`
- Editor has markdown textarea + preview + save/cancel buttons

### Decision 4: Error Handling for Generation Timeouts

**Decision**: 60 second timeout with clear error message + retry option

**Rationale**:
- Backend LLM calls may take 30-60s
- User needs visual feedback during wait
- If timeout, offer retry or manual creation fallback
- Spec requires "clear error messages when generation fails"

**Alternatives Considered**:
- Polling/background job - Over-engineering for MVP
- Longer timeout (120s+) - Poor UX, users will abandon
- No timeout - Could hang indefinitely

**Implementation**:
- Show loading spinner with "Generating your study..." message
- Client-side 60s timeout
- Error state shows: "Generation took too long. [Retry] or [Create Manually]"
- Retry calls same endpoint again

## Integration Patterns

### Calling Backend Generation Endpoint

**Pattern**: POST to `/orgs/{orgId}/studies/generate` with topic

```typescript
// frontend/src/lib/api.ts
async function generateStudy(orgId: string, topic: string) {
  const response = await fetch(`/api/orgs/${orgId}/studies/generate`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ topic }),
  });

  if (!response.ok) throw new Error('Generation failed');

  return await response.json(); // { study: {...}, guide: {...} }
}
```

**Response**:
```json
{
  "study": {
    "study_id": "uuid",
    "title": "Generated Title",
    "description": "Original topic",
    "org_id": "uuid",
    "created_at": "...",
    "updated_at": "..."
  },
  "guide": {
    "study_id": "uuid",
    "content_md": "# Welcome\n\n## Section 1\n...",
    "updated_at": "..."
  }
}
```

### Saving Interview Guide Edits

**Pattern**: PUT to `/studies/{studyId}/guide` with updated markdown

```typescript
async function updateGuide(studyId: string, contentMd: string) {
  const response = await fetch(`/api/studies/${studyId}/guide`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content_md: contentMd }),
  });

  if (!response.ok) throw new Error('Save failed');

  return await response.json(); // Updated guide
}
```

### Fetching Existing Guide

**Pattern**: GET from `/studies/{studyId}/guide`

```typescript
async function getGuide(studyId: string) {
  const response = await fetch(`/api/studies/${studyId}/guide`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (response.status === 404) {
    return null; // No guide yet
  }

  if (!response.ok) throw new Error('Fetch failed');

  return await response.json(); // { study_id, content_md, updated_at }
}
```

## Dependencies

**New npm packages needed**:
- `react-markdown` or `marked` - Markdown rendering for preview
- No other new dependencies - everything else already installed

**No backend changes needed** - all endpoints exist.

## Open Questions

**None** - all technical questions resolved based on existing codebase.
