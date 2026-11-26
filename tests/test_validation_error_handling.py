from my_toolbox.error_handling import APIError, RateLimitError, RetryExhaustedError, ValidationError
from my_toolbox.validation import Validator, validate_email, validate_json_schema, validate_url


def test_validation_basics():
    assert validate_email("user@example.com")[0] is True
    assert validate_email("bad-email")[0] is False

    assert validate_url("https://example.com", require_https=True)[0] is True
    assert validate_url("http://example.com", require_https=True)[0] is False

    assert Validator.validate_ticker("AAPL")[0] is True
    assert Validator.validate_currency_code("USD")[0] is True
    assert Validator.validate_currency_code("US")[0] is False


def test_json_schema_validation():
    schema = {
        "name": {"type": "str", "required": True, "min_length": 2},
        "age": {"type": "int", "required": True},
        "role": {"type": "str", "enum": ["admin", "user"]},
    }

    ok_data = {"name": "Alice", "age": 30, "role": "admin"}
    bad_data = {"name": "A", "age": "30", "role": "guest"}

    assert validate_json_schema(ok_data, schema)[0] is True
    valid, errors = validate_json_schema(bad_data, schema)
    assert valid is False
    assert len(errors) >= 2


def test_error_classes_render_messages():
    ve = ValidationError("invalid value", field="price")
    assert "price" in str(ve)

    api_err = APIError("server down", status_code=503)
    assert "503" in str(api_err)

    rate = RateLimitError(retry_after=10)
    assert rate.status_code == 429

    exhausted = RetryExhaustedError("failed", attempts=3)
    assert "3 attempts" in str(exhausted)
