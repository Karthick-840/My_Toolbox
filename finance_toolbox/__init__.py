"""
Finance Toolbox - Comprehensive financial analysis toolkit.

Provides market data fetching, fundamental analysis, DCF valuation, portfolio analysis,
and comprehensive financial reporting capabilities.

Layers:
- Layer 0: Config, data models, shared utilities
- Layer 1: Market data APIs (yfinance, FMP)
- Layer 2: Analysis metrics (fundamentals, DCF, ratios, moats, risk)
- Layer 3: Composite workflows (portfolio, reports)

Linear dependency: my_toolbox → finance_toolbox (no reverse imports)
"""

from .config import Config
from .data_models import (
    TickerProfile,
    PriceSnapshot,
    FinancialStatement,
    AnalysisResult,
    DCFValuation,
    FinancialRatios,
    MoatScore,
    RiskMetrics,
    GrowthMetrics,
    ComprehensiveAnalysis,
    PortfolioHolding,
    PortfolioMetrics,
    to_dict,
)
from .market_data import YFinanceClient, YFinanceBatch

__version__ = "1.0.0"

__all__ = [
    # Configuration
    'Config',
    # Data models
    'TickerProfile',
    'PriceSnapshot',
    'FinancialStatement',
    'AnalysisResult',
    'DCFValuation',
    'FinancialRatios',
    'MoatScore',
    'RiskMetrics',
    'GrowthMetrics',
    'ComprehensiveAnalysis',
    'PortfolioHolding',
    'PortfolioMetrics',
    'to_dict',
    # Market data APIs
    'YFinanceClient',
    'YFinanceBatch',
]
