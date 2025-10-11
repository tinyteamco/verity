Feature: Study Settings - Reusable Interview Links

  As a researcher
  I want to view and copy reusable study links
  So that I can distribute interviews to participants via recruitment platforms or direct links

  Background:
    Given I am signed in as an organization owner
    And I have created a study with slug "mobile-banking-study"

  Scenario: Researcher views reusable link template in study settings
    When I navigate to the study settings page
    Then I see the reusable link template displayed
    And the link contains the study slug "mobile-banking-study"
    And the link includes the pid parameter placeholder

  Scenario: Researcher copies reusable link to clipboard
    When I navigate to the study settings page
    And I click the "Copy Link" button
    Then the reusable link is copied to my clipboard
    And I see a confirmation message

  Scenario: Researcher sees recruitment platform usage instructions
    When I navigate to the study settings page
    Then I see instructions for using the link with recruitment platforms
    And I see examples for Prolific integration
    And I see examples for Respondent integration
    And I see examples for UserTesting integration
    And I see explanation of the pid parameter
