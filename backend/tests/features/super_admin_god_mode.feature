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

  Scenario: Super admin can get specific organization by ID
    Given the super admin creates an organization named "Specific Org"
    When the super admin gets organization by ID for "Specific Org"
    Then the response status is 200
    And the organization name is "Specific Org"

  Scenario: Regular user cannot get organization by ID
    Given the super admin creates an organization named "Forbidden Org"
    And the regular user is added to "Forbidden Org" as owner
    And a second regular user exists with email "outsider@example.com"
    And the super admin creates an organization named "Other Company"
    And the second user is added to "Other Company" as owner
    When the regular user gets organization by ID for "Other Company"
    Then the response status is 403

  Scenario: Super admin creates organization with owner
    When the super admin creates an organization named "NewCo" with owner "newowner@newco.com"
    Then the response status is 201
    And the organization "NewCo" exists in the database
    And the owner "newowner@newco.com" exists in the database
    And the owner is linked to organization "NewCo"
    And the owner has role "owner"
    And a password reset link is returned

  Scenario: Organization owner can access their own organization
    Given the super admin creates an organization named "OwnerOrg" with owner "owner@ownerorg.com"
    When the owner "owner@ownerorg.com" requests their organization details
    Then the response status is 200
    And the organization name is "OwnerOrg"

  Scenario: Organization owner cannot access other organizations
    Given the super admin creates an organization named "OrgA" with owner "ownerA@orga.com"
    And the super admin creates an organization named "OrgB" with owner "ownerB@orgb.com"
    When the owner "ownerA@orga.com" requests organization details for "OrgB"
    Then the response status is 403