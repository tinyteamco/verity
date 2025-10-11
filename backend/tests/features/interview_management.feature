Feature: Self-Led Interview Management
  As a UX researcher
  I want to generate interview links for my studies
  So that participants can complete self-led interviews

  Background:
    Given a test organization with ID 1 exists
    And a study with ID 1 titled "User Onboarding Research" exists in organization 1

  Scenario Outline: Organization users can generate interview links
    Given a signed-in organization user with role "<role>"
    When they POST /studies/1/interviews to generate a link
    Then the response status is 201
    And the response has an interview object
    And the response has an interview_url
    And the interview has a unique access_token
    And the interview has study_id "1"
    And the interview has status "pending"
    And the interview has no interviewee_firebase_uid

    Examples:
      | role   |
      | owner  |
      | admin  |
      | member |

  Scenario Outline: Organization users can list interviews
    Given a signed-in organization user with role "<role>"
    And an interview link exists for study 1
    And another interview link exists for study 1
    When they GET /studies/1/interviews
    Then the response status is 200
    And the response contains 2 interviews
    And each interview has an access_token

    Examples:
      | role   |
      | owner  |
      | admin  |
      | member |

  Scenario: Get specific interview details
    Given a signed-in organization user with role "admin"
    And an interview link exists for study 1
    When they GET /studies/1/interviews/{interview_id}
    Then the response status is 200
    And the interview has status "pending"
    And the interview has a unique access_token

  Scenario: Cannot generate interview for non-existent study
    Given a signed-in organization user with role "admin"
    When they POST /studies/999/interviews to generate a link
    Then the response status is 404
    And the error message is "Study not found"

  Scenario: Cannot access interviews from different organization
    Given a signed-in organization user with role "admin"
    And a study with ID 2 exists in a different organization
    When they GET /studies/2/interviews
    Then the response status is 404
    And the error message is "Study not found"

  Scenario: Interviewee users cannot generate interview links
    Given a signed-in interviewee user
    When they POST /studies/1/interviews to generate a link
    Then the response status is 403
    And the error message is "Organization user access required"

  Scenario: Unauthenticated users cannot generate interview links
    When an unauthenticated user posts to /studies/1/interviews
    Then the response status is 401

  # Public Interview Access (No Auth Required)

  Scenario: Participant can access interview via link
    Given an interview link exists for study 1 with access_token "abc123"
    When they GET /interview/abc123 without authentication
    Then the response status is 200
    And the response has an interview object
    And the response has a study object
    And the study has title "User Onboarding Research"
    And the study has an interview_guide

  Scenario: Participant can complete interview
    Given an interview link exists for study 1 with access_token "abc123"
    When they POST /interview/abc123/complete without authentication with:
      | transcript_url | https://storage.example.com/transcript.json |
      | recording_url  | https://storage.example.com/recording.mp3   |
      | notes         | Great insights from user                     |
    Then the response status is 200
    And the interview status is now "completed"

  Scenario: Cannot complete interview twice
    Given an interview link exists for study 1 with access_token "abc123"
    And the interview has been completed
    When they POST /interview/abc123/complete without authentication with:
      | transcript_url | https://storage.example.com/transcript2.json |
    Then the response status is 200

  Scenario: Cannot access non-existent interview
    When they GET /interview/invalid-token without authentication
    Then the response status is 404

  Scenario: Participant can claim interview after sign-in
    Given an interview link exists for study 1 with access_token "abc123"
    And a signed-in interviewee user with uid "test-interviewee-uid"
    When they POST /interview/abc123/claim
    Then the response status is 200
    And the interview is now associated with "test-interviewee-uid"

  Scenario: Cannot claim already claimed interview
    Given an interview link exists for study 1 with access_token "abc123"
    And the interview is associated with "other-user-uid"
    And a signed-in interviewee user with uid "test-interviewee-uid"
    When they POST /interview/abc123/claim
    Then the response status is 400
    And the error message contains "already claimed"