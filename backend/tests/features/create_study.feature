Feature: Create Study
  As an organization user (employee of a client organization)
  I want to create a new study within my organization
  So that I can organize UX research activities

  Scenario: Organization user creates a study successfully
    Given I am authenticated as an organization user with role "owner"
    And my organization has been onboarded by super admin
    When I POST /studies with title "Onboarding Feedback"
    Then the response status is 201
    And the response has a study_id
    And the study exists for my organization with title "Onboarding Feedback"

  Scenario: Cannot create study without authentication
    When an unauthenticated user POST /studies with title "Test Study"
    Then the response status is 401

  Scenario: Interviewee cannot create studies
    Given I am authenticated as an interviewee
    When I POST /studies with title "Test Study"  
    Then the response status is 403