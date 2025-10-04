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
      const slug = name.toLowerCase().replace(/\s+/g, '-')
      const ownerEmail = `owner@${slug.replace(/-/g, '')}.com`
      const response = await this.page.request.post(`http://localhost:${this.backendPort}/api/orgs`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        data: {
          name: slug,
          display_name: name,
          description: `Test organization: ${name}`,
          owner_email: ownerEmail,
        },
      })
      if (!response.ok()) {
        throw new Error(`Failed to create org ${name}: ${response.status()} ${await response.text()}`)
      }
    }
  }

  async seedOrganizationWithUsers(
    orgName: string,
    users: Array<{ email: string; role: string }>
  ): Promise<void> {
    const token = await this.page.evaluate(() => localStorage.getItem('firebase_token'))

    // Create organization with owner (first user should be owner)
    const ownerUser = users.find(u => u.role === 'owner')
    if (!ownerUser) {
      throw new Error('Organization must have an owner')
    }

    const slug = orgName.toLowerCase().replace(/\s+/g, '-')
    const orgResponse = await this.page.request.post(`http://localhost:${this.backendPort}/api/orgs`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      data: {
        name: slug,
        display_name: orgName,
        description: `Test organization: ${orgName}`,
        owner_email: ownerUser.email,
      },
    })

    if (!orgResponse.ok()) {
      throw new Error(`Failed to create org ${orgName}: ${orgResponse.status()} ${await orgResponse.text()}`)
    }

    const org = await orgResponse.json()
    const orgId = org.org_id

    // Add additional users (non-owners)
    for (const user of users) {
      if (user.role === 'owner') {
        continue // Owner already created
      }

      // Create Firebase user via stub
      const createUserResponse = await this.page.request.post(
        `http://localhost:${this.stubPort}/identitytoolkit.googleapis.com/v1/accounts`,
        {
          headers: { 'Content-Type': 'application/json' },
          data: {
            email: user.email,
            password: 'test123',
            returnSecureToken: true,
          },
        }
      )

      if (!createUserResponse.ok()) {
        throw new Error(`Failed to create Firebase user ${user.email}: ${createUserResponse.status()} ${await createUserResponse.text()}`)
      }

      const firebaseUser = await createUserResponse.json()

      // Create user in backend using test-only endpoint
      const userResponse = await this.page.request.post(
        `http://localhost:${this.backendPort}/api/test/orgs/${orgId}/users`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
          data: {
            email: user.email,
            role: user.role,
            firebase_uid: firebaseUser.localId,
          },
        }
      )

      if (!userResponse.ok()) {
        throw new Error(`Failed to create user ${user.email}: ${userResponse.status()} ${await userResponse.text()}`)
      }
    }
  }
}
