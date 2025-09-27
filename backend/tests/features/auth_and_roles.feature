Feature: Org roles for organization users

  Scenario: Members cannot list organization users

    Given a signed-in organization user with role "member"

    When they GET /orgs/current/users

    Then the response status is 403



  Scenario: Owner can list organization users

    Given a signed-in organization user with role "owner"

    When they GET /orgs/current/users

    Then the response status is 200