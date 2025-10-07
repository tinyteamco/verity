# Data Model: Study Management UI

**Feature**: Study Management UI
**Date**: 2025-10-07

## Overview

This feature uses **existing backend database schema** - no database changes required. The frontend will interact with existing Study and InterviewGuide entities via REST APIs.

## Backend Entities (Existing - Read Only)

### Study

**Database Table**: `studies`

**Fields**:
- `id` (UUID, primary key)
- `organization_id` (UUID, foreign key → organizations)
- `title` (string, required) - Study name
- `description` (string, nullable) - What the researcher wants to learn (stored topic)
- `created_at` (timestamp)
- `updated_at` (timestamp, nullable)

**Relationships**:
- Belongs to Organization (many-to-one)
- Has one InterviewGuide (one-to-one, optional)
- Has many Interviews (one-to-many)

**Validation Rules** (enforced by backend):
- `title` must not be empty
- `organization_id` must be valid UUID of existing organization
- User must belong to organization to create/edit (multi-tenancy security)

### InterviewGuide

**Database Table**: `interview_guides`

**Fields**:
- `id` (UUID, primary key)
- `study_id` (UUID, foreign key → studies, unique)
- `content_md` (text, required) - Markdown content of interview guide
- `updated_at` (timestamp)

**Relationships**:
- Belongs to Study (one-to-one)

**Validation Rules** (enforced by backend):
- `study_id` must be valid UUID of existing study
- `content_md` can be any markdown text (including empty string)
- 1:1 relationship - each study has at most one guide

## Frontend State Management

### Component State (React)

**StudyGeneratePage**:
```typescript
interface StudyGenerateState {
  topic: string;              // User input
  isGenerating: boolean;      // Loading state
  error: string | null;       // Error message
  generatedStudy: Study | null;  // Result
}
```

**StudyGuideEditor**:
```typescript
interface EditorState {
  contentMd: string;          // Current markdown content
  isDirty: boolean;           // Has unsaved changes
  isSaving: boolean;          // Save in progress
  showPreview: boolean;       // Toggle preview pane
  error: string | null;       // Save error
}
```

**StudyDetailPage**:
```typescript
interface DetailPageState {
  study: Study | null;
  guide: InterviewGuide | null;
  isEditingGuide: boolean;    // Edit mode toggle
  isLoading: boolean;
}
```

### Data Flow

#### Study Generation Flow
```
User inputs topic
  ↓
POST /api/orgs/{orgId}/studies/generate { topic }
  ↓
Backend: LLM generates title + guide content
  ↓
Backend: Creates Study + InterviewGuide in database
  ↓
Response: { study: {...}, guide: {...} }
  ↓
Frontend: Navigate to /orgs/{orgId}/studies/{newStudyId}
```

#### Guide Editing Flow
```
User clicks "Edit Guide"
  ↓
Load current guide content into editor
  ↓
User edits markdown in textarea
  ↓
User clicks "Save"
  ↓
PUT /api/studies/{studyId}/guide { content_md: "..." }
  ↓
Backend: Updates interview_guides.content_md
  ↓
Response: Updated guide
  ↓
Frontend: Show success, exit edit mode
```

#### Guide Viewing Flow
```
User navigates to study detail page
  ↓
GET /api/orgs/{orgId}/studies/{studyId}  (get study)
  ↓
GET /api/studies/{studyId}/guide  (get guide)
  ↓
If guide exists:
  Render markdown with react-markdown
Else:
  Show "No guide yet" + "Generate" button
```

## TypeScript Types (Frontend)

```typescript
// frontend/src/types/study.ts

export interface Study {
  study_id: string;
  org_id: string;
  title: string;
  description: string | null;
  created_at: string;  // ISO 8601
  updated_at: string | null;  // ISO 8601
}

export interface InterviewGuide {
  study_id: string;
  content_md: string;
  updated_at: string;  // ISO 8601
}

export interface StudyWithGuide {
  study: Study;
  guide: InterviewGuide;
}

export interface StudyGenerateRequest {
  topic: string;
}

export interface GuideUpdateRequest {
  content_md: string;
}
```

## API Contracts (Existing - No Changes)

See `/specs/001-study-management-ui/contracts/` for OpenAPI definitions.

All endpoints already exist and are tested:
- `POST /api/orgs/{org_id}/studies/generate`
- `GET /api/studies/{study_id}/guide`
- `PUT /api/studies/{study_id}/guide`

## State Transitions

### Study Creation States

```
[Initial] → (user enters topic) → [Validating Input]
  ↓
  ↓ (topic valid)
  ↓
[Generating] → (30-60s wait) → [Success] OR [Error]
  ↓                              ↓           ↓
  ↓                         (navigate)    (retry)
  ↓                         to detail      ↓
  ↓                           page      [Generating]
```

### Guide Editing States

```
[Viewing] → (click Edit) → [Editing]
  ↓                          ↓
  ↓                     (modify content)
  ↓                          ↓
  ↓                      [Dirty State]
  ↓                          ↓
  ↓                     (click Save)
  ↓                          ↓
  ↓                       [Saving]
  ↓                          ↓
  ↓                    (success/error)
  ↓                          ↓
[Viewing] ← (on success) ← [Done]
```

## Validation Rules

### Client-Side (Frontend)

**Topic Input**:
- Must not be empty (trim whitespace)
- Min length: 10 characters (prevent "test" inputs)
- Max length: 500 characters (prevent abuse)
- Show validation error immediately on blur

**Guide Content**:
- No validation - any markdown is valid
- Warn if completely empty (but allow save)
- Check for unsaved changes before navigation

### Server-Side (Backend - Existing)

**Study Creation**:
- Title must not be empty
- User must belong to organization
- Organization must exist

**Guide Update**:
- Study must exist
- User must have access to study's organization

## Error Handling

### Generation Errors

| Error Type | HTTP Status | Frontend Handling |
|------------|-------------|-------------------|
| Topic validation failed | 400 | Show inline error under textarea |
| User not in org | 403 | Redirect to login (auth issue) |
| LLM service error | 500 | Show "Generation failed, please retry" |
| Timeout (client-side) | - | Show "Took too long, retry or create manually" |

### Save Errors

| Error Type | HTTP Status | Frontend Handling |
|------------|-------------|-------------------|
| Study not found | 404 | Show "Study was deleted" |
| User not in org | 403 | Redirect to login |
| Database error | 500 | Show "Save failed, please retry" |
| Network error | - | Show "Connection lost, changes preserved locally" |

## Caching & Performance

**No caching needed** for MVP:
- Studies list already fetches on demand
- Guide content fetched when viewing study detail
- No real-time updates needed (single-user editing)

**Future Optimization** (not in this iteration):
- Cache guide content in browser (localStorage)
- Debounce autosave
- Optimistic UI updates
