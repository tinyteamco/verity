export interface Study {
  study_id: string;
  org_id: string;
  title: string;
  description: string | null;
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
