# test_date_manipulations.py
import pytest
import pandas as pd
from datetime import datetime
from My_Toolbox.Time_Ops import Date_Manipulations

@pytest.fixture
def date_manipulator():
    """Fixture to initialize Date_Manipulations instance."""
    return Date_Manipulations()

def test_update_end_date(date_manipulator):
    # Test with "TILL" input
    assert date_manipulator.update_end_date("TILL") == datetime.today().strftime('%Y-%m-%d')
    
    # Test with other string
    assert date_manipulator.update_end_date("2023-01-01") == "2023-01-01"

def test_convert_to_standard_date(date_manipulator):
    # Test with valid date in YYYY-MM-DD format
    assert date_manipulator.convert_to_standard_date("2023-01-01") == "2023-01-01"
    
    # Test with valid date in DD-MMM-YY format
    assert date_manipulator.convert_to_standard_date("6-May-20") == "2020-05-06"
    
    # Test with invalid date format
    with pytest.raises(ValueError):
        date_manipulator.convert_to_standard_date("01-2023-01")

def test_string_to_datetime(date_manipulator):
    # Test with valid date string
    assert date_manipulator.string_to_datetime("2023-01-01") == pd.to_datetime("2023-01-01")
    
    # Test with invalid date format
    assert date_manipulator.string_to_datetime("not-a-date") is None

def test_datetime_to_string(date_manipulator):
    # Test with valid date string
    assert date_manipulator.datetime_to_string("2023-01-01") == "2023-01-01"
    
    # Test with invalid date string
    assert date_manipulator.datetime_to_string("not-a-date") is None

def test_get_next_business_day(date_manipulator):
    # Test with a weekday (should return the same date)
    weekday_date = "2023-06-14"  # Assume June 14, 2023, is a weekday (Wednesday)
    assert date_manipulator.get_next_business_day(weekday_date) == "2023-06-14"
    
    # Test with a weekend date (Saturday)
    weekend_date = "2023-06-17"  # Assume June 17, 2023, is a Saturday
    assert date_manipulator.get_next_business_day(weekend_date) == "2023-06-19"  # Should return Monday, June 19


def test_date_generator(date_manipulator):
    # Generate a simple date range and validate format
    dates = date_manipulator.date_generator("2023-01-01", "2023-06-01")
    assert isinstance(dates, list)
    assert all(isinstance(d, str) for d in dates)
    assert all(len(d) == 10 for d in dates)  # Expect 'YYYY-MM-DD' format

def test_find_closest_date(date_manipulator):
    # Prepare mock data
    nav_data = pd.DataFrame({
        "scheme": ["A", "A", "A"],
        "date": pd.to_datetime(["2023-01-01", "2023-01-05", "2023-01-10"]),
        "nav": [10, 12, 15]
    })
    row = {"scheme": "A", "date": "2023-01-04"}
    
    # Test for finding the closest date
    closest_date, closest_nav = date_manipulator.find_closest_date(row, nav_data)
    assert closest_date == pd.to_datetime("2023-01-05")
    assert closest_nav == 12



def test_merge_on_closest_date(date_manipulator):
    # Prepare mock data
    no_nav_df = pd.DataFrame({
        "date": pd.to_datetime(["2023-01-04", "2023-01-06"]),
        "value": [100, 200]
    })
    nav_history = pd.DataFrame({
        "date": pd.to_datetime(["2023-01-01", "2023-01-05", "2023-01-10"]),
        "nav": [10, 12, 15]
    })
    
    # Perform merge
    merged_df = date_manipulator.merge_on_closest_date(no_nav_df, nav_history)
    
    # Check the merged data
    assert len(merged_df) == len(no_nav_df)
    assert "nav" in merged_df.columns

def test_merge_schemes_on_closest_date(date_manipulator):
    # Prepare mock data for 'no_nav_df' and 'nav_history' with required columns
    no_nav_df = pd.DataFrame({
        "scheme": ["A", "A", "B"],
        "date": ["2023-01-04", "2023-01-06", "2023-01-08"],
        "value": [100, 200, 300]
    })
    nav_history = pd.DataFrame({
        "scheme": ["A", "A", "B", "B"],
        "date": ["2023-01-01", "2023-01-05", "2023-01-10", "2023-01-07"],
        "nav": [10, 12, 15, 20]
    })

    # Convert 'date' columns to datetime format for consistency
    no_nav_df["date"] = pd.to_datetime(no_nav_df["date"])
    nav_history["date"] = pd.to_datetime(nav_history["date"])

    # Perform the merge operation
    merged_df = date_manipulator.merge_schemes_on_closest_date(no_nav_df, nav_history)

    # Assertions to check the output
    assert len(merged_df) == len(no_nav_df)
    assert "nav" in merged_df.columns  # Check if 'nav' column is present in merged output
    assert "scheme_x" in merged_df.columns and "scheme_y" in merged_df.columns  # Ensure both scheme columns are present
    assert merged_df['scheme_x'].isin(["A", "B"]).all()  # Verify the schemes in the no_nav_df
    assert merged_df['scheme_y'].isin(["A", "B"]).all()  # Verify the schemes in the nav_history
