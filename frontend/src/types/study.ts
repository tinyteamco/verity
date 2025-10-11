export interface Study {
  study_id: string;
  org_id: string;
  title: string;
  slug: string; // URL-friendly identifier for reusable links
  description: string | null;
  participant_identity_flow: 'anonymous' | 'claim_after' | 'allow_pre_signin';
  created_at: string; // ISO 8601
  updated_at: string | null; // ISO 8601
}

export interface InterviewGuide {
  study_id: string;
  content_md: string;
  updated_at: string; // ISO 8601
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

// Interview types for self-led interview feature

export interface Interview {
  id: number;
  study_id: number;
  status: 'pending' | 'completed';
  completed_at: string | null; // ISO 8601
  external_participant_id: string | null; // From recruitment platforms (e.g., "prolific_abc123")
  platform_source: string | null; // Inferred from pid prefix (e.g., "prolific")
  has_transcript: boolean;
  has_recording: boolean;
}

export interface InterviewListResponse {
  interviews: Interview[];
}

export interface InterviewDetail extends Interview {
  transcript_text?: string; // Only present if has_transcript is true
  recording_url?: string; // Only present if has_recording is true
}
