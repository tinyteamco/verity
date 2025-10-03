import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { bootstrapHydration } from '@tinyteamco/hydration-test-utils'
import { hydrationRegistry } from '../tests/support/hydration-registry'
import App from './App'
import './index.css'

// Bootstrap hydration before rendering
// This is safe - it's a no-op when no hydration data is present
await bootstrapHydration(hydrationRegistry, {
  strict: false,  // Temporarily disable strict mode to debug
  timeoutMs: 3000,
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
