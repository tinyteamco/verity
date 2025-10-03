import { createBdd } from '../support/world'
import { expect } from '@playwright/test'

// Auto-hydration built into When - zero boilerplate!
const { Given, When, Then } = createBdd()

// Given steps accumulate hydration data
Given('I am logged in as super admin {string}', async ({ fixtures }, email: string) => {
  await fixtures.loginAsSuperAdmin(email)
})

Given('organizations {string} and {string} exist', async ({ fixtures }, org1: string, org2: string) => {
  await fixtures.seedOrganizations([org1, org2])
})

// When steps auto-apply hydration
When('I navigate to the admin dashboard', async ({ page }) => {
  // hydration.apply() called automatically by autoHydrate wrapper
  await expect(page).toHaveURL('/')
})

Then('I see {string}', async ({ page }, text: string) => {
  await expect(page.getByText(text)).toBeVisible()
})

Then('I see {string} in the organizations list', async ({ page }, orgName: string) => {
  const orgsList = page.getByTestId('organizations-list')
  await expect(orgsList.getByText(orgName)).toBeVisible()
})

When('I click {string}', async ({ page }, buttonText: string) => {
  await page.getByRole('button', { name: buttonText }).click()
})

When('I enter {string} as the organization name', async ({ page }, name: string) => {
  await page.getByTestId('org-name-input').fill(name)
})

When('I enter {string} as the owner email', async ({ page }, email: string) => {
  await page.getByTestId('owner-email-input').fill(email)
})

When('I submit the organization form', async ({ page }) => {
  await page.getByTestId('create-org-submit').click()

  // Wait for create modal to close (API call completes)
  await expect(page.getByTestId('create-org-modal')).not.toBeVisible({ timeout: 10000 })
})

Then('I see a success message with password reset link', async ({ page }) => {
  // Success modal should be visible
  await expect(page.getByTestId('success-modal')).toBeVisible()

  // Password reset link should be present
  await expect(page.getByTestId('password-reset-link')).toBeVisible()

  // Close the success modal
  await page.getByTestId('success-modal-close').click()

  // Modal should be closed
  await expect(page.getByTestId('success-modal')).not.toBeVisible()
})

Then('I don\'t see {string}', async ({ page }, text: string) => {
  await expect(page.getByText(text)).not.toBeVisible()
})

When('I click on the {string} organization', async ({ page }, orgName: string) => {
  const orgsList = page.getByTestId('organizations-list')
  await orgsList.getByText(orgName).click()
})

Then('I see the organization details page for {string}', async ({ page }, orgName: string) => {
  // Wait for navigation and verify we're on the org detail page
  await page.waitForURL(/\/orgs\/[^/]+$/)
  await expect(page.getByTestId('org-detail-name')).toHaveText(orgName)
})

Then('I see the organization users section', async ({ page }) => {
  await expect(page.getByTestId('org-users-section')).toBeVisible()
})

Then('I see the organization studies section', async ({ page }) => {
  await expect(page.getByTestId('org-studies-section')).toBeVisible()
})

When('I reload the page', async ({ page }) => {
  await page.reload()
})
