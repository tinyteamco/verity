import pytest
from pytest_bdd import scenarios, when, then, parsers


scenarios("../features/health_check.feature")


@pytest.fixture
def response_data():
    return {}


@when(parsers.parse("I GET {path}"))
def make_get_request(client, response_data, path):
    response = client.get(path)
    response_data["response"] = response
    response_data["json"] = response.json() if response.status_code == 200 else None


@then(parsers.parse("the response status is {status:d}"))
def check_status(response_data, status):
    assert response_data["response"].status_code == status


@then(parsers.parse('the response contains "{field}" as {value}'))
def check_field_value(response_data, field, value):
    json_data = response_data["json"]
    assert json_data is not None

    # Handle boolean values
    if value.lower() == "true":
        expected = True
    elif value.lower() == "false":
        expected = False
    else:
        # Remove quotes if present
        expected = value.strip('"')

    assert json_data[field] == expected