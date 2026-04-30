import pandas as pd

from my_toolbox.time_ops import Date_Manipulations


def test_update_and_convert_dates(dummy_logger):
    d = Date_Manipulations(dummy_logger)
    assert isinstance(d.update_end_date("TILL"), str)
    assert d.update_end_date("2024-01-01") == "2024-01-01"
    assert d.convert_to_standard_date("2024-05-06") == "2024-05-06"
    assert d.convert_to_standard_date("06-May-24") == "2024-05-06"


def test_datetime_helpers(dummy_logger):
    d = Date_Manipulations(dummy_logger)
    dt = d.string_to_datetime("2024-01-01")
    assert dt is not None
    assert d.datetime_to_string("2024-01-01") == "2024-01-01"
    assert d.datetime_to_string("bad-date") is None


def test_business_day_and_date_generator(dummy_logger):
    d = Date_Manipulations(dummy_logger)
    # Saturday -> Monday
    assert d.get_next_business_day("2024-05-04") == "2024-05-06"
    generated = d.date_generator("2024-01-15", "2024-03-15", delay=0)
    assert len(generated) >= 2


def test_merge_closest_date_by_scheme(dummy_logger):
    d = Date_Manipulations(dummy_logger)
    no_nav = pd.DataFrame(
        {
            "scheme": ["A", "A", "B"],
            "date": pd.to_datetime(["2024-01-10", "2024-01-20", "2024-01-15"]),
        }
    )
    nav = pd.DataFrame(
        {
            "scheme": ["A", "A", "B"],
            "date": pd.to_datetime(["2024-01-11", "2024-01-21", "2024-01-14"]),
            "nav": [10.0, 11.0, 20.0],
        }
    )
    out = d.merge_schemes_on_closest_date(no_nav, nav)
    assert "nav" in out.columns
    assert len(out) == 3
