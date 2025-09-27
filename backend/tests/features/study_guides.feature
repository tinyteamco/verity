Feature: Study Guide Management
  As a UX researcher
  I want to create and manage interview guides for my studies
  So that I can structure my interviews effectively

  Background:
    Given a test organization with ID 1 exists
    And a study with ID 1 titled "User Onboarding Research" exists in organization 1

  Scenario Outline: Organization users can create study guides
    Given a signed-in organization user with role "<role>"
    When they PUT /studies/1/guide with content "# Interview Guide\n\n## Opening Questions\n1. Tell me about yourself"
    Then the response status is 200
    And the response has a study_id "1"
    And the response has content_md containing "# Interview Guide"
    And the response has an updated_at timestamp

    Examples:
      | role   |
      | owner  |
      | admin  |
      | member |

  Scenario: Update an existing study guide
    Given a signed-in organization user with role "admin"
    And a study guide exists for study 1 with content "# Old Guide"
    When they PUT /studies/1/guide with content "# Updated Guide\n\n## New Questions\n1. What's your experience?"
    Then the response status is 200
    And the response has content_md containing "# Updated Guide"
    And the response has content_md containing "New Questions"

  Scenario Outline: Organization users can retrieve study guides
    Given a signed-in organization user with role "<role>"
    And a study guide exists for study 1 with content "# Interview Guide\n\n## Questions\n1. How do you currently..."
    When they GET /studies/1/guide
    Then the response status is 200
    And the response has a study_id "1"
    And the response has content_md containing "# Interview Guide"

    Examples:
      | role   |
      | owner  |
      | admin  |
      | member |

  Scenario: Get study guide when none exists
    Given a signed-in organization user with role "admin"
    When they GET /studies/1/guide
    Then the response status is 404
    And the response contains an error message

  Scenario: Cannot access study guide from different organization
    Given a signed-in organization user with role "admin"
    And a study with ID 2 exists in a different organization
    When they GET /studies/2/guide
    Then the response status is 404

  Scenario: Cannot create study guide for non-existent study
    Given a signed-in organization user with role "admin"
    When they PUT /studies/999/guide with content "# Guide"
    Then the response status is 404

  Scenario: Interviewee users cannot access study guides
    Given a signed-in interviewee user
    When they GET /studies/1/guide
    Then the response status is 403

  Scenario: Unauthenticated users cannot access study guides
    When an unauthenticated user gets /studies/1/guide
    Then the response status is 401