Feature: API Health Check
  As a developer or monitoring system
  I want to check if the API is healthy
  So that I know the service is running

  Scenario: Service is healthy
    When I GET /health
    Then the response status is 200
    And the response contains "healthy" as true
    And the response contains "service" as "verity-backend"
    And the response contains "version" as "0.1.0"