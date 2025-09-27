Feature: Org roles on company API

  Scenario: Members cannot list company users

    Given a signed-in company user with role "member"

    When they GET /orgs/current/users

    Then the response status is 403



  Scenario: Owner can list company users

    Given a signed-in company user with role "owner"

    When they GET /orgs/current/users

    Then the response status is 200

