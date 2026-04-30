import os
import types

import pandas as pd

import my_toolbox.finance_tools as finance_tools


def test_init_requires_yfinance(monkeypatch):
    monkeypatch.setattr(finance_tools, "HAS_YFINANCE", False)
    try:
        finance_tools.FinanceTools()
        assert False, "Expected ImportError"
    except ImportError:
        pass


def test_include_stamp_duty():
    assert finance_tools.FinanceTools.include_stamp_duty(1000, "2020-06-30") == 1000
    assert finance_tools.FinanceTools.include_stamp_duty(1000, "2020-07-02") == 999.95


def test_fetch_ticker_data_sip(monkeypatch, dummy_logger):
    monkeypatch.setattr(finance_tools, "HAS_YFINANCE", True)

    class FakeTicker:
        info = {"name": "x"}

        def __init__(self, _ticker):
            pass

        def history(self, period="max"):
            return pd.DataFrame(
                {
                    "Date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                    "Open": [1, 2],
                    "High": [1, 2],
                    "Low": [1, 2],
                    "Close": [10, 11],
                    "Volume": [100, 200],
                    "Dividends": [0, 0],
                    "Stock Splits": [0, 0],
                }
            )

    monkeypatch.setattr(finance_tools.time, "sleep", lambda *_: None)
    monkeypatch.setattr(
        finance_tools,
        "yf",
        types.SimpleNamespace(Ticker=FakeTicker),
        raising=False,
    )

    ft = finance_tools.FinanceTools(dummy_logger)
    row = pd.Series(
        {
            "Yahoo_Ticker": "ABC",
            "min_start": "2024-01-01",
            "max_end": "2024-01-31",
        }
    )
    out = ft.fetch_ticker_data(row, data_type="SIP")
    assert out["Yahoo_Ticker"] == "ABC"
    assert isinstance(out["prices"], list)
    assert "Open" not in out["prices"][0]


def test_get_yfinance_info_writes_outputs(monkeypatch, tmp_path, dummy_logger):
    monkeypatch.setattr(finance_tools, "HAS_YFINANCE", True)
    ft = finance_tools.FinanceTools(dummy_logger)

    def fake_fetch(row, data_type, save_path):
        if row["Yahoo_Ticker"] == "OK":
            return {"Yahoo_Ticker": "OK", "prices": [{"Date": "2024-01-01"}], "info": {}}
        return {"Yahoo_Ticker": "BAD"}

    monkeypatch.setattr(ft, "fetch_ticker_data", fake_fetch)

    inp = pd.DataFrame(
        [
            {"Yahoo_Ticker": "OK", "min_start": "2024-01-01", "max_end": "2024-01-02", "Security_Status": "Active"},
            {"Yahoo_Ticker": "BAD", "min_start": "2024-01-01", "max_end": "2024-01-02", "Security_Status": "Active"},
        ]
    )
    out = ft.get_yfinance_info(inp, data_type="SIP", save_path=str(tmp_path), process="get_history")
    assert len(out) == 1
    assert os.path.exists(tmp_path / "New_SIP_Info.json")
    assert os.path.exists(tmp_path / "Unavailable_securities_SIP.json")
