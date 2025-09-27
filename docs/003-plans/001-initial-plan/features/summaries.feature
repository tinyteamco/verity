Feature: Generate summaries asynchronously

  Scenario: Generate interview summary (fake-async)

    Given an interview has a transcript

    When they POST /interviews/{interview_id}/summary:generate

    Then the response status is 202

    And a job_id is returned

    When the job runner processes jobs

    Then GET /jobs/{job_id} eventually returns status "succeeded"

    And GET /interviews/{interview_id}/summary returns the generated summary



  Scenario: Generate study summary (manual trigger)

    Given a study with at least one interview summary

    When they POST /studies/{study_id}/summary:generate

    Then the response status is 202

    And a job_id is returned

