Feature: Interview Completion Callback
  As Pipecat
  I need to notify Verity when an interview is completed
  So that artifacts can be stored and interviews marked as done

  Background:
    Given I am a super admin user
    And an organization exists with name "acme-corp" and display_name "Acme Corp"
    And the organization has a study with title "Mobile Banking Study"
    And the study has an interview guide with content "# Interview Guide"
    And the study has a pending interview with external_participant_id "prolific_test123"

  Scenario: Verity receives completion callback with storage paths marks interview completed
    Given I have the access token for the pending interview
    When I POST to "/api/interview/{access_token}/complete" with:
      | transcript_url | https://storage.googleapis.com/verity-artifacts-prod/iv_001/transcript.txt |
      | recording_url  | https://storage.googleapis.com/verity-artifacts-prod/iv_001/recording.wav  |
      | notes          | Interview completed successfully. Duration: 18 minutes.                    |
    Then the response status code should be 200
    And the response should contain "message"
    And the interview status should be "completed"
    And the interview completed_at should be set
    And the interview transcript_url should be "https://storage.googleapis.com/verity-artifacts-prod/iv_001/transcript.txt"
    And the interview recording_url should be "https://storage.googleapis.com/verity-artifacts-prod/iv_001/recording.wav"
    And the interview notes should be "Interview completed successfully. Duration: 18 minutes."

  Scenario: Completion callback includes streaming transcript makes it viewable
    Given I have the access token for the pending interview
    When I POST to "/api/interview/{access_token}/complete" with:
      | transcript_url | https://storage.googleapis.com/verity-artifacts-prod/iv_002/transcript.txt |
    Then the response status code should be 200
    And the interview transcript_url should be "https://storage.googleapis.com/verity-artifacts-prod/iv_002/transcript.txt"
    And the interview recording_url should be None

  Scenario: Completion callback includes audio storage path makes audio downloadable
    Given I have the access token for the pending interview
    When I POST to "/api/interview/{access_token}/complete" with:
      | transcript_url | https://storage.googleapis.com/verity-artifacts-prod/iv_003/transcript.txt |
      | recording_url  | https://storage.googleapis.com/verity-artifacts-prod/iv_003/recording.wav  |
    Then the response status code should be 200
    And the interview transcript_url should be "https://storage.googleapis.com/verity-artifacts-prod/iv_003/transcript.txt"
    And the interview recording_url should be "https://storage.googleapis.com/verity-artifacts-prod/iv_003/recording.wav"

  Scenario: Pipecat retries completion callback for already complete interview returns 200 idempotent
    Given I have the access token for the pending interview
    And I have completed the interview with:
      | transcript_url | https://storage.googleapis.com/verity-artifacts-prod/iv_004/transcript.txt |
      | recording_url  | https://storage.googleapis.com/verity-artifacts-prod/iv_004/recording.wav  |
      | notes          | First completion                                                           |
    When I POST to "/api/interview/{access_token}/complete" with:
      | transcript_url | https://storage.googleapis.com/verity-artifacts-prod/iv_004/transcript.txt |
      | recording_url  | https://storage.googleapis.com/verity-artifacts-prod/iv_004/recording.wav  |
      | notes          | Retry attempt                                                              |
    Then the response status code should be 200
    And the interview notes should be "First completion"
