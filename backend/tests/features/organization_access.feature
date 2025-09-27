Feature: Organization Access Control
  As a platform with multiple user types
  I want to ensure proper access control to organization endpoints
  So that organization data is properly secured

  Scenario: Member can access their current organization
    Given a signed-in organization user with role "member"
    When they GET /orgs/current
    Then the response status is 200
    And the response contains their organization details

  Scenario: Admin can access their current organization
    Given a signed-in organization user with role "admin"
    When they GET /orgs/current
    Then the response status is 200
    And the response contains their organization details

  Scenario: Owner can access their current organization
    Given a signed-in organization user with role "owner"
    When they GET /orgs/current
    Then the response status is 200
    And the response contains their organization details

  Scenario: Interviewee cannot access organization endpoint
    Given a signed-in interviewee user
    When they GET /orgs/current
    Then the response status is 403

  Scenario: Unauthenticated user cannot access organization endpoint
    Given an unauthenticated user
    When they GET /orgs/current
    Then the response status is 401

  Scenario: Super admin cannot access organization endpoint directly
    Given a signed-in super admin user
    When they GET /orgs/current
    Then the response status is 403

  Scenario: User not associated with any organization
    Given a signed-in organization user not in database
    When they GET /orgs/current
    Then the response status is 403
    And the error message is "User not associated with any organization"