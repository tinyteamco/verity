import { createBdd } from '../support/world'
import { expect } from '@playwright/test'
import { DataTable } from '@cucumber/cucumber'

// Auto-hydration built into When - zero boilerplate!
const { Given, When, Then } = createBdd()

// Given steps accumulate hydration data
Given('I am logged in as super admin {string}', async ({ fixtures }, email: string) => {
  await fixtures.loginAsSuperAdmin(email)
})

Given('organizations {string} and {string} exist', async ({ fixtures }, org1: string, org2: string) => {
  await fixtures.seedOrganizations([org1, org2])
})

Given('organization {string} exists with users:', async ({ fixtures }, orgName: string, dataTable: DataTable) => {
  const users = dataTable.hashes() // hashes() converts table to array of objects
  await fixtures.seedOrganizationWithUsers(orgName, users)
})

// When steps auto-apply hydration
When('I navigate to the admin dashboard', async ({ page }) => {
  // hydration.apply() called automatically by autoHydrate wrapper
  await page.goto('/')
  // Don't assert URL here - let Then steps verify the outcome
  // (logged in users stay on /, logged out users redirect to /login)
})

Then('I see {string}', async ({ page }, text: string) => {
  await expect(page.getByText(text)).toBeVisible()
})

Then('I see {string} in the organizations list', async ({ page }, orgName: string) => {
  const orgsList = page.getByTestId('organizations-list')
  await expect(orgsList.getByText(orgName)).toBeVisible()
})

When('I click {string}', async ({ page }, buttonText: string) => {
  // Special handling for Logout button - wait for redirect
  if (buttonText === 'Logout') {
    await page.getByRole('button', { name: buttonText }).click()
    await page.waitForURL('/login', { timeout: 5000 })
  } else {
    await page.getByRole('button', { name: buttonText }).click()
  }
})

When('I enter {string} as the organization name', async ({ page }, name: string) => {
  // Convert to slug for the slug field
  const slug = name.toLowerCase().replace(/\s+/g, '-')
  await page.getByTestId('org-name-input').fill(slug)
  // Also fill display_name
  await page.getByTestId('display-name-input').fill(name)
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

Then('I see {string} in the users list', async ({ page }, email: string) => {
  const usersList = page.getByTestId('org-users-list')
  await expect(usersList.getByText(email)).toBeVisible()
})

Then('I see user {string} with role {string}', async ({ page }, email: string, role: string) => {
  const usersList = page.getByTestId('org-users-list')
  const userRow = usersList.locator(`[data-user-email="${email}"]`)
  await expect(userRow.getByTestId('user-role')).toHaveText(role)
})

// Add User modal steps
When('I enter {string} as the user email', async ({ page }, email: string) => {
  await page.getByTestId('user-email-input').fill(email)
})

When('I select {string} as the user role', async ({ page }, role: string) => {
  // Click the Select trigger to open the dropdown
  await page.getByTestId('user-role-select').click()
  // Click the option with the specified role (capitalize first letter)
  const capitalizedRole = role.charAt(0).toUpperCase() + role.slice(1)
  // Find the option within the dropdown portal using getByLabel (Radix uses labels for items)
  await page.getByLabel(capitalizedRole, { exact: true }).click()
})

When('I submit the add user form', async ({ page }) => {
  await page.getByTestId('add-user-submit').click()

  // Wait for add user modal to close (API call completes)
  await expect(page.getByTestId('add-user-modal')).not.toBeVisible({ timeout: 10000 })
})

Then('I see a success message for adding user', async ({ page }) => {
  // Success modal should be visible
  await expect(page.getByTestId('user-success-modal')).toBeVisible()

  // Close the success modal
  await page.getByTestId('user-success-modal-close').click()

  // Modal should be closed
  await expect(page.getByTestId('user-success-modal')).not.toBeVisible()
})

// Logout steps
Then('I am redirected to the login page', async ({ page }) => {
  // Wait for navigation to complete (React Router redirect)
  await page.waitForURL('/login', { timeout: 5000 })
  await expect(page).toHaveURL('/login')
})
