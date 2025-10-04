import { test as base, createBdd as createBddBase } from 'playwright-bdd'
import { createHydrationFixture, autoHydrate } from './bdd-hydration'
import { TestFixtures } from './fixtures'
import { exec, spawn } from 'child_process'
import { promisify } from 'util'

const execAsync = promisify(exec)

// Extend Playwright test with hydration accumulator and fixtures
export const test = base.extend({
  ...createHydrationFixture(),

  fixtures: async ({ page, hydration }, use) => {
    // Always use real backend with dynamic port allocation
    const startTime = Date.now()
    console.log('[Test] Starting backend + Firebase stub with clean state...')

    // Start backend+stub script and capture port assignments
    const backendProcess = spawn('bash', ['-c', 'cd ../backend && ./scripts/start_e2e_backend.sh'], {
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe']
    })

    // Read port assignments from stdout
    let stubPort = 0
    let backendPort = 0
    let portData = ''

    backendProcess.stdout?.on('data', (data) => {
      portData += data.toString()
      const stubMatch = portData.match(/STUB_PORT=(\d+)/)
      const backendMatch = portData.match(/BACKEND_PORT=(\d+)/)
      if (stubMatch) stubPort = parseInt(stubMatch[1])
      if (backendMatch) backendPort = parseInt(backendMatch[1])
    })

    // Capture stderr for debugging
    let stderrData = ''
    backendProcess.stderr?.on('data', (data) => {
      stderrData += data.toString()
    })

    // Wait for port assignments
    const portWaitStart = Date.now()
    for (let i = 0; i < 30; i++) {
      if (stubPort && backendPort) break
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    if (!stubPort || !backendPort) {
      console.error('[Test] Backend startup failed!')
      console.error('[Test] stderr:', stderrData)
      backendProcess.kill()
      throw new Error('Failed to get port assignments from backend script')
    }

    console.log(`[Test] Allocated ports - Stub: ${stubPort}, Backend: ${backendPort} (${Date.now() - portWaitStart}ms)`)

    // Wait for backend to be ready
    const healthCheckStart = Date.now()
    let ready = false
    for (let i = 0; i < 100; i++) {
      try {
        const response = await fetch(`http://localhost:${backendPort}/api/health`)
        if (response.ok) {
          ready = true
          console.log(`[Test] Backend ready! (${Date.now() - healthCheckStart}ms)`)
          console.log(`[Test] Total setup time: ${Date.now() - startTime}ms`)
          break
        }
      } catch (e) {
        // Not ready yet
      }
      await new Promise(resolve => setTimeout(resolve, 50))
    }

    if (!ready) {
      console.error('[Test] Backend health check failed!')
      console.error('[Test] stderr:', stderrData)
      backendProcess.kill()
      throw new Error('Backend failed to start')
    }

    // Set E2E ports in localStorage via init script (persists across navigation)
    // Each test gets a fresh browser context with isolated localStorage
    await page.addInitScript((args) => {
      localStorage.setItem('__E2E_BACKEND_PORT__', String(args.bp));
      localStorage.setItem('__E2E_STUB_PORT__', String(args.sp))
    }, { bp: backendPort, sp: stubPort });

    // Store process PID and ports for cleanup
    (page as any).__backendProcess__ = backendProcess;
    (page as any).__backendPort__ = backendPort;
    (page as any).__stubPort__ = stubPort

    // Create fixtures with backend ports
    const fixtures = new TestFixtures(page, hydration, backendPort, stubPort)
    await use(fixtures)

    // Cleanup: kill backend process after test
    const cleanupProcess = (page as any).__backendProcess__
    if (cleanupProcess) {
      console.log('[Test] Cleaning up backend process...')
      cleanupProcess.kill('SIGKILL')
      // Also kill any child processes
      try {
        process.kill(-cleanupProcess.pid, 'SIGKILL')
      } catch (e) {
        // Ignore if process group doesn't exist
      }
    }
  },
})

/**
 * Create BDD helpers with auto-hydration built-in.
 * Developers just use Given/When/Then - hydration happens automatically.
 *
 * Usage:
 *   import { createBdd } from '../support/world'
 *   const { Given, When, Then } = createBdd()
 *
 *   // When steps auto-hydrate before executing
 *   When('I navigate to dashboard', async ({ page }) => {
 *     // hydration already applied!
 *   })
 */
export function createBdd() {
  const { Given, When: WhenRaw, Then } = createBddBase(test)

  // Wrap When with auto-hydration
  const When = autoHydrate(WhenRaw)

  return { Given, When, Then }
}
