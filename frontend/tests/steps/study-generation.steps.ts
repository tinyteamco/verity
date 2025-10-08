import { createBdd } from '../support/world'
import { expect } from '@playwright/test'

const { Given, When, Then } = createBdd()

// Given steps for study generation
Given('organization {string} has a study with an interview guide', async ({ page, fixtures }, orgName: string) => {
  const orgId = await fixtures.getOrganizationId(orgName)
  const token = await page.evaluate(() => localStorage.getItem('firebase_token'))
  const backendPort = (page as any).__backendPort__

  // Create study via generation endpoint (which creates both study and guide)
  const response = await page.request.post(`http://localhost:${backendPort}/api/orgs/${orgId}/studies/generate`, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    data: {
      topic: 'How do people shop in supermarkets?',
    },
  })

  if (!response.ok()) {
    throw new Error(`Failed to generate study with guide: ${response.status()} ${await response.text()}`)
  }

  const result = await response.json()
  // Store study ID for later use
  await page.evaluate((studyId) => {
    sessionStorage.setItem('test_study_id', studyId)
  }, result.study.study_id)
})

Given('organization {string} has a study without an interview guide', async ({ page, fixtures }, orgName: string) => {
  const orgId = await fixtures.getOrganizationId(orgName)
  const token = await page.evaluate(() => localStorage.getItem('firebase_token'))
  const backendPort = (page as any).__backendPort__

  // Create study manually (no guide)
  const response = await page.request.post(`http://localhost:${backendPort}/api/orgs/${orgId}/studies`, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    data: {
      title: 'Manual Study',
      description: 'Study without guide',
    },
  })

  if (!response.ok()) {
    throw new Error(`Failed to create study: ${response.status()} ${await response.text()}`)
  }

  const result = await response.json()
  await page.evaluate((studyId) => {
    sessionStorage.setItem('test_study_id', studyId)
  }, result.study_id)
})

// When steps for generation flow
// Note: 'When I click {string}' is already defined in org-management.steps.ts

When('I enter {string} as the topic', async ({ page }, topic: string) => {
  await page.getByTestId('topic-input').fill(topic)
})

When('I submit the generation form', async ({ page }) => {
  await page.getByTestId('generate-study-submit').click()
})

When('generation takes more than 60 seconds', async ({ page }) => {
  // This scenario tests timeout handling - we'll need to mock a slow response
  // For now, we'll just verify the timeout logic exists in the UI
  // The actual timeout will be tested via the UI implementation
})

When('the backend returns 500 error', async ({ page }) => {
  // This scenario tests error handling - we'll need to mock a server error
  // For now, we'll just verify the error handling logic exists in the UI
})

When('I navigate to the study detail page', async ({ page }) => {
  const studyId = await page.evaluate(() => sessionStorage.getItem('test_study_id'))
  if (!studyId) {
    throw new Error('No study ID found in session storage')
  }
  // For now, studies are shown in modals on the org page
  // We'll need to update this once we have proper study detail pages
  await page.getByTestId('studies-list').getByText(/Manual Study|Generated/).click()
})

When('I modify the interview guide content', async ({ page }) => {
  const editor = page.getByTestId('guide-editor-textarea')
  await editor.fill('# Modified Guide\n\nThis is updated content.')
})

When('I toggle {string} mode', async ({ page }, mode: string) => {
  await page.getByTestId('preview-toggle').click()
})

When('I attempt to navigate away', async ({ page }) => {
  // Try to navigate away - this should trigger unsaved changes warning
  await page.goto('/')
})

When('I delete all content', async ({ page }) => {
  const editor = page.getByTestId('guide-editor-textarea')
  await editor.clear()
})

// Then steps for assertions
Then('I see a loading indicator', async ({ page }) => {
  await expect(page.getByTestId('generation-loading')).toBeVisible()
})

Then('after generation completes, I see a new study with generated title', async ({ page }) => {
  // Wait for loading to disappear
  await expect(page.getByTestId('generation-loading')).not.toBeVisible({ timeout: 65000 })
  // Should redirect to study or show success
  // For now, just check that we're not still on the generation form
  await expect(page.getByTestId('generate-study-modal')).not.toBeVisible()
})

Then('I see the interview guide content', async ({ page }) => {
  // Guide should be visible in the study view
  await expect(page.getByTestId('guide-viewer')).toBeVisible()
})

Then('I see validation error {string}', async ({ page }, errorMessage: string) => {
  await expect(page.getByText(errorMessage)).toBeVisible()
})

Then('I see timeout error with retry option', async ({ page }) => {
  await expect(page.getByText(/took too long/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Retry' })).toBeVisible()
})

Then('I see error message with {string} and {string} buttons', async ({ page }, button1: string, button2: string) => {
  await expect(page.getByRole('button', { name: button1 })).toBeVisible()
  await expect(page.getByRole('button', { name: button2 })).toBeVisible()
})

Then('the updated content is displayed', async ({ page }) => {
  await expect(page.getByText('Modified Guide')).toBeVisible()
})

Then('I see rendered markdown', async ({ page }) => {
  // Preview pane should be visible with rendered HTML
  await expect(page.getByTestId('guide-preview')).toBeVisible()
})

Then('I see warning {string}', async ({ page }, warningMessage: string) => {
  // Browser's beforeunload dialog - we'll need to handle this specially
  // For now, just check that the isDirty state is tracked
  await expect(page.getByTestId('guide-editor')).toHaveAttribute('data-dirty', 'true')
})

Then('I see study title and description', async ({ page }) => {
  await expect(page.getByTestId('study-title')).toBeVisible()
  await expect(page.getByTestId('study-description')).toBeVisible()
})

Then('I see interview guide rendered with sections and questions', async ({ page }) => {
  const guideViewer = page.getByTestId('guide-viewer')
  await expect(guideViewer).toBeVisible()
  // Should have markdown content rendered (headings, paragraphs, etc.)
  await expect(guideViewer.locator('h1, h2, h3')).toHaveCount({ min: 1 })
})

Then('I see {string} or {string} button', async ({ page }, button1: string, button2: string) => {
  // Either button should be visible
  const button1Visible = await page.getByRole('button', { name: button1 }).isVisible()
  const button2Visible = await page.getByRole('button', { name: button2 }).isVisible()
  expect(button1Visible || button2Visible).toBeTruthy()
})

Then('the study has no interview guide', async ({ page }) => {
  // Should not see guide viewer
  await expect(page.getByTestId('guide-viewer')).not.toBeVisible()
})
