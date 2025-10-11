import type { InterviewListResponse } from '../types/study';
import { getApiUrl } from './api';

/**
 * Get list of interviews for a study
 * @param orgId Organization ID
 * @param studyId Study ID
 * @param token Firebase JWT token
 * @returns List of interviews with metadata
 */
export async function listStudyInterviews(
  orgId: string,
  studyId: string,
  token: string
): Promise<InterviewListResponse> {
  const response = await fetch(
    `${getApiUrl()}/api/orgs/${orgId}/studies/${studyId}/interviews`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to load interviews');
  }

  return await response.json();
}

/**
 * Get URL for downloading interview artifact (transcript or recording)
 * @param orgId Organization ID
 * @param interviewId Interview ID
 * @param filename Artifact filename ('transcript.txt' or 'recording.wav')
 * @param token Firebase JWT token
 * @returns Full URL for artifact download
 */
export function getInterviewArtifactUrl(
  orgId: string,
  interviewId: number,
  filename: 'transcript.txt' | 'recording.wav',
  token: string
): string {
  // Construct URL with token as query parameter for authenticated download
  const baseUrl = getApiUrl();
  return `${baseUrl}/api/orgs/${orgId}/interviews/${interviewId}/artifacts/${filename}?token=${encodeURIComponent(token)}`;
}

/**
 * Get reusable study link URL from slug
 * @param slug Study slug
 * @param includePid Whether to include placeholder for participant ID
 * @returns Full reusable link URL
 */
export function getReusableStudyLinkUrl(slug: string, includePid: boolean = true): string {
  // In production, this would use the actual domain
  // For dev/test, use window.location.origin
  const baseUrl = typeof window !== 'undefined'
    ? window.location.origin
    : 'https://verity.com';

  const basePath = `/study/${slug}/start`;
  return includePid ? `${baseUrl}${basePath}?pid={{PARTICIPANT_ID}}` : `${baseUrl}${basePath}`;
}

/**
 * Fetch interview transcript text
 * @param orgId Organization ID
 * @param interviewId Interview ID
 * @param token Firebase JWT token
 * @returns Transcript text content
 */
export async function fetchInterviewTranscript(
  orgId: string,
  interviewId: number,
  token: string
): Promise<string> {
  const response = await fetch(
    `${getApiUrl()}/api/orgs/${orgId}/interviews/${interviewId}/artifacts/transcript.txt`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to load transcript' }));
    throw new Error(error.detail || 'Failed to load transcript');
  }

  return await response.text();
}
