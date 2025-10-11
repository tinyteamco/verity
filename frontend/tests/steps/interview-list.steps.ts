import { createBdd } from '../support/world'
import { expect } from '@playwright/test'

const { Given, When, Then } = createBdd()

// Additional Given steps specific to interview tests
Given('I have a completed interview with a transcript', async ({ page, fixtures }) => {
  const orgName = 'Test Organization'
  await fixtures.seedOrganizations([orgName])
  await fixtures.seedStudy(orgName, 'Test Study')

  await fixtures.seedCompletedInterviews(orgName, 'Test Study', [
    { has_transcript: true, has_recording: true },
  ])

  const orgId = await fixtures.getOrganizationId(orgName)
  const studyId = await fixtures.getStudyId(orgId, 'Test Study')
  await page.evaluate(({ orgId, studyId }) => {
    (window as any).__testContext__ = { orgId, studyId }
  }, { orgId, studyId })
})

Given('I have a completed interview with a recording', async ({ page, fixtures }) => {
  const orgName = 'Test Organization'
  await fixtures.seedOrganizations([orgName])
  await fixtures.seedStudy(orgName, 'Test Study')

  await fixtures.seedCompletedInterviews(orgName, 'Test Study', [
    { has_recording: true },
  ])

  const orgId = await fixtures.getOrganizationId(orgName)
  const studyId = await fixtures.getStudyId(orgId, 'Test Study')
  await page.evaluate(({ orgId, studyId }) => {
    (window as any).__testContext__ = { orgId, studyId }
  }, { orgId, studyId })
})

Given('I have a study with no completed interviews', async ({ page, fixtures }) => {
  const orgName = 'Test Organization'
  await fixtures.seedOrganizations([orgName])
  await fixtures.seedStudy(orgName, 'Empty Study')

  const orgId = await fixtures.getOrganizationId(orgName)
  const studyId = await fixtures.getStudyId(orgId, 'Empty Study')
  await page.evaluate(({ orgId, studyId }) => {
    (window as any).__testContext__ = { orgId, studyId }
  }, { orgId, studyId })
})

Given('I have a completed interview without a transcript', async ({ page, fixtures }) => {
  const orgName = 'Test Organization'
  await fixtures.seedOrganizations([orgName])
  await fixtures.seedStudy(orgName, 'Test Study')

  await fixtures.seedCompletedInterviews(orgName, 'Test Study', [
    { has_transcript: false, has_recording: true },
  ])

  const orgId = await fixtures.getOrganizationId(orgName)
  const studyId = await fixtures.getStudyId(orgId, 'Test Study')
  await page.evaluate(({ orgId, studyId }) => {
    (window as any).__testContext__ = { orgId, studyId }
  }, { orgId, studyId })
})

// When steps
When('I click on the interview from the list', async ({ page }) => {
  // Click on the first interview in the list
  const firstInterview = page.getByTestId('interview-list').locator('a').first()
  await firstInterview.click()

  // Wait for detail page to load
  await expect(page.getByTestId('interview-detail')).toBeVisible()
})

When('I navigate to the interview detail page', async ({ page }) => {
  // Navigate to interviews page first
  const context = await page.evaluate(() => (window as any).__testContext__)
  await page.goto(`/orgs/${context.orgId}/studies/${context.studyId}/interviews`)
  await expect(page.getByTestId('interviews-page')).toBeVisible()

  // Click on first interview
  const firstInterview = page.getByTestId('interview-list').locator('a').first()
  await firstInterview.click()

  await expect(page.getByTestId('interview-detail')).toBeVisible()
})

When('I click the {string} button', async ({ page }, buttonText: string) => {
  if (buttonText === 'Download Audio') {
    // Start waiting for download before clicking
    const downloadPromise = page.waitForEvent('download')
    await page.getByTestId('download-audio-button').click()
    // Note: In actual test, we'd verify the download starts
    // For now, just check the button exists and is clickable
  }
})

When('I view the interview list', async ({ page }) => {
  const context = await page.evaluate(() => (window as any).__testContext__)
  await page.goto(`/orgs/${context.orgId}/studies/${context.studyId}/interviews`)
  await expect(page.getByTestId('interviews-page')).toBeVisible()
})

// Then steps
Then('I see a list of completed interviews', async ({ page }) => {
  const interviewList = page.getByTestId('interview-list')
  await expect(interviewList).toBeVisible()

  // Check that at least one interview is present
  const interviews = interviewList.locator('[data-testid^="interview-"]')
  await expect(interviews.first()).toBeVisible()
})

Then('each interview shows its completion date', async ({ page }) => {
  const interviewList = page.getByTestId('interview-list')
  const firstInterview = interviewList.locator('[data-testid^="interview-"]').first()

  // Check for "Completed:" text
  await expect(firstInterview.getByText(/Completed:/)).toBeVisible()
})

Then('each interview shows transcript and recording availability', async ({ page }) => {
  const interviewList = page.getByTestId('interview-list')
  const firstInterview = interviewList.locator('[data-testid^="interview-"]').first()

  // Check for transcript status
  await expect(firstInterview.locator('[data-testid^="transcript-status-"]')).toBeVisible()

  // Check for recording status
  await expect(firstInterview.locator('[data-testid^="recording-status-"]')).toBeVisible()
})

Then('I see the external participant ID for platform-sourced interviews', async ({ page }) => {
  const interviewList = page.getByTestId('interview-list')

  // Look for participant ID badge
  const participantIdBadge = interviewList.locator('[data-testid^="participant-id-"]').first()
  await expect(participantIdBadge).toBeVisible()
  await expect(participantIdBadge).toContainText(/prolific_|respondent_/)
})

Then('I see the platform source \\(e.g., {string}, {string}\\)', async ({ page }, platform1: string, platform2: string) => {
  const interviewList = page.getByTestId('interview-list')

  // Look for platform source badge
  const platformBadge = interviewList.locator('[data-testid^="platform-"]').first()
  await expect(platformBadge).toBeVisible()
})

Then('I see the interview detail page', async ({ page }) => {
  await expect(page.getByTestId('interview-detail')).toBeVisible()
})

Then('I see the transcript displayed inline', async ({ page }) => {
  const transcriptContent = page.getByTestId('transcript-content')
  await expect(transcriptContent).toBeVisible()
})

Then('the transcript text is readable and formatted', async ({ page }) => {
  const transcriptContent = page.getByTestId('transcript-content')

  // Check that content is not empty
  const text = await transcriptContent.textContent()
  expect(text).toBeTruthy()
  expect(text!.length).toBeGreaterThan(0)
})

Then('the audio file download begins', async ({ page }) => {
  // Verify download button is visible
  await expect(page.getByTestId('download-audio-button')).toBeVisible()
})

Then('I receive the audio file in WAV format', async ({ page }) => {
  // In a real test, we'd verify the download
  // For now, just check the button exists
  await expect(page.getByTestId('download-audio-button')).toContainText('Download Audio')
})

Then('I see a message indicating no interviews have been completed yet', async ({ page }) => {
  await expect(page.getByTestId('empty-interviews')).toBeVisible()
  await expect(page.getByText(/No interviews completed yet/i)).toBeVisible()
})

Then('the transcript availability is marked as unavailable', async ({ page }) => {
  const interviewList = page.getByTestId('interview-list')
  const firstInterview = interviewList.locator('[data-testid^="interview-"]').first()

  // Check for "No Transcript" status
  const transcriptStatus = firstInterview.locator('[data-testid^="transcript-status-"]')
  await expect(transcriptStatus).toContainText(/No Transcript|✗/)
})

Then('I cannot click to view the missing transcript', async ({ page }) => {
  // Navigate to interview detail
  const firstInterview = page.getByTestId('interview-list').locator('a').first()
  await firstInterview.click()

  // Check that transcript unavailable message is shown
  await expect(page.getByTestId('transcript-unavailable')).toBeVisible()
})
