/**
 * BDD-friendly hydration helpers for hydration-test-utils
 *
 * Problem: hydration-test-utils expects hydratePage() to be called once with all data.
 * BDD scenario steps accumulate data across multiple Given steps.
 *
 * Solution: HydrationAccumulator tracks data across steps and applies it on first When.
 */

import { Page } from '@playwright/test'
import { hydratePage } from '@tinyteamco/hydration-test-utils/playwright'

export class HydrationAccumulator {
  private data: Record<string, any> = {}
  private applied = false

  constructor(private page: Page) {}

  /**
   * Add data to be hydrated (called by Given steps)
   */
  accumulate(sectionName: string, sectionData: any): void {
    this.data[sectionName] = sectionData
  }

  /**
   * Apply all accumulated hydration data and navigate (called by first When step)
   */
  async apply(url: string = '/'): Promise<void> {
    if (this.applied) return

    await hydratePage(this.page, {
      data: this.data,
      url,
    })

    this.applied = true
  }

  /**
   * Check if hydration has been applied
   */
  isApplied(): boolean {
    return this.applied
  }

  /**
   * Get accumulated data (for debugging)
   */
  getData(): Record<string, any> {
    return { ...this.data }
  }
}

/**
 * Playwright test fixture that provides HydrationAccumulator
 *
 * Usage in tests:
 *   const { Given, When, Then } = createBdd(test)
 *
 *   Given('user exists', ({ hydration }) => {
 *     hydration.accumulate('user', { id: 1, name: 'Alice' })
 *   })
 *
 *   When('I visit dashboard', ({ hydration }) => {
 *     await hydration.apply('/dashboard')  // Auto-hydrates + navigates
 *   })
 */
export function createHydrationFixture() {
  return {
    hydration: async ({ page }: { page: Page }, use: (r: HydrationAccumulator) => Promise<void>) => {
      const accumulator = new HydrationAccumulator(page)
      await use(accumulator)
    },
  }
}

/**
 * Higher-order function to wrap When steps with auto-hydration
 *
 * Usage:
 *   const When = autoHydrate(WhenRaw)
 *
 *   When('I click button', async ({ page }) => {
 *     // hydration.apply() called automatically before this
 *     await page.click('button')
 *   })
 */
export function autoHydrate(WhenFn: any) {
  return (pattern: string | RegExp, handler: any) => {
    WhenFn(pattern, async ({ page, hydration, fixtures }: any, ...args: any[]) => {
      // Only apply hydration in mock mode
      const mode = process.env.E2E_BACKEND || 'mock'
      if (mode === 'mock' && hydration && !hydration.isApplied()) {
        await hydration.apply()
      }

      // Call original handler
      return handler({ page, hydration, fixtures }, ...args)
    })
  }
}
