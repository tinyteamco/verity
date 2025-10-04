/**
 * Initialize Firebase auth and handle token refresh
 */
import { onAuthStateChanged, type User } from 'firebase/auth'
import { auth } from './firebase'

let tokenRefreshInterval: ReturnType<typeof setInterval> | null = null

/**
 * Start listening for auth state changes and automatically refresh tokens
 */
export function initializeAuth(onTokenRefresh?: (token: string) => void): void {
  // Clear any existing interval
  if (tokenRefreshInterval) {
    clearInterval(tokenRefreshInterval)
  }

  // Listen for auth state changes
  onAuthStateChanged(auth, async (user: User | null) => {
    if (user) {
      // User is signed in, get fresh token
      const token = await user.getIdToken(true) // force refresh
      localStorage.setItem('firebase_token', token)

      if (onTokenRefresh) {
        onTokenRefresh(token)
      }

      // Set up token refresh every 50 minutes (tokens expire after 60 min)
      tokenRefreshInterval = setInterval(
        async () => {
          try {
            const freshToken = await user.getIdToken(true)
            localStorage.setItem('firebase_token', freshToken)

            if (onTokenRefresh) {
              onTokenRefresh(freshToken)
            }

            console.log('Token refreshed successfully')
          } catch (error) {
            console.error('Failed to refresh token:', error)
          }
        },
        50 * 60 * 1000
      ) // 50 minutes
    } else {
      // User is signed out
      localStorage.removeItem('firebase_token')

      if (tokenRefreshInterval) {
        clearInterval(tokenRefreshInterval)
        tokenRefreshInterval = null
      }
    }
  })
}

/**
 * Get the current ID token, refreshing if expired
 */
export async function getValidToken(): Promise<string | null> {
  const user = auth.currentUser

  if (!user) {
    return null
  }

  try {
    // getIdToken() automatically refreshes if expired
    const token = await user.getIdToken()
    localStorage.setItem('firebase_token', token)
    return token
  } catch (error) {
    console.error('Failed to get valid token:', error)
    return null
  }
}
