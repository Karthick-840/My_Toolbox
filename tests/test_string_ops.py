import pandas as pd

from my_toolbox.string_ops import String_Functions


def test_convert_frequency_defaults_and_known(dummy_logger):
    s = String_Functions(dummy_logger)
    assert s.convert_frequency("monthly") == 12
    assert s.convert_frequency("quarterly") == 4
    assert s.convert_frequency("unknown") == 12


def test_string_2_num_and_number_to_string(dummy_logger):
    s = String_Functions(dummy_logger)
    assert s.string_2_num("$1,234.50") == 1234.50
    assert s.string_2_num("abc") == "abc"
    assert s.number_to_string(10) == "10"
    assert s.number_to_string("x") == ""


def test_summarize(dummy_logger):
    s = String_Functions(dummy_logger)
    df = pd.DataFrame(
        {
            "grp": ["A", "A", "B"],
            "x": [1, 2, 3],
            "y": ["m", "m", "n"],
        }
    )
    out = s.summarize(df, "grp", {"x": "mean", "y": "mode"})
    assert set(out.columns) == {"grp", "x", "y"}
    assert out.loc[out["grp"] == "A", "x"].iloc[0] == 1.5
