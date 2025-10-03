import { initializeApp } from 'firebase/app'
import { getAuth, connectAuthEmulator } from 'firebase/auth'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'demo-api-key',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'demo-project.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'demo-project',
}

const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)

// Connect to emulator in development or E2E tests
// Always check localStorage first (set by E2E tests), then fallback to env vars
const useEmulator = import.meta.env.DEV ||
                    import.meta.env.VITE_USE_FIREBASE_EMULATOR === 'true' ||
                    (typeof window !== 'undefined' && localStorage.getItem('__E2E_STUB_PORT__'))

if (useEmulator) {
  // Use dynamic stub port from localStorage (E2E tests), or default 9099
  const stubPort = typeof window !== 'undefined'
    ? parseInt(localStorage.getItem('__E2E_STUB_PORT__') || '0') || 9099
    : 9099
  console.log('[Firebase] Connecting to auth emulator on port:', stubPort)
  connectAuthEmulator(auth, `http://localhost:${stubPort}`, { disableWarnings: true })
}
