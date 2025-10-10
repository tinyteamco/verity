Feature: Interview Access
  As a participant
  I want to access interviews via reusable study links
  So that I can participate in research studies

  Background:
    Given a study exists with slug "mobile-banking-study" and has an interview guide

  Scenario: Participant accesses reusable link with pid
    When a participant accesses GET /study/{slug}/start?pid=prolific_abc123
    Then the response is a 302 redirect
    And the redirect Location header contains "access_token="
    And the redirect Location header contains "verity_api="
    And an interview is created with external_participant_id "prolific_abc123"
    And the interview platform_source is "prolific"

  Scenario: Participant accesses reusable link without pid
    When a participant accesses GET /study/{slug}/start
    Then the response is a 302 redirect
    And the redirect Location header contains "access_token="
    And an interview is created with external_participant_id null

  Scenario: Deduplication prevents duplicate interview for same external_participant_id
    Given an interview already exists for study "mobile-banking-study" with pid "prolific_abc123"
    When a participant accesses GET /study/{slug}/start?pid=prolific_abc123
    Then the response is a 302 redirect
    And no new interview is created
    And the redirect uses the existing interview access_token

  Scenario: Accessing non-existent study slug returns 404
    When a participant accesses GET /study/non-existent-study/start
    Then the response status is 404
    And the error message contains "Study not found"

  Scenario: Participant accesses valid interview link and receives redirect
    When a participant accesses GET /study/{slug}/start
    Then the response is a 302 redirect
    And the redirect Location header contains "access_token="
    And the redirect Location header contains "verity_api="

  Scenario: Participant tries to access completed interview shows error page
    Given an interview already exists for study "mobile-banking-study" with pid "prolific_completed" and status "completed"
    When a participant accesses GET /study/{slug}/start?pid=prolific_completed
    Then the response status is 400
    And the response is HTML content
    And the error page contains "Interview Already Completed"
