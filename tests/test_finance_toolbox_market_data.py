import types

import pandas as pd

import finance_toolbox.market_data as market_data


class _FakeTicker:
    def __init__(self, _symbol):
        self.info = {
            "isin": "US000000",
            "longName": "Acme Corp",
            "sector": "Tech",
            "currency": "USD",
        }

    def history(self, period=None, start=None, end=None):
        idx = pd.to_datetime(["2026-01-01", "2026-01-02"])
        return pd.DataFrame(
            {
                "Open": [10.0, 11.0],
                "High": [12.0, 13.0],
                "Low": [9.0, 10.0],
                "Close": [11.0, 12.0],
                "Adj Close": [11.0, 12.0],
                "Volume": [100, 200],
            },
            index=idx,
        )

    @property
    def income_stmt(self):
        return pd.DataFrame({"a": [1]})

    @property
    def balance_sheet(self):
        return pd.DataFrame({"a": [1]})

    @property
    def cash_flow(self):
        return pd.DataFrame({"a": [1]})


class _NoopRateLimiter:
    def __init__(self, _rpm):
        pass

    def wait(self):
        return None


class _NoopBreaker:
    def __init__(self, *args, **kwargs):
        pass

    def call(self, fn, *args, **kwargs):
        return fn(*args, **kwargs)


def test_yfinance_client_profile_and_price(monkeypatch):
    monkeypatch.setattr(market_data, "HAS_YFINANCE", True)
    monkeypatch.setattr(market_data, "yf", types.SimpleNamespace(Ticker=_FakeTicker), raising=False)
    monkeypatch.setattr(market_data, "RateLimiter", _NoopRateLimiter)
    monkeypatch.setattr(market_data, "CircuitBreaker", _NoopBreaker)

    client = market_data.YFinanceClient()
    profile = client.get_profile("AAPL")
    price = client.get_price_today("AAPL")

    assert profile is not None
    assert profile.name == "Acme Corp"
    assert price is not None
    assert price.close == 12.0


def test_yfinance_batch_fetch(monkeypatch):
    monkeypatch.setattr(market_data, "HAS_YFINANCE", True)
    monkeypatch.setattr(market_data, "yf", types.SimpleNamespace(Ticker=_FakeTicker), raising=False)
    monkeypatch.setattr(market_data, "RateLimiter", _NoopRateLimiter)
    monkeypatch.setattr(market_data, "CircuitBreaker", _NoopBreaker)

    batch = market_data.YFinanceBatch(max_workers=2)
    out = batch.fetch_profiles(["AAPL", "MSFT"])

    assert set(out.keys()) == {"AAPL", "MSFT"}
    assert all(v is not None for v in out.values())
