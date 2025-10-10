Feature: Study Settings
  As a researcher
  I want to view and configure study settings
  So that I can manage reusable study links and participant identity flows

  Scenario: Researcher views reusable link template
    Given a signed-in organization user with role "owner"
    And a study exists with slug "mobile-banking-study"
    When they GET /studies/{study_id}
    Then the response status is 200
    And the response has a slug field
    And the slug is "mobile-banking-study"
