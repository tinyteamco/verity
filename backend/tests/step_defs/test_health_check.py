import pytest
from pytest_bdd import parsers, scenarios, then, when

scenarios("../features/health_check.feature")


@pytest.fixture
def response_data():
    return {}


# Database connectivity scenarios are environment-dependent:
# - Test environment: SQLite always available via dependency injection
# - Production: PostgreSQL connectivity can fail and should be monitored


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


@then("the response contains database status information")
def check_database_status_exists(response_data):
    """Check that database status information is present"""
    json_data = response_data["json"]
    assert json_data is not None
    assert "database" in json_data
    assert "connected" in json_data["database"]


@then("the database status is connected")
def check_database_connected(response_data):
    """Check that database status shows connected"""
    json_data = response_data["json"]
    assert json_data["database"]["connected"] is True
    assert json_data["database"].get("error") is None


# Note: "database not connected" scenarios would be tested in production/staging
# where actual PostgreSQL connection failures could occur
