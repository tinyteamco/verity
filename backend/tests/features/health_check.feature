Feature: API Health Check
  As a developer or monitoring system
  I want to check if the API is healthy
  So that I know the service is running

  Scenario: Service health check returns status
    When I GET /health
    Then the response status is 200
    And the response contains "service" as "verity-backend"
    And the response contains "version" as "0.1.0"
    And the response contains database status information

  Scenario: Service is healthy in test environment
    When I GET /health
    Then the response status is 200
    And the response contains "healthy" as true
    And the database status is connected

  # Note: Database disconnection scenarios would be tested in production/staging
  # where actual PostgreSQL connection failures could occur. In test environment,
  # SQLite is always available via dependency injection.