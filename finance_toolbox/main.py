# main.py
import pandas as pd
from modules import dcf, cashflow, leverage, growth, moat, risk

def process_stock(stock_df):
    """
    stock_df: DataFrame containing historical quarterly data for 1 stock
    """
    fcf_series = stock_df['fcf']
    eps_series = stock_df['eps']
    roe_series = stock_df['roe']
    gross_margin_series = stock_df['gross_margin']
    debt_series = stock_df['debt_to_equity']
    market_price = stock_df['market_price'].iloc[-1]

    intrinsic_val = dcf.compute_dcf(list(fcf_series), discount_rate=0.1, terminal_growth_rate=0.02)
    mos = risk.margin_of_safety(intrinsic_val, market_price)
    fcf_score = cashflow.fcf_stability(fcf_series)
    earnings_score = cashflow.earnings_sustainability(eps_series)
    leverage_score = leverage.debt_safety_score(debt_series)
    moat_score_val = moat.moat_score(roe_series, wacc=0.08, gross_margin_series=gross_margin_series)
    cag = growth.cagr(eps_series)
    risk_adj = risk.risk_adjusted_growth(cag, beta=1.1)  # beta example

    result = {
        "intrinsic_value": intrinsic_val,
        "margin_of_safety": mos,
        "fcf_stability": fcf_score,
        "earnings_sustainability": earnings_score,
        "leverage_score": leverage_score,
        "moat_score": moat_score_val,
        "risk_adjusted_growth": risk_adj
    }
    return pd.DataFrame([result])
