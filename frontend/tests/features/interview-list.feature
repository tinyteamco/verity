Feature: Interview List and Detail Views

  As a researcher
  I want to view completed interviews with their transcripts and recordings
  So that I can analyze participant responses

  Background:
    Given I am signed in as an organization owner
    And I have a study with completed interviews

  Scenario: Researcher views interview list with completion status
    When I navigate to the interviews page for my study
    Then I see a list of completed interviews
    And each interview shows its completion date
    And each interview shows transcript and recording availability

  Scenario: Researcher views interview list with external participant IDs
    Given I have interviews from recruitment platforms
    When I navigate to the interviews page
    Then I see the external participant ID for platform-sourced interviews
    And I see the platform source (e.g., "prolific", "respondent")

  Scenario: Researcher views transcript inline in interview detail
    Given I have a completed interview with a transcript
    When I click on the interview from the list
    Then I see the interview detail page
    And I see the transcript displayed inline
    And the transcript text is readable and formatted

  Scenario: Researcher downloads audio file from interview
    Given I have a completed interview with a recording
    When I navigate to the interview detail page
    And I click the "Download Audio" button
    Then the audio file download begins
    And I receive the audio file in WAV format

  Scenario: Interview list shows empty state when no interviews exist
    Given I have a study with no completed interviews
    When I navigate to the interviews page
    Then I see a message indicating no interviews have been completed yet

  Scenario: Interview list handles missing artifacts gracefully
    Given I have a completed interview without a transcript
    When I view the interview list
    Then the transcript availability is marked as unavailable
    And I cannot click to view the missing transcript
