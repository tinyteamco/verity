Feature: Upload audio and finalize transcript

  Scenario: Upload audio to an interview

    Given an interview exists for an interviewee

    When they POST /recordings:upload with a small WAV file

    Then the response status is 201

    And the recording is stored in object storage

    And the recording metadata is persisted



  Scenario: Finalize single-segment transcript

    Given a recording exists

    When they POST /interviews/{interview_id}/transcript:finalize with one segment

    Then the response status is 201

    And the transcript is persisted and linked to the interview

