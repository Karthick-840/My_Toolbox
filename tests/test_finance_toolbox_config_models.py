from finance_toolbox.config import Config
from finance_toolbox.data_models import (
    DCFValuation,
    PortfolioHolding,
    PriceSnapshot,
    TickerProfile,
    to_dict,
)


def test_config_to_dict_and_validate():
    cfg = Config.to_dict()
    assert "DCF_DISCOUNT_RATE" in cfg
    assert cfg["DCF_DISCOUNT_RATE"] > 0
    Config.validate()


def test_data_models_and_helpers():
    profile = TickerProfile(symbol="AAPL", name="Apple", sector="Technology")
    assert profile.symbol == "AAPL"

    snap = PriceSnapshot(
        symbol="AAPL",
        date="2026-01-01",
        open=100.0,
        high=110.0,
        low=95.0,
        close=105.0,
        volume=1_000_000,
    )
    assert snap.close == 105.0

    dcf = DCFValuation(
        symbol="AAPL",
        analyzed_at="2026-01-01T00:00:00Z",
        data_source="test",
        intrinsic_value=200.0,
        fair_value=150.0,
        margin_of_safety=0.25,
        current_price=105.0,
        upside_downside=0.90,
    )
    assert dcf.margin_of_safety == 0.25

    holding = PortfolioHolding(symbol="AAPL", quantity=10, avg_cost=90, current_price=105)
    assert holding.market_value() == 1050
    assert holding.unrealized_gain() == 150

    as_dict = to_dict(profile)
    assert as_dict["symbol"] == "AAPL"
