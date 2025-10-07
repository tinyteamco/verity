import type { StudyWithGuide, InterviewGuide, GuideUpdateRequest } from '../types/study';

/**
 * Get the API base URL based on environment
 *
 * - E2E tests: Use dynamic port from localStorage (__E2E_BACKEND_PORT__)
 * - Production: Use relative /api path (proxied by Firebase Hosting to Cloud Run)
 * - Local dev: Use localhost:8000
 */
export function getApiUrl(): string {
  // Check if running in E2E test mode (has dynamic backend port)
  const e2ePort = typeof window !== 'undefined'
    ? parseInt(localStorage.getItem('__E2E_BACKEND_PORT__') || '0')
    : 0

  if (e2ePort > 0) {
    // E2E test mode - use dynamic port
    return `http://localhost:${e2ePort}`
  }

  // Check if we're in development (Vite dev server sets this)
  const isDev = import.meta.env.DEV

  if (isDev) {
    // Local development - use default backend port
    return 'http://localhost:8000'
  }

  // Production - use relative URL (Firebase Hosting proxies /api/** to Cloud Run)
  return ''
}

/**
 * Generate a study from a research topic
 * @param orgId Organization ID
 * @param topic What the researcher wants to learn
 * @param token Firebase JWT token
 * @returns Study with auto-generated interview guide
 */
export async function generateStudy(
  orgId: string,
  topic: string,
  token: string
): Promise<StudyWithGuide> {
  const response = await fetch(`${getApiUrl()}/api/orgs/${orgId}/studies/generate`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ topic }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate study');
  }

  return await response.json();
}

/**
 * Get the interview guide for a study
 * @param studyId Study ID
 * @param token Firebase JWT token
 * @returns Interview guide or null if not found
 */
export async function getGuide(
  studyId: string,
  token: string
): Promise<InterviewGuide | null> {
  const response = await fetch(`${getApiUrl()}/api/studies/${studyId}/guide`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (response.status === 404) {
    return null; // No guide yet
  }

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to load guide');
  }

  return await response.json();
}

/**
 * Update or create interview guide for a study
 * @param studyId Study ID
 * @param contentMd Markdown content
 * @param token Firebase JWT token
 * @returns Updated interview guide
 */
export async function updateGuide(
  studyId: string,
  contentMd: string,
  token: string
): Promise<InterviewGuide> {
  const response = await fetch(`${getApiUrl()}/api/studies/${studyId}/guide`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content_md: contentMd } as GuideUpdateRequest),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to save guide');
  }

  return await response.json();
}
