Feature: Cross-Organization Security
  As a multi-tenant platform
  I want to ensure users cannot access other organizations' data
  So that organization data remains isolated

  Background:
    Given two organizations exist:
      | org_name    | org_id |
      | Acme Corp   | 1      |
      | Beta Inc    | 2      |
    And the following users exist:
      | email              | organization | role   |
      | alice@acme.com     | Acme Corp   | owner  |
      | bob@beta.com       | Beta Inc    | owner  |
      | charlie@acme.com   | Acme Corp   | member |

  Scenario: User from one org cannot list users from another org
    Given I am signed in as "alice@acme.com"
    When I try to list users for "Beta Inc"
    Then the response status is 403

  Scenario: User can only see their own organization details
    Given I am signed in as "bob@beta.com"
    When they GET /orgs/current
    Then the response status is 200
    And the organization name is "Beta Inc"
    And the organization name is not "Acme Corp"

  Scenario: Organization isolation for user lists - owner sees only their org
    Given I am signed in as "alice@acme.com"
    When they GET /orgs/current/users
    Then the response status is 200
    And the user list contains "charlie@acme.com"
    And the user list does not contain "bob@beta.com"
  
  Scenario: Organization isolation for user lists - member cannot see users
    Given I am signed in as "charlie@acme.com"
    When they GET /orgs/current/users
    Then the response status is 403