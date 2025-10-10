import { createBdd } from '../support/world'
import { expect } from '@playwright/test'
import { DataTable } from '@cucumber/cucumber'

const { Given, When, Then } = createBdd()

// Given steps
Given('organization {string} exists', async ({ fixtures }, orgName: string) => {
  await fixtures.seedOrganizations([orgName])
})

Given('organization {string} has study {string}', async ({ fixtures }, orgName: string, studyTitle: string) => {
  await fixtures.seedStudy(orgName, studyTitle)
})

Given('organization {string} has studies:', async ({ fixtures }, orgName: string, dataTable: DataTable) => {
  const studies = dataTable.hashes()
  await fixtures.seedStudies(orgName, studies)
})

// Navigation - go to org detail page instead of separate studies page
When('I navigate to organization {string} studies page', async ({ page, fixtures }, orgName: string) => {
  const orgId = await fixtures.getOrganizationId(orgName)
  await page.goto(`/orgs/${orgId}`)
})

// Study list assertions
Then('I see {string} in the studies list', async ({ page }, studyTitle: string) => {
  const studiesList = page.getByTestId('studies-list')
  await expect(studiesList.getByText(studyTitle)).toBeVisible()
})

Then('I don\'t see {string} in the studies list', async ({ page }, studyTitle: string) => {
  const studiesList = page.getByTestId('studies-list')
  await expect(studiesList.getByText(studyTitle)).not.toBeVisible()
})

// Study creation
When('I enter {string} as the study title', async ({ page }, title: string) => {
  await page.getByTestId('study-title-input').fill(title)
})

When('I enter {string} as the study description', async ({ page }, description: string) => {
  await page.getByTestId('study-description-input').fill(description)
})

When('I submit the study form', async ({ page }) => {
  // Try create-study-submit first, then edit-study-submit
  const createButton = page.getByTestId('create-study-submit')
  const editButton = page.getByTestId('edit-study-submit')

  if (await createButton.isVisible()) {
    await createButton.click()
    // Wait for create modal to close
    await expect(page.getByTestId('create-study-modal')).not.toBeVisible({ timeout: 10000 })
  } else {
    await editButton.click()
    // Wait for edit modal to close
    await expect(page.getByTestId('edit-study-modal')).not.toBeVisible({ timeout: 10000 })
  }
})

// Study details navigation - now opens modal instead of navigating
When('I click on study {string}', async ({ page }, studyTitle: string) => {
  const studiesList = page.getByTestId('studies-list')
  await studiesList.getByText(studyTitle).click()
})

// Study details modal - now in modal instead of separate page
Then('I see the study details page for {string}', async ({ page }, studyTitle: string) => {
  // Detail modal should be visible
  await expect(page.getByTestId('edit-study-modal')).toBeVisible()
  // Click "Edit Details" to enter edit mode
  await page.getByRole('button', { name: 'Edit Details' }).click()
  // Now we should see the input fields with the study title
  await expect(page.getByTestId('study-title-input')).toHaveValue(studyTitle)
})

Then('I see the study description', async ({ page }) => {
  // Description is in the modal form
  await expect(page.getByTestId('study-description-input')).toBeVisible()
})

// Study deletion
When('I click delete for study {string}', async ({ page }, studyTitle: string) => {
  // Find the study in the list and click its delete button
  const studyItem = page.getByTestId('studies-list').locator('div').filter({ hasText: studyTitle })
  await studyItem.getByRole('button', { name: 'Delete' }).click()

  // Wait for delete confirmation modal to appear
  await expect(page.getByTestId('delete-study-modal')).toBeVisible()
})

When('I confirm the deletion', async ({ page }) => {
  await page.getByTestId('delete-study-confirm').click()

  // Wait for delete modal to close
  await expect(page.getByTestId('delete-study-modal')).not.toBeVisible({ timeout: 10000 })
})

Then('I am redirected to the studies list page', async ({ page }) => {
  // No redirect anymore - we stay on the org detail page
  await expect(page.getByTestId('org-studies-section')).toBeVisible()
})
