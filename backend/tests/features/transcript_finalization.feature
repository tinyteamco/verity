Feature: Transcript Finalization
  As a participant completing an interview
  I want to finalize my interview transcript
  So that researchers can analyze my responses

  Background:
    Given a test organization with ID 1 exists
    And a study with ID 1 titled "User Experience Research" exists in organization 1
    And an interview with access_token "abc123" exists for study 1

  Scenario: Successfully finalize transcript with multiple segments
    When I finalize the transcript for interview with access_token "abc123" with 3 segments
    Then the response status is 201
    And the response contains transcript_id
    And the transcript has 3 segments
    And the full_text contains all segment text concatenated

  Scenario: Finalize transcript with single segment
    When I finalize the transcript for interview with access_token "abc123" with 1 segment
    Then the response status is 201
    And the transcript is created successfully

  Scenario: Cannot finalize transcript for non-existent interview
    When I finalize the transcript for interview with access_token "invalid-token" with 1 segment
    Then the response status is 404
    And the error message is "Interview not found"

  Scenario: Cannot finalize transcript twice for same interview
    Given a transcript exists for interview with access_token "abc123"
    When I finalize the transcript for interview with access_token "abc123" with 1 segment
    Then the response status is 400
    And the error message contains "Transcript already exists"

  Scenario: Cannot finalize with empty segments
    When I finalize the transcript for interview with access_token "abc123" with 0 segments
    Then the response status is 400
    And the error message contains "at least one segment"