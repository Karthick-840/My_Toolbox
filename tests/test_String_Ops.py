import pytest
import pandas as pd
from My_Toolbox.String_Ops import String_Functions  # Replace 'your_module' with the actual module name

@pytest.fixture
def string_functions():
    return String_Functions()

def test_convert_frequency(string_functions):
    assert string_functions.convert_frequency("monthly") == 12
    assert string_functions.convert_frequency("quarterly") == 4
    assert string_functions.convert_frequency("yearly") == 12  # Default value when frequency is not found
    assert string_functions.convert_frequency("MONTHLY") == 12  # Check case insensitivity

def test_string_2_num(string_functions):
    assert string_functions.string_2_num("1,234.56") == 1234.56
    assert string_functions.string_2_num("1234") == 1234.0
    assert string_functions.string_2_num("$1,234.56") == 1234.56  # Check with special characters
    assert string_functions.string_2_num("abc") == "abc"  # Non-numeric string should return the original text
    assert string_functions.string_2_num(None) == None  # None should be handled without errors

def test_number_to_string(string_functions):
    assert string_functions.number_to_string(1234.56) == "1234.56"
    assert string_functions.number_to_string(1234) == "1234"
    assert string_functions.number_to_string("not a number") == ""
    assert string_functions.number_to_string(None) == ""

def test_summarize(string_functions):
    # Test data for summarization
    data = {
        "group": ["A", "A", "B", "B", "C", "C", "C"],
        "value": [10, 20, 30, 30, 40, 50, 50],
        "amount": [5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5]
    }
    df = pd.DataFrame(data)

    # Define aggregation rules
    aggregate_dicts = {"value": "mode", "amount": "mean"}

    # Call summarize and check results
    result = string_functions.summarize(df, "group", aggregate_dicts)
    
    # Expected values for the test dataset
    expected_data = {
        "group": ["A", "B", "C"],
        "value": [10, 30, 50],  # Mode for each group
        "amount": [6.0, 8.0, 10.5]  # Mean rounded to 2 decimals
    }
    expected_df = pd.DataFrame(expected_data)

    # Validate that the result matches the expected DataFrame
    pd.testing.assert_frame_equal(result, expected_df)
