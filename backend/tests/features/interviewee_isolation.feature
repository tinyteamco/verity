Feature: Interviewee Tenant Isolation
  As a platform with separate organization and interviewee users
  I want to ensure interviewees cannot access organization resources
  So that tenant boundaries are properly enforced

  Scenario: Interviewee cannot access organization details
    Given a signed-in interviewee user
    When they GET /orgs/current
    Then the response status is 403
    And the error message is "Organization user access required"

  Scenario: Interviewee cannot list organization users
    Given a signed-in interviewee user
    When they GET /orgs/current/users
    Then the response status is 403
    And the error message is "Organization user access required"

  Scenario: Interviewee cannot create organizations
    Given a signed-in interviewee user
    When they POST /orgs with name "Hacker Org"
    Then the response status is 403
    And the error message is "Super admin access required"

  Scenario: Organization user cannot access interviewee endpoints
    Given a signed-in organization user with role "owner"
    When they try to access an interviewee-only endpoint
    Then the error message indicates wrong tenant