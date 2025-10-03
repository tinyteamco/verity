Feature: Super Admin Organization Management
  As a super admin
  I want to view organizations
  So I can manage the platform

  Background:
    Given I am logged in as super admin "admin@tinyteam.co"

  Scenario: View empty organizations list
    When I navigate to the admin dashboard
    Then I see "No organizations yet"

  Scenario: View existing organizations
    Given organizations "Acme Corp" and "Beta Inc" exist
    When I navigate to the admin dashboard
    Then I see "Acme Corp" in the organizations list
    And I see "Beta Inc" in the organizations list

  Scenario: Create a new organization
    When I navigate to the admin dashboard
    And I click "Create Organization"
    And I enter "New Startup Inc" as the organization name
    And I submit the organization form
    Then I see "New Startup Inc" in the organizations list
    And I don't see "No organizations yet"
