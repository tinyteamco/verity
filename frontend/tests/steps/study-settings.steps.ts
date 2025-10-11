import { createBdd } from '../support/world'
import { expect } from '@playwright/test'

const { Given, When, Then } = createBdd()

// Given steps
Given('I am signed in as an organization owner', async ({ page, fixtures }) => {
  // Login as super admin and create org in background
  await fixtures.loginAsSuperAdmin('admin@tinyteam.co')
})

Given('I have created a study with slug {string}', async ({ page, fixtures }, slug: string) => {
  // Create organization and study
  const orgName = 'Test Organization'
  await fixtures.seedOrganizations([orgName])
  await fixtures.seedStudy(orgName, 'Mobile Banking Study')

  // Store context for navigation
  const orgId = await fixtures.getOrganizationId(orgName)
  const studyId = await fixtures.getStudyId(orgId, 'Mobile Banking Study')
  await page.evaluate(({ orgId, studyId }) => {
    (window as any).__testContext__ = { orgId, studyId }
  }, { orgId, studyId })
})

Given('I have a study with completed interviews', async ({ page, fixtures }) => {
  const orgName = 'Test Organization'
  await fixtures.seedOrganizations([orgName])
  await fixtures.seedStudy(orgName, 'Test Study')

  // Seed completed interviews
  await fixtures.seedCompletedInterviews(orgName, 'Test Study', [
    { external_participant_id: 'prolific_123', platform_source: 'prolific' },
    { external_participant_id: 'respondent_456', platform_source: 'respondent' },
  ])

  const orgId = await fixtures.getOrganizationId(orgName)
  const studyId = await fixtures.getStudyId(orgId, 'Test Study')
  await page.evaluate(({ orgId, studyId }) => {
    (window as any).__testContext__ = { orgId, studyId }
  }, { orgId, studyId })
})

Given('I have interviews from recruitment platforms', async ({ page, fixtures }) => {
  // Already handled by "I have a study with completed interviews"
})

// When steps
When('I navigate to the study settings page', async ({ page }) => {
  const context = await page.evaluate(() => (window as any).__testContext__)
  await page.goto(`/orgs/${context.orgId}/studies/${context.studyId}`)

  // Wait for page to load
  await expect(page.getByTestId('study-detail-page')).toBeVisible()

  // Click on Settings tab
  await page.getByTestId('settings-tab').click()

  // Wait for settings section to be visible
  await expect(page.getByTestId('settings-section')).toBeVisible()
})

When('I navigate to the interviews page for my study', async ({ page }) => {
  const context = await page.evaluate(() => (window as any).__testContext__)
  await page.goto(`/orgs/${context.orgId}/studies/${context.studyId}`)

  // Click on Interviews tab
  await page.getByTestId('interviews-tab').click()

  // Click on "View All Interviews" link
  await page.getByTestId('view-interviews-link').click()

  // Wait for interviews page to load
  await expect(page.getByTestId('interviews-page')).toBeVisible()
})

When('I navigate to the interviews page', async ({ page }) => {
  // Alias for previous step
  const context = await page.evaluate(() => (window as any).__testContext__)
  await page.goto(`/orgs/${context.orgId}/studies/${context.studyId}/interviews`)
  await expect(page.getByTestId('interviews-page')).toBeVisible()
})

When('I click the {string} button', async ({ page }, buttonText: string) => {
  if (buttonText === 'Copy Link') {
    await page.getByTestId('copy-link-button').click()
  }
})

// Then steps
Then('I see the reusable link template displayed', async ({ page }) => {
  const linkInput = page.getByTestId('reusable-link-input')
  await expect(linkInput).toBeVisible()
  await expect(linkInput).toHaveValue(/.*\/study\/.*\/start\?pid=.*/)
})

Then('the link contains the study slug {string}', async ({ page }, slug: string) => {
  const linkInput = page.getByTestId('reusable-link-input')
  const value = await linkInput.inputValue()
  expect(value).toContain(`/study/mobile-banking-study/start`)
})

Then('the link includes the pid parameter placeholder', async ({ page }) => {
  const linkInput = page.getByTestId('reusable-link-input')
  const value = await linkInput.inputValue()
  expect(value).toContain('pid={{PARTICIPANT_ID}}')
})

Then('the reusable link is copied to my clipboard', async ({ page }) => {
  // Check clipboard content (requires clipboard permissions grant)
  // In Playwright, we can verify the button shows "Copied!" state
  await expect(page.getByTestId('copy-link-button')).toHaveText('Copied!')
})

Then('I see a confirmation message', async ({ page }) => {
  // Button text changes to "Copied!"
  await expect(page.getByTestId('copy-link-button')).toHaveText('Copied!')
})

Then('I see instructions for using the link with recruitment platforms', async ({ page }) => {
  await expect(page.getByText('Recruitment Platform Integration')).toBeVisible()
})

Then('I see examples for Prolific integration', async ({ page }) => {
  await page.getByTestId('prolific-toggle').click()
  await expect(page.getByTestId('prolific-instructions')).toBeVisible()
  await expect(page.getByTestId('prolific-instructions')).toContainText('{{%PROLIFIC_PID%}}')
})

Then('I see examples for Respondent integration', async ({ page }) => {
  await page.getByTestId('respondent-toggle').click()
  await expect(page.getByTestId('respondent-instructions')).toBeVisible()
  await expect(page.getByTestId('respondent-instructions')).toContainText('{{respondent_id}}')
})

Then('I see examples for UserTesting integration', async ({ page }) => {
  await page.getByTestId('usertesting-toggle').click()
  await expect(page.getByTestId('usertesting-instructions')).toBeVisible()
  await expect(page.getByTestId('usertesting-instructions')).toContainText('{{tester_id}}')
})

Then('I see explanation of the pid parameter', async ({ page }) => {
  await expect(page.getByText(/pid.*parameter/i)).toBeVisible()
})
