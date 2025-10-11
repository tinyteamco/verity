Feature: Researcher Interview Submissions
  As a UX researcher
  I want to view all interview submissions for my studies
  So that I can access recordings and transcripts

  Background:
    Given a test organization with ID 1 exists
    And a study with ID 1 titled "Mobile Banking Study" exists in organization 1
    And a completed interview exists for study 1 with transcript and recording

  Scenario: Researcher views list of completed interviews for study
    Given a signed-in organization user with role "admin"
    When they GET /api/orgs/1/studies/1/interviews
    Then the response status is 200
    And the response contains a list of interviews
    And each interview has status "completed"
    And each interview has transcript and recording flags

  Scenario: Researcher clicks interview to view transcript inline
    Given a signed-in organization user with role "admin"
    And an interview with ID 1 has a transcript stored in GCS
    When they GET /api/orgs/1/interviews/1/artifacts/transcript.txt
    Then the response status is 200
    And the response content type is "text/plain"
    And the response body contains transcript text

  Scenario: Researcher downloads audio file from interview
    Given a signed-in organization user with role "admin"
    And an interview with ID 1 has a recording stored in GCS
    When they GET /api/orgs/1/interviews/1/artifacts/recording.wav
    Then the response status is 200
    And the response content type is "audio/wav"
    And the response contains audio data

  Scenario: Researcher cannot access interviews from other organization
    Given a signed-in organization user with role "admin" in organization 1
    And a study with ID 2 exists in organization 2
    And a completed interview exists for study 2
    When they GET /api/orgs/2/studies/2/interviews
    Then the response status is 403
    And the error message is "User does not belong to organization"

  Scenario: Researcher cannot access artifacts from other organization
    Given a signed-in organization user with role "admin" in organization 1
    And a study with ID 2 exists in organization 2
    And a completed interview with ID 2 exists for study 2
    When they GET /api/orgs/2/interviews/2/artifacts/transcript.txt
    Then the response status is 403
    And the error message is "User does not belong to organization"

  Scenario: Only completed interviews appear in list
    Given a signed-in organization user with role "admin"
    And a pending interview exists for study 1
    And a completed interview exists for study 1 with transcript and recording
    When they GET /api/orgs/1/studies/1/interviews
    Then the response status is 200
    And the response contains 1 interview
    And all interviews have status "completed"
