import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from tests.test_helpers import get_auth_headers

# Load scenarios from the feature file
scenarios("../features/create_organization.feature")


@pytest.fixture
def response():
    return {}


@pytest.fixture
def auth_context():
    return {}


# Step definitions
@given("I am authenticated as a super admin in the organization tenant")
def super_admin_auth(super_admin_token, auth_context):
    auth_context["headers"] = get_auth_headers(super_admin_token)


@given("I am authenticated as a regular organization user")
def regular_user_auth(org_user_token, auth_context):
    auth_context["headers"] = get_auth_headers(org_user_token)


@given("I am authenticated as an interviewee")
def interviewee_auth(interviewee_token, auth_context):
    auth_context["headers"] = get_auth_headers(interviewee_token)


@when(parsers.parse('I POST /orgs with name "{org_name}"'))
def post_create_org(client, response, auth_context, org_name):
    headers = auth_context.get("headers", {})
    response["result"] = client.post("/orgs", json={"name": org_name}, headers=headers)


@when(parsers.parse('an unauthenticated user POST /orgs with name "{org_name}"'))
def post_create_org_unauth(client, response, org_name):
    response["result"] = client.post("/orgs", json={"name": org_name})


@then(parsers.parse("the response status is {status_code:d}"))
def check_status_code(response, status_code):
    if response["result"].status_code != status_code:
        print(f"Expected {status_code}, got {response['result'].status_code}")
        print(f"Response: {response['result'].text}")
    assert response["result"].status_code == status_code


@then("the response has an org_id")
def check_org_id(response):
    data = response["result"].json()
    assert "org_id" in data
    assert data["org_id"] is not None


@then(parsers.parse('a new organization exists in the database with name "{org_name}"'))
def check_org_exists(response, org_name):
    data = response["result"].json()
    assert data["name"] == org_name
