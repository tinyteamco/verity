/**
 * Test fixtures for E2E testing with real backend and hydration
 */

import { Page } from '@playwright/test'
import type { HydrationAccumulator } from './bdd-hydration'
import type { Organization } from './hydration-registry'

export class TestFixtures {
  private backendPort: number
  private stubPort: number

  constructor(
    private page: Page,
    private hydration?: HydrationAccumulator,
    backendPort?: number,
    stubPort?: number
  ) {
    this.backendPort = backendPort || 8001
    this.stubPort = stubPort || 9099
  }

  async loginAsSuperAdmin(email: string): Promise<void> {
    // Real Firebase sign-in (no mock mode)
    await this.page.goto('/login')
    await this.page.fill('[name=email]', email)
    await this.page.fill('[name=password]', 'superadmin123')
    await this.page.click('button:has-text("Sign In")')
    await this.page.waitForURL('/')
  }

  async seedOrganizations(orgNames: string[]): Promise<void> {
    // Use hydration to accumulate org data for fast test setup
    const organizations: Organization[] = orgNames.map((name, index) => ({
      org_id: String(index + 1),
      name,
      created_at: new Date().toISOString(),
    }))

    this.hydration?.accumulate('organizations', organizations)

    // Also create via real API so backend has the data
    const token = await this.page.evaluate(() => localStorage.getItem('firebase_token'))

    for (const name of orgNames) {
      const response = await this.page.request.post(`http://localhost:${this.backendPort}/api/orgs`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        data: { name },
      })
      if (!response.ok()) {
        throw new Error(`Failed to create org ${name}: ${response.status()} ${await response.text()}`)
      }
    }
  }
}
