Feature: Share link onboarding

  Background:

    Given a study with an active share link



  Scenario: Visitor can view landing

    Given an unauthenticated visitor

    When they visit GET /share/join?token=<valid>

    Then they see the study landing



  Scenario: Authenticated interviewee creates interview from link

    Given a signed-in interviewee

    When they POST /share/join/resolve with token <valid>

    Then the response status is 201

    And an Interview is created for the interviewee and study

