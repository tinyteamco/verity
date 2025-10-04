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

  Scenario: Create a new organization with owner
    When I navigate to the admin dashboard
    And I click "Create Organization"
    And I enter "New Startup Inc" as the organization name
    And I enter "owner@newstartup.com" as the owner email
    And I submit the organization form
    Then I see a success message with password reset link
    And I see "New Startup Inc" in the organizations list
    And I don't see "No organizations yet"

  Scenario: View organization details
    Given organizations "Acme Corp" and "Beta Inc" exist
    When I navigate to the admin dashboard
    And I click on the "Acme Corp" organization
    Then I see the organization details page for "Acme Corp"
    And I see the organization users section
    And I see the organization studies section

  Scenario: Refresh on organization details page
    Given organizations "Acme Corp" and "Beta Inc" exist
    When I navigate to the admin dashboard
    And I click on the "Acme Corp" organization
    And I reload the page
    Then I see the organization details page for "Acme Corp"
    And I see the organization users section
    And I see the organization studies section

  Scenario: View organization users
    Given organization "Tech Startup" exists with users:
      | email                | role   |
      | owner@techstartup.io | owner  |
      | admin@techstartup.io | admin  |
      | dev@techstartup.io   | member |
    When I navigate to the admin dashboard
    And I click on the "Tech Startup" organization
    Then I see the organization details page for "Tech Startup"
    And I see "owner@techstartup.io" in the users list
    And I see "admin@techstartup.io" in the users list
    And I see "dev@techstartup.io" in the users list
    And I see user "owner@techstartup.io" with role "owner"
    And I see user "admin@techstartup.io" with role "admin"
    And I see user "dev@techstartup.io" with role "member"
