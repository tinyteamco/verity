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
