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

When('I submit the organization form', async ({ page }) => {
  // Listen for console messages to debug
  const consoleMessages: string[] = []
  page.on('console', msg => {
    const text = msg.text()
    consoleMessages.push(text)
    if (text.includes('[CreateOrg]') || text.includes('Error')) {
      console.log('Browser:', text)
    }
  })

  await page.getByTestId('create-org-submit').click()

  // Wait a moment for the API call
  await page.waitForTimeout(2000)

  // Check if modal closed
  const modalVisible = await page.getByTestId('create-org-modal').isVisible()
  if (modalVisible) {
    console.log('Modal still visible! Console logs:', consoleMessages.join('\n'))
    throw new Error('Modal did not close - org creation failed')
  }
})

Then('I don\'t see {string}', async ({ page }, text: string) => {
  await expect(page.getByText(text)).not.toBeVisible()
})
