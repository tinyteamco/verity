Feature: Super Admin Organization Management
  As a Verity platform super admin
  I want to create new organizations for client companies
  So that companies can start using the UXR platform

  Scenario: Super admin creates a new organization
    Given I am authenticated as a super admin in the organization tenant
    When I POST /orgs with name "Acme Corp"
    Then the response status is 201
    And the response has an org_id
    And a new organization exists in the database with name "Acme Corp"

  Scenario: Regular organization user cannot create organizations
    Given I am authenticated as a regular organization user
    When I POST /orgs with name "Test Corp"
    Then the response status is 403

  Scenario: Interviewee user cannot create organizations
    Given I am authenticated as an interviewee
    When I POST /orgs with name "Test Corp"
    Then the response status is 403

  Scenario: Unauthenticated user cannot create organizations
    When an unauthenticated user POST /orgs with name "Test Corp"
    Then the response status is 401