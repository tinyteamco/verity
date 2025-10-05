Feature: Study Management
  As an organization user
  I want to manage studies for my organization
  So I can organize and track user research projects

  Background:
    Given I am logged in as super admin "admin@tinyteam.co"
    And organization "Research Corp" exists

  Scenario: View empty studies list for organization
    When I navigate to organization "Research Corp" studies page
    Then I see "No studies yet"

  Scenario: Create a new study
    When I navigate to organization "Research Corp" studies page
    And I click "Create Study"
    And I enter "Onboarding Feedback" as the study title
    And I enter "Understanding user onboarding experience" as the study description
    And I submit the study form
    Then I see "Onboarding Feedback" in the studies list
    And I don't see "No studies yet"

  Scenario: View study details
    Given organization "Research Corp" has study "Checkout Flow Study"
    When I navigate to organization "Research Corp" studies page
    And I click on study "Checkout Flow Study"
    Then I see the study details page for "Checkout Flow Study"
    And I see the study description
    And I see the interview guide section
    And I see the interviews section

  Scenario: Edit study details
    Given organization "Research Corp" has study "Old Study Name"
    When I navigate to organization "Research Corp" studies page
    And I click on study "Old Study Name"
    And I click "Edit Study"
    And I enter "New Study Name" as the study title
    And I enter "Updated description" as the study description
    And I submit the study form
    Then I see "New Study Name" in the study title

  Scenario: Delete study
    Given organization "Research Corp" has studies:
      | title               |
      | Keep This Study     |
      | Delete This Study   |
    When I navigate to organization "Research Corp" studies page
    Then I see "Keep This Study" in the studies list
    And I see "Delete This Study" in the studies list
    When I click on study "Delete This Study"
    And I click "Delete Study"
    And I confirm the deletion
    Then I am redirected to the studies list page
    And I see "Keep This Study" in the studies list
    And I don't see "Delete This Study" in the studies list

  Scenario: View multiple studies
    Given organization "Research Corp" has studies:
      | title                  | description                    |
      | Onboarding Feedback    | User onboarding experience     |
      | Checkout Flow Study    | Payment and checkout process   |
      | Mobile App Usability   | Mobile interface feedback      |
    When I navigate to organization "Research Corp" studies page
    Then I see "Onboarding Feedback" in the studies list
    And I see "Checkout Flow Study" in the studies list
    And I see "Mobile App Usability" in the studies list
