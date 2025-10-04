Feature: Organization User Management - Super Admin Access
  As a super admin
  I want to view users in any organization
  So that I can administer the platform

  Note: Organization users (owner/admin) use /orgs/current/users for their own org
        Super admin uses /orgs/{org_id}/users to view any org

  Scenario: Super admin can list users in an organization
    Given a signed-in super admin user
    And an organization exists with multiple users
    When they GET /orgs/{org_id}/users
    Then the response status is 200
    And the response contains a list of users
    And each user has email, role, and created_at fields

  Scenario: Super admin can see owner in users list
    Given a signed-in super admin user
    And an organization exists with an owner
    When they GET /orgs/{org_id}/users
    Then the response status is 200
    And the response includes the owner user

  Scenario: Organization admin cannot use super admin endpoint
    Given a signed-in organization user with role "admin"
    When they GET /orgs/{org_id}/users
    Then the response status is 403

  Scenario: Organization member cannot use super admin endpoint
    Given a signed-in organization user with role "member"
    When they GET /orgs/{org_id}/users
    Then the response status is 403

  Scenario: Unauthenticated user cannot list organization users
    Given an unauthenticated user
    When they GET /orgs/1/users
    Then the response status is 401

  Scenario: Super admin gets 404 for non-existent organization
    Given a signed-in super admin user
    When they GET /orgs/99999/users
    Then the response status is 404
