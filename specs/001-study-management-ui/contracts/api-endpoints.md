# API Contracts: Study Management UI

**Feature**: Study Management UI
**Date**: 2025-10-07
**Status**: Endpoints exist but can be modified if needed

## Overview

This feature uses backend REST APIs that already exist. These endpoints are documented based on current implementation, but **can be changed** if frontend requirements differ during development.

## Endpoint 1: Generate Study from Topic

**Purpose**: Create a new study with auto-generated interview guide from a research topic

### Request

```http
POST /api/orgs/{org_id}/studies/generate
Authorization: Bearer {firebase_jwt_token}
Content-Type: application/json

{
  "topic": "How do freelancers choose project management tools?"
}
```

**Path Parameters**:
- `org_id` (string, UUID) - Organization ID

**Request Body**:
```typescript
{
  topic: string;  // Required, what the researcher wants to learn
}
```

### Response

**Success (201 Created)**:
```json
{
  "study": {
    "study_id": "550e8400-e29b-41d4-a716-446655440000",
    "org_id": "660e8400-e29b-41d4-a716-446655440001",
    "title": "Freelancer Project Management Tool Selection",
    "description": "How do freelancers choose project management tools?",
    "created_at": "2025-10-07T18:23:00Z",
    "updated_at": null
  },
  "guide": {
    "study_id": "550e8400-e29b-41d4-a716-446655440000",
    "content_md": "# Welcome\n\nThank you for participating...\n\n## Work Context\n\n1. Tell me about...",
    "updated_at": "2025-10-07T18:23:00Z"
  }
}
```

**Error Responses**:

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Topic empty or invalid | `{"detail": "Topic is required"}` |
| 403 | User not in organization | `{"detail": "User not in organization"}` |
| 500 | LLM generation failed | `{"detail": "Failed to generate interview guide: {error}"}` |
| 500 | Database error | `{"detail": "Database error: {error}"}` |

### Implementation Notes

- Backend uses LLM to generate study title from topic
- Topic is stored as `study.description`
- LLM generates markdown interview guide content
- Both Study and InterviewGuide created in single transaction
- If guide generation fails, study creation is rolled back

---

## Endpoint 2: Get Interview Guide

**Purpose**: Fetch the interview guide for a study

### Request

```http
GET /api/studies/{study_id}/guide
Authorization: Bearer {firebase_jwt_token}
```

**Path Parameters**:
- `study_id` (string, UUID) - Study ID

### Response

**Success (200 OK)**:
```json
{
  "study_id": "550e8400-e29b-41d4-a716-446655440000",
  "content_md": "# Welcome\n\nThank you for participating...",
  "updated_at": "2025-10-07T18:23:00Z"
}
```

**Error Responses**:

| Status | Condition | Body |
|--------|-----------|------|
| 404 | Study has no guide | `{"detail": "Interview guide not found"}` |
| 404 | Study doesn't exist | `{"detail": "Study not found"}` |
| 403 | User not authorized | `{"detail": "User not in organization"}` |

### Implementation Notes

- Returns 404 if study exists but has no guide (manual creation)
- Multi-tenancy: user must belong to study's organization

---

## Endpoint 3: Update Interview Guide

**Purpose**: Create or update the interview guide for a study

### Request

```http
PUT /api/studies/{study_id}/guide
Authorization: Bearer {firebase_jwt_token}
Content-Type: application/json

{
  "content_md": "# Updated Welcome Message\n\n## New Section..."
}
```

**Path Parameters**:
- `study_id` (string, UUID) - Study ID

**Request Body**:
```typescript
{
  content_md: string;  // Required, markdown content (can be empty string)
}
```

### Response

**Success (200 OK)**:
```json
{
  "study_id": "550e8400-e29b-41d4-a716-446655440000",
  "content_md": "# Updated Welcome Message\n\n## New Section...",
  "updated_at": "2025-10-07T19:45:00Z"
}
```

**Error Responses**:

| Status | Condition | Body |
|--------|-----------|------|
| 404 | Study doesn't exist | `{"detail": "Study not found"}` |
| 403 | User not authorized | `{"detail": "User not in organization"}` |
| 500 | Database error | `{"detail": "Database error: {error}"}` |

### Implementation Notes

- **Upsert operation**: Creates guide if doesn't exist, updates if exists
- Empty string is valid (allows deleting all content)
- `updated_at` timestamp automatically set to current time
- Multi-tenancy: user must belong to study's organization

---

## Frontend Usage Patterns

### Pattern 1: Generate Study

```typescript
// In StudyGeneratePage.tsx
async function handleGenerate() {
  setIsGenerating(true);
  try {
    const response = await fetch(
      `/api/orgs/${orgId}/studies/generate`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic }),
      }
    );

    if (!response.ok) {
      throw new Error('Generation failed');
    }

    const result = await response.json();

    // Navigate to new study
    navigate(`/orgs/${orgId}/studies/${result.study.study_id}`);
  } catch (error) {
    setError('Failed to generate study. Please retry.');
  } finally {
    setIsGenerating(false);
  }
}
```

### Pattern 2: Fetch Guide for Display

```typescript
// In StudyDetailPage.tsx
useEffect(() => {
  async function loadGuide() {
    try {
      const response = await fetch(
        `/api/studies/${studyId}/guide`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.status === 404) {
        setGuide(null); // No guide yet
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to load guide');
      }

      const guide = await response.json();
      setGuide(guide);
    } catch (error) {
      console.error('Error loading guide:', error);
    }
  }

  loadGuide();
}, [studyId]);
```

### Pattern 3: Save Guide Edits

```typescript
// In StudyGuideEditor.tsx
async function handleSave() {
  setIsSaving(true);
  try {
    const response = await fetch(
      `/api/studies/${studyId}/guide`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content_md: contentMd }),
      }
    );

    if (!response.ok) {
      throw new Error('Save failed');
    }

    const updatedGuide = await response.json();
    onSave(updatedGuide);
    setIsDirty(false);
  } catch (error) {
    setError('Failed to save changes. Please retry.');
  } finally {
    setIsSaving(false);
  }
}
```

## Authentication & Authorization

All endpoints require:
- **Authentication**: Valid Firebase JWT token in `Authorization: Bearer {token}` header
- **Authorization**: User must belong to the organization that owns the study
- **Multi-tenancy**: Backend verifies org membership before allowing access

## Rate Limiting

**Not currently implemented** - no rate limiting on these endpoints.

**Future consideration**: May add rate limiting on `/generate` endpoint to prevent abuse (expensive LLM calls).

## Testing

All endpoints have existing BDD tests in `backend/tests/features/study_guides.feature`:
- ✅ Generate study with valid topic
- ✅ Generation fails when LLM service fails (rollback test)
- ✅ Get guide returns 404 when no guide exists
- ✅ Update guide creates new guide if doesn't exist
- ✅ Cross-organization access denied (403)

No new backend tests needed - frontend E2E tests will verify end-to-end integration.
