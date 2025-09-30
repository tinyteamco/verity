Feature: Super Admin God Mode
  As a platform super admin
  I want invisible access to all organizations
  So that I can provide support without appearing in member lists

  Background:
    Given a super admin user exists with email "superadmin@platform.com"
    And a regular user exists with email "owner@company.com"

  Scenario: Super admin can create an organization
    When the super admin creates an organization named "Acme Corp"
    Then the response status is 201
    And the organization "Acme Corp" exists in the database

  Scenario: Super admin can access any organization without a User record
    Given the super admin creates an organization named "Test Org"
    And the regular user is added to "Test Org" as owner
    When the super admin requests organization details for "Test Org"
    Then the response status is 200
    And the organization name is "Test Org"

  Scenario: Super admin can create studies in any organization
    Given the super admin creates an organization named "Research Co"
    And the regular user is added to "Research Co" as owner
    And the regular user creates a study titled "UX Study" in their organization
    When the super admin creates a study titled "Admin Study" in "Research Co"
    Then the response status is 201
    And the study "Admin Study" belongs to "Research Co"

  Scenario: Super admin can access interviews across all organizations
    Given the super admin creates an organization named "Client Org"
    And the regular user is added to "Client Org" as owner
    And the regular user creates a study titled "Customer Research" in their organization
    And an interview with access_token "test123" exists for the study
    When the super admin retrieves interview with access_token "test123"
    Then the response status is 200
    And the interview data is returned

  Scenario: Super admin does not appear in organization user lists
    Given the super admin creates an organization named "Private Corp"
    And the regular user is added to "Private Corp" as owner
    When the super admin accesses studies in "Private Corp"
    And the regular user lists users in their organization
    Then the response status is 200
    And the user list has 1 user
    And "test-superadmin@test.com" does not appear in the user list

  Scenario: Super admin can access organization current endpoint
    Given the super admin creates an organization named "Test Company"
    And the regular user is added to "Test Company" as owner
    When the super admin requests organization details for "Test Company"
    Then the response status is 200
    And the organization name is "Test Company"

  Scenario: Regular user cannot access organizations they don't belong to
    Given the super admin creates an organization named "Their Org"
    And the regular user is added to "Their Org" as owner
    And a second regular user exists with email "other@example.com"
    And the super admin creates an organization named "Other Org"
    And the second user is added to "Other Org" as owner
    And the second user creates a study titled "Other Study" in their organization
    When the regular user lists studies in their organization
    Then the response status is 200
    And the study list is empty
    And "Other Study" does not appear in the study list