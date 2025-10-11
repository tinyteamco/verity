Feature: Interview Data API for Pipecat
  As pipecat interview service
  I want to fetch interview data via Verity's public API
  So that I can conduct interviews with participants

  Background:
    Given a study exists with slug "mobile-banking-study" and has an interview guide
    And an interview exists for the study with access_token and status "pending"

  Scenario: Pipecat fetches interview data with valid token returns 200 with study guide
    When pipecat calls GET /interview/{access_token}
    Then the response status is 200
    And the response contains study title "Mobile Banking App Usability Study"
    And the response contains interview guide markdown content
    And the response contains the access_token
    And the response contains interview status "pending"

  Scenario: Pipecat calls with completed interview token returns 410 Gone
    Given the interview status is "completed"
    When pipecat calls GET /interview/{access_token}
    Then the response status is 410
    And the error message contains "Interview already completed"

  Scenario: Pipecat calls with invalid token returns 404
    When pipecat calls GET /interview/invalid-token-12345
    Then the response status is 404
    And the error message contains "Interview not found"

  Scenario: Pipecat calls with expired token returns 410 Gone
    Given the interview expires_at is in the past
    When pipecat calls GET /interview/{access_token}
    Then the response status is 410
    And the error message contains "expired"
