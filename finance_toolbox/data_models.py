"""
Data models for finance_toolbox.

Strongly-typed dataclasses for market data, financial statements, and analysis results.
Ensures consistent data flow across modules and enables serialization.
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class TickerProfile:
    """Basic ticker/company metadata."""
    symbol: str
    isin: Optional[str] = None
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    employees: Optional[int] = None
    exchange: Optional[str] = None
    currency: Optional[str] = 'USD'
    description: Optional[str] = None
    website: Optional[str] = None
    

@dataclass
class PriceSnapshot:
    """Point-in-time stock price and volume data."""
    symbol: str
    date: str  # YYYY-MM-DD format
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None
    

@dataclass
class FinancialStatement:
    """Financial statement (income, balance sheet, cash flow)."""
    symbol: str
    period: str  # e.g., "2023-Q1", "2023-FY", "Q1", "FY"
    date: str  # YYYY-MM-DD (quarter/year end date)
    statement_type: str  # "income", "balance_sheet", "cash_flow"
    
    # Income Statement
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expenses: Optional[float] = None
    operating_income: Optional[float] = None
    interest_expense: Optional[float] = None
    income_before_tax: Optional[float] = None
    income_tax: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None
    
    # Balance Sheet
    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    cash: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    total_liabilities: Optional[float] = None
    current_liabilities: Optional[float] = None
    long_term_debt: Optional[float] = None
    shareholders_equity: Optional[float] = None
    
    # Cash Flow
    operating_cash_flow: Optional[float] = None
    capital_expenditure: Optional[float] = None
    free_cash_flow: Optional[float] = None
    financing_activities: Optional[float] = None
    

@dataclass
class AnalysisResult:
    """Base class for analysis results."""
    symbol: str
    analyzed_at: str  # ISO format timestamp
    data_source: str  # e.g., "yfinance", "fmp", "combined"
    

@dataclass
class DCFValuation(AnalysisResult):
    """DCF-based intrinsic valuation."""
    intrinsic_value: float
    fair_value: float  # With margin of safety
    margin_of_safety: float  # Discount % applied
    current_price: float
    upside_downside: float  # % difference
    fcf_current: Optional[float] = None
    fcf_growth_rate: Optional[float] = None
    terminal_value: Optional[float] = None
    discount_rate: Optional[float] = None
    terminal_growth: Optional[float] = None
    confidence: float = 0.5  # 0-1 scale
    

@dataclass
class FinancialRatios(AnalysisResult):
    """Fundamental financial ratios."""
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    roe: Optional[float] = None  # Return on equity
    roa: Optional[float] = None  # Return on assets
    roic: Optional[float] = None  # Return on invested capital
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    fcf_per_share: Optional[float] = None
    fcf_yield: Optional[float] = None
    

@dataclass
class MoatScore(AnalysisResult):
    """Competitive advantage (moat) scoring."""
    overall_score: float  # 0-100
    brand_score: float  # 0-100
    cost_advantage_score: float  # 0-100
    switching_cost_score: float  # 0-100
    network_effect_score: float  # 0-100
    scale_score: float  # 0-100
    explanation: str = ""
    recommendation: str = ""  # "STRONG_MOAT", "WEAK_MOAT", "NO_MOAT"
    

@dataclass
class RiskMetrics(AnalysisResult):
    """Risk assessment metrics."""
    beta: Optional[float] = None  # Market risk (Beta)
    volatility_1y: Optional[float] = None  # 1-year volatility
    volatility_5y: Optional[float] = None  # 5-year volatility
    max_drawdown: Optional[float] = None  # Largest peak-to-trough decline
    debt_risk_score: float = 0.5  # 0-1, higher = more risky
    revenue_risk_score: float = 0.5  # Consistency of revenue
    concentration_risk_score: float = 0.5  # Customer/product concentration
    business_risk_category: str = "MEDIUM"  # "LOW", "MEDIUM", "HIGH"
    

@dataclass
class GrowthMetrics(AnalysisResult):
    """Historical and projected growth metrics."""
    revenue_cagr_3y: Optional[float] = None
    revenue_cagr_5y: Optional[float] = None
    eps_cagr_3y: Optional[float] = None
    eps_cagr_5y: Optional[float] = None
    fcf_cagr_3y: Optional[float] = None
    revenue_yoy: Optional[float] = None  # Most recent year-over-year
    eps_yoy: Optional[float] = None
    projected_eps_growth: Optional[float] = None  # Analyst consensus
    growth_quality: str = "MODERATE"  # "LOW", "MODERATE", "HIGH"
    

@dataclass
class ComprehensiveAnalysis(AnalysisResult):
    """Complete fundamental analysis for a ticker."""
    profile: Optional[TickerProfile] = None
    latest_price: Optional[PriceSnapshot] = None
    valuation: Optional[DCFValuation] = None
    ratios: Optional[FinancialRatios] = None
    moat: Optional[MoatScore] = None
    risk: Optional[RiskMetrics] = None
    growth: Optional[GrowthMetrics] = None
    recommendation: str = "HOLD"  # "BUY", "HOLD", "SELL"
    recommendation_score: float = 0.5  # 0-1, higher = stronger buy
    

@dataclass
class PortfolioHolding:
    """Single holding in a portfolio."""
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    sector: Optional[str] = None
    analysis: Optional[ComprehensiveAnalysis] = None
    
    def market_value(self) -> float:
        """Total market value of position."""
        return self.quantity * self.current_price
    
    def unrealized_gain(self) -> float:
        """Unrealized gain/loss in dollars."""
        return self.market_value() - (self.quantity * self.avg_cost)


@dataclass
class PortfolioMetrics:
    """Aggregate portfolio-level metrics."""
    total_value: float
    total_cost: float
    total_unrealized_gain: float
    allocation: Dict[str, float]  # sector/ticker -> % allocation
    sector_concentration: Dict[str, float]  # sector -> % of portfolio
    correlation_matrix: Optional[List[List[float]]] = None
    diversification_score: float = 0.5  # 0-1, higher = better diversified
    portfolio_beta: Optional[float] = None
    portfolio_volatility: Optional[float] = None
    max_drawdown: Optional[float] = None


def to_dict(obj: Any) -> dict:
    """Convert dataclass to dictionary."""
    if hasattr(obj, '__dataclass_fields__'):
        return asdict(obj)
    return obj
