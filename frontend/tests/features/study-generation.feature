Feature: Automated Study Generation
  As an organization user
  I want to generate studies from research topics
  So I can quickly create interview guides

  Background:
    Given I am logged in as super admin "admin@tinyteam.co"
    And organization "Research Corp" exists

  Scenario: Generate study from topic
    When I navigate to organization "Research Corp" studies page
    And I click "Generate Study"
    And I enter "How do people shop in supermarkets?" as the topic
    And I submit the generation form
    Then I see a loading indicator
    And after generation completes, I see a new study with generated title
    And I see the interview guide content

  Scenario: Validation error for empty topic
    When I navigate to organization "Research Corp" studies page
    And I click "Generate Study"
    And I enter "" as the topic
    And I submit the generation form
    Then I see validation error "Topic is required"

  Scenario: Timeout error for slow generation
    When I navigate to organization "Research Corp" studies page
    And I click "Generate Study"
    And I enter "How do people shop in supermarkets?" as the topic
    And generation takes more than 60 seconds
    Then I see timeout error with retry option

  Scenario: Server error with retry option
    When I navigate to organization "Research Corp" studies page
    And I click "Generate Study"
    And I enter "How do people shop in supermarkets?" as the topic
    And the backend returns 500 error
    Then I see error message with "Retry" and "Create Manually" buttons

  Scenario: Edit interview guide
    Given organization "Research Corp" has a study with an interview guide
    When I navigate to the study detail page
    And I click "Edit Guide"
    And I modify the interview guide content
    And I click "Save"
    Then I see "Guide saved successfully"
    And the updated content is displayed

  Scenario: Preview markdown while editing
    Given organization "Research Corp" has a study with an interview guide
    When I navigate to the study detail page
    And I click "Edit Guide"
    And I toggle "Preview" mode
    Then I see rendered markdown

  Scenario: Warning before navigation with unsaved changes
    Given organization "Research Corp" has a study with an interview guide
    When I navigate to the study detail page
    And I click "Edit Guide"
    And I modify the interview guide content
    And I attempt to navigate away
    Then I see warning "You have unsaved changes"

  Scenario: Save empty guide content
    Given organization "Research Corp" has a study with an interview guide
    When I navigate to the study detail page
    And I click "Edit Guide"
    And I delete all content
    And I click "Save"
    Then I see "Guide saved successfully"

  Scenario: View study with interview guide
    Given organization "Research Corp" has a study with an interview guide
    When I navigate to the study detail page
    Then I see study title and description
    And I see interview guide rendered with sections and questions

  Scenario: View study without interview guide
    Given organization "Research Corp" has a study without an interview guide
    When I navigate to the study detail page
    Then I see "No interview guide yet"
    And I see "Add Guide" or "Generate Guide" button

  Scenario: Create study manually
    When I navigate to organization "Research Corp" studies page
    And I click "Create Study Manually"
    And I enter "Manual Study" as the study title
    And I enter "Testing manual creation" as the study description
    And I submit the study form
    Then I see "Manual Study" in the studies list
    And the study has no interview guide
