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

// Navigation
When('I navigate to organization {string} studies page', async ({ page, fixtures }, orgName: string) => {
  const orgId = await fixtures.getOrganizationId(orgName)
  await page.goto(`/orgs/${orgId}/studies`)
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
  await page.getByTestId('study-form-submit').click()

  // Wait for create/edit modal to close
  await expect(page.getByTestId('study-modal')).not.toBeVisible({ timeout: 10000 })
})

// Study details navigation
When('I click on study {string}', async ({ page }, studyTitle: string) => {
  const studiesList = page.getByTestId('studies-list')
  await studiesList.getByRole('link', { name: studyTitle }).click()
})

// Study details page
Then('I see the study details page for {string}', async ({ page }, studyTitle: string) => {
  await page.waitForURL(/\/orgs\/[^/]+\/studies\/[^/]+$/)
  await expect(page.getByTestId('study-detail-title')).toHaveText(studyTitle)
})

Then('I see the study description', async ({ page }) => {
  await expect(page.getByTestId('study-detail-description')).toBeVisible()
})

Then('I see the interview guide section', async ({ page }) => {
  await expect(page.getByTestId('interview-guide-section')).toBeVisible()
})

Then('I see the interviews section', async ({ page }) => {
  await expect(page.getByTestId('interviews-section')).toBeVisible()
})

// Study editing - reuse the button click step from org-management

Then('I see {string} in the study title', async ({ page }, title: string) => {
  await expect(page.getByTestId('study-detail-title')).toHaveText(title)
})

// Study deletion
When('I confirm the deletion', async ({ page }) => {
  await page.getByTestId('confirm-delete-button').click()
})

Then('I am redirected to the studies list page', async ({ page }) => {
  await page.waitForURL(/\/orgs\/[^/]+\/studies$/)
})
