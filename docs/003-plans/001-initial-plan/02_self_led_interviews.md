# Self-Led Interview Design

## Context

After initial implementation discussion, the team clarified that interviews are **self-led** by interviewees, not scheduled meetings with researchers. This fundamentally changes the interview flow.

## Core Workflow

1. **Organization creates study + interview guide**
2. **Organization generates unique interview links** 
3. **Interviewees access interviews via links** (no authentication required)
4. **Optional interviewee sign-in** (for tracking participation history)
5. **System uploads interview results** (transcript, recordings)

## Key Design Decisions

### Link-Based Access
- Each interview has a unique `access_token` (UUID)
- Links are shareable: `https://app.verity.com/interviews/{access_token}`
- No authentication required to start an interview

### Optional User Association
From team discussion:
> "For now I'll implement unique link generation and make it optional to sign in after (which would give the participant the option to get a view of all the studies they have participated in / interviews given at a later date). If they don't sign in the interview won't be associated with a user id on our side"

This means:
- `interviewee_firebase_uid` is nullable
- Interviewees can complete anonymously
- Sign-in can happen during or after interview
- Signed-in users get a dashboard of their participation

### MVP Simplifications
For the initial release:
- No link expiration
- No IP tracking or session management  
- Simple status: "pending" → "completed"
- One-time completion (no re-submission)
- No complex abandonment tracking

## Database Schema

```sql
interviews
- id (PK)
- study_id (FK to studies)
- access_token (unique UUID for link access)
- interviewee_firebase_uid (nullable - set if user signs in)
- status (pending, completed)
- created_at
- completed_at
- transcript_url
- recording_url
- notes
```

## API Endpoints

### Organization Endpoints (Auth Required)
- `POST /studies/{id}/interviews/generate-link` - Create new interview link
- `GET /studies/{id}/interviews` - List all interviews for a study
- `GET /studies/{id}/interviews/{id}` - View specific interview details

### Public Endpoints (No Auth)
- `GET /interviews/{access_token}` - Access interview (returns study info)
- `POST /interviews/{access_token}/complete` - Submit interview results
- `POST /interviews/{access_token}/claim` - Associate with authenticated user

## Future Enhancements
Once MVP is proven:
- Link expiration dates
- Session management for security
- Abandoned interview tracking
- Bulk link generation
- Analytics on completion rates
- Multi-use links for recurring interviews