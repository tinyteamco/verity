Feature: Audio Recording Upload
  As a participant completing an interview
  I want to upload my audio recording
  So that researchers can analyze my responses

  Background:
    Given a test organization with ID 1 exists
    And a study with ID 1 titled "User Experience Research" exists in organization 1
    And an interview with access_token "abc123" exists for study 1

  Scenario: Successfully upload audio recording
    When I upload an audio file for interview with access_token "abc123" with:
    Then the response status is 201
    And the response contains recording details
    And the recording has interview_id matching the interview
    And the recording has a unique recording_id
    And the recording has the correct file metadata

  Scenario: Upload audio with minimal metadata
    When I upload an audio file for interview with access_token "abc123" with:
    Then the response status is 201
    And the recording is created successfully

  Scenario: Cannot upload recording for non-existent interview
    When I upload an audio file for interview with access_token "invalid-token" with:
    Then the response status is 404
    And the error message is "Interview not found"

  Scenario: Cannot upload recording twice for same interview
    Given an audio recording exists for interview with access_token "abc123"
    When I upload an audio file for interview with access_token "abc123" with:
    Then the response status is 400
    And the error message contains "Recording already exists"

  Scenario: Cannot upload non-audio file
    When I upload a non-audio file for interview with access_token "abc123" with:
    Then the response status is 400
    And the error message contains "must be an audio file"

  Scenario: Upload without content type uses file detection
    When I upload an audio file for interview with access_token "abc123" with:
    Then the response status is 201
    And the recording is created successfully

  Scenario: Large file upload is handled correctly
    When I upload a large audio file for interview with access_token "abc123" with:
    Then the response status is 201
    And the recording metadata includes file size
    And the recording is stored in object storage

  Scenario: Complete upload-download cycle works
    When I upload an audio file for interview with access_token "abc123" with:
    Then the response status is 201
    And I can retrieve the recording metadata
    And I can download the uploaded audio file
    And the downloaded content matches the uploaded content

  Scenario: Download non-existent recording fails
    When I try to download recording with ID 99999
    Then the response status is 404
    And the error message is "Recording not found"

  Scenario: Get metadata for non-existent recording fails
    When I try to get metadata for recording with ID 99999
    Then the response status is 404
    And the error message is "Recording not found"