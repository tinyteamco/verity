Feature: Manage studies

  Scenario: Create a study

    Given a signed-in organization user

    When they POST /studies with title "Onboarding Feedback"

    Then the response status is 201

    And the response has a study_id

    And the study exists for the user's org with title "Onboarding Feedback"



  Scenario: Update a study title

    Given an existing study titled "Old Name"

    When they PATCH /studies/{study_id} with title "New Name"

    Then the response status is 200

    And the study title is "New Name"