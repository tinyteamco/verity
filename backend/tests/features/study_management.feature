Feature: Study Management
  As an organization user
  I want to manage studies for my organization
  So that I can organize and track user research projects

  Scenario: Create a new study
    Given a signed-in organization user with role "owner"
    When they POST /studies with title "Onboarding Feedback"
    Then the response status is 201
    And the response has a study_id
    And the study title is "Onboarding Feedback"

  Scenario: List studies for organization
    Given a signed-in organization user with role "owner"
    And a study exists with title "Onboarding Feedback"
    And a study exists with title "Checkout Flow Study"
    When they GET /studies
    Then the response status is 200
    And the response contains 2 studies
    And the study list contains "Onboarding Feedback"
    And the study list contains "Checkout Flow Study"

  Scenario: Get a specific study
    Given a signed-in organization user with role "owner"
    And a study exists with title "Onboarding Feedback"
    When they GET /studies/{study_id}
    Then the response status is 200
    And the study title is "Onboarding Feedback"
    And the response has organization_id

  Scenario: Update a study title
    Given a signed-in organization user with role "owner"
    And a study exists with title "Old Name"
    When they PATCH /studies/{study_id} with title "New Name"
    Then the response status is 200
    And the study title is "New Name"

  Scenario: Delete a study
    Given a signed-in organization user with role "owner"
    And a study exists with title "Test Study"
    When they DELETE /studies/{study_id}
    Then the response status is 200

  Scenario Outline: All organization roles can create studies
    Given a signed-in organization user with role "<role>"
    When they POST /studies with title "Role Test Study"
    Then the response status is 201
    And the response has a study_id

    Examples:
      | role   |
      | owner  |
      | admin  |
      | member |

  Scenario Outline: All organization roles can list studies
    Given a signed-in organization user with role "<role>"
    And a study exists with title "Test Study"
    When they GET /studies
    Then the response status is 200
    And the study list contains "Test Study"

    Examples:
      | role   |
      | owner  |
      | admin  |
      | member |

  Scenario: Cannot access studies from other organizations
    Given a signed-in organization user with role "owner"
    And a study exists in a different organization with title "Other Org Study"
    When they GET /studies
    Then the response status is 200
    And the study list does not contain "Other Org Study"

  Scenario: Cannot get study from other organization by ID
    Given a signed-in organization user with role "owner"
    And a study exists in a different organization with title "Other Org Study"
    When they GET /studies/{other_org_study_id}
    Then the response status is 404

  Scenario: Interviewee cannot access studies
    Given a signed-in interviewee user
    When they GET /studies
    Then the response status is 403
    And the error message is "Organization user access required"

  Scenario: Unauthenticated user cannot access studies
    Given an unauthenticated user
    When they GET /studies
    Then the response status is 401