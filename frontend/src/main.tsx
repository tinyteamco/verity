import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

// Bootstrap hydration only in development/E2E test mode
// This entire block is tree-shaken out in production builds
if (import.meta.env.DEV) {
  // Only load hydration utilities if E2E markers are present
  if (typeof window !== 'undefined' && localStorage.getItem('__E2E_BACKEND_PORT__')) {
    const { bootstrapHydration } = await import('@tinyteamco/hydration-test-utils')
    const { hydrationRegistry } = await import('../tests/support/hydration-registry')

    await bootstrapHydration(hydrationRegistry, {
      strict: false,
      timeoutMs: 3000,
    })
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
