/**
 * Auth state persistence helpers
 */

export interface PersistedAuthState {
  userId: number
  email: string
  orgId: number | null
  organizationName: string | null
  role: 'owner' | 'admin' | 'member' | 'super_admin'
  firebaseUid: string
}

const AUTH_STATE_KEY = 'auth_state'

export function saveAuthState(state: PersistedAuthState): void {
  localStorage.setItem(AUTH_STATE_KEY, JSON.stringify(state))
}

export function loadAuthState(): PersistedAuthState | null {
  const stored = localStorage.getItem(AUTH_STATE_KEY)
  if (!stored) return null

  try {
    return JSON.parse(stored) as PersistedAuthState
  } catch {
    return null
  }
}

export function clearAuthState(): void {
  localStorage.removeItem(AUTH_STATE_KEY)
}
