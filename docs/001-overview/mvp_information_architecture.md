# Information Architecture Plan – MVP (v3)

This document captures the **minimum viable information architecture** for the UXR startup project. It has been stripped back to YAGNI essentials, with deferred complexity explicitly noted.

---

## Core Entities

### Company
- `company_id`
- `name`
- **Relationships:** has many **Users**, **Studies**

### User (Company-side)
- `user_id`
- `company_id` (FK)
- `email`, `password_hash`, `name`
- `created_at`, `last_login_at`
- **Relationships:** belongs to **Company**

### Study
- `study_id`
- `company_id` (FK)
- `title`
- `created_by_user_id` (FK to User)
- `created_at`, `updated_at`
- **Relationships:** belongs to **Company**; has **one InterviewGuide**; has many **Interviews**; has **one StudySummary**

### InterviewGuide (1:1 with Study)
- `guide_id`
- `study_id` (FK)
- `content_md` *(markdown content)*
- `created_at`, `updated_at`

### Interviewee (Marketplace-side)
- `interviewee_id`
- `email`, `password_hash`
- `name` *(required)*
- `created_at`, `last_login_at`
- **Relationships:** has many **Interviews**

### Interview (joins Interviewee ↔ Study)
- `interview_id`
- `study_id` (FK), `interviewee_id` (FK)
- `started_at`, `completed_at` (nullable)
- **Relationships:** has **one Transcript**, optional **one AudioRecording**, **one InterviewSummary**

### AudioRecording
- `audio_recording_id`
- `interview_id` (FK)
- `uri`
- `duration_ms`
- **Relationships:** has many **Highlights**

### Transcript
- `transcript_id`
- `interview_id` (FK)
- `text`
- `created_at`

### Highlight
- `highlight_id`
- `audio_recording_id` (FK)
- `start_ms`, `end_ms`
- `auto_label` (short description)
- *(optional MVP)* `confidence`
- **Relationships:** belongs to **AudioRecording**

### InterviewSummary (per Interview)
- `interview_summary_id`
- `interview_id` (FK)
- `summary_text`
- *(optional MVP)* `audio_reel_uri` *(system-generated on demand; cached if rendered)*
- `created_at`

### StudySummary (single, per Study)
- `study_summary_id`
- `study_id` (FK)
- `summary_text`
- *(optional MVP)* `audio_reel_uri` *(system-generated on demand; cached if rendered)*
- `created_at`, `updated_at`

---

## Relationships (Cardinalities)
- **Company 1—n Users**
- **Company 1—n Studies**
- **Study 1—1 InterviewGuide**
- **Study 1—n Interviews**
- **Study 1—1 StudySummary**
- **Interviewee 1—n Interviews**
- **Interview 1—1 Transcript**
- **Interview 0–1 AudioRecording**
- **AudioRecording 1—n Highlights**
- **Interview 1—1 InterviewSummary**

---

## Access & Flows (MVP)
- **Company users**: login → Studies list → create Study → define InterviewGuide (markdown) → share study link → view incoming Interviews → read Interview Summaries → view Study Summary.
- **Interviewees**: login → complete Interview → view past Interviews (basic list + transcript, audio if permitted).

---

## Intentionally Omitted (Until Needed)
- Company billing & plans (`plan_tier`, subscription state).
- User roles/permissions (all same for now).
- Versioning/history (multiple Study Summary versions, audit trails).
- Video recordings, video highlights, video reels.
- Reels as entities (persistent `HighlightsReel`, narration scripts, sequences).
- Invitation/eligibility entities (use simple signed link for now).
- Consent granularity & privacy controls beyond basic acceptance.
- Detailed asset metadata (codecs, fps, ASR model info).
- Moderation/compliance (PII redaction, safety flags).
- Tagging/analytics (topics, sentiment, personas, dashboards).
- Soft deletes/archival policies.
- Marketplace features (interviewee discovery/matching, incentives, reputation).

---

**Next steps:** This doc can be archived as the canonical MVP IA. Another LLM can pick up here and extend as new requirements are added.

