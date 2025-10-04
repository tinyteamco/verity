Feature: Organization User Management - Super Admin Access
  As a super admin
  I want to view and manage users in any organization
  So that I can administer the platform

  Note: Organization users (owner/admin) use /orgs/current/users for their own org
        Super admin uses /orgs/{org_id}/users to view/manage any org

  # ===== Viewing Users =====

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

  # ===== Creating Users =====

  Scenario: Super admin adds admin user to organization
    Given a signed-in super admin user
    And an organization exists
    When they POST /orgs/{org_id}/users with email "newadmin@company.com" and role "admin"
    Then the response status is 201
    And the response contains user_id, email, role, and password_reset_link
    And the user email is "newadmin@company.com"
    And the user role is "admin"
    And a Firebase user was created with email "newadmin@company.com"
    And a database user exists with email "newadmin@company.com" and role "admin"

  Scenario: Super admin adds member user to organization
    Given a signed-in super admin user
    And an organization exists
    When they POST /orgs/{org_id}/users with email "developer@company.com" and role "member"
    Then the response status is 201
    And the user email is "developer@company.com"
    And the user role is "member"
    And a Firebase user was created with email "developer@company.com"

  Scenario: Cannot create user with owner role
    Given a signed-in super admin user
    And an organization exists
    When they POST /orgs/{org_id}/users with email "fake-owner@company.com" and role "owner"
    Then the response status is 400
    And the error message contains "owner role"

  Scenario: Cannot create duplicate user
    Given a signed-in super admin user
    And an organization exists with an owner
    When they POST /orgs/{org_id}/users with the owner's email and role "admin"
    Then the response status is 400
    And the error message contains "already exists"

  Scenario: Organization admin cannot create users via super admin endpoint
    Given a signed-in organization user with role "admin"
    And an organization exists
    When they POST /orgs/{org_id}/users with email "test@company.com" and role "member"
    Then the response status is 403

  Scenario: Unauthenticated user cannot create organization users
    Given an unauthenticated user
    And an organization exists
    When they POST /orgs/{org_id}/users with email "test@company.com" and role "member"
    Then the response status is 401
