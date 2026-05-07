"""
Configuration for finance_toolbox.

Centralized settings for API keys, rate limits, DCF defaults, and analysis thresholds.
"""

import os
from typing import Optional


class Config:
    """Finance toolbox configuration."""
    
    # ===== API KEYS & ENDPOINTS =====
    YFINANCE_API_KEY = os.getenv('YFINANCE_API_KEY', None)  # yfinance doesn't require key; added for future use
    FMP_API_KEY = os.getenv('FMP_API_KEY', None)
    YFINANCE_TIMEOUT = 10  # seconds
    FMP_TIMEOUT = 10  # seconds
    
    # ===== RATE LIMITING =====
    YFINANCE_REQUESTS_PER_MINUTE = 120  # yfinance typical limit
    FMP_REQUESTS_PER_MINUTE = 250  # FMP free tier limit (25 calls/min, premium varies)
    
    # ===== RETRY POLICY =====
    RETRY_MAX_ATTEMPTS = 3
    RETRY_INITIAL_DELAY = 1.0  # seconds
    RETRY_MAX_DELAY = 32.0  # seconds
    RETRY_MULTIPLIER = 2.0
    RETRY_JITTER = True
    
    # ===== CIRCUIT BREAKER =====
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60.0  # seconds
    
    # ===== CACHING =====
    CACHE_ENABLED = True
    CACHE_TTL_MARKET_DATA = 3600  # 1 hour for price data
    CACHE_TTL_FUNDAMENTAL_DATA = 86400  # 1 day for fundamental data
    CACHE_TTL_ANALYST_ESTIMATES = 604800  # 1 week for analyst estimates
    CACHE_MAX_SIZE_MB = 100  # Max cache size in MB
    
    # ===== DCF VALUATION DEFAULTS =====
    DCF_DISCOUNT_RATE = 0.10  # 10% WACC default
    DCF_TERMINAL_GROWTH_RATE = 0.025  # 2.5% perpetual growth
    DCF_FREE_CASH_FLOW_YEARS = 5  # Project 5 years
    DCF_MARGIN_OF_SAFETY = 0.25  # 25% discount to intrinsic value for safety
    
    # ===== FINANCIAL METRICS THRESHOLDS =====
    MIN_REVENUE_FOR_ANALYSIS = 1_000_000  # $1M minimum market cap
    MIN_HISTORICAL_YEARS = 3  # Need 3 years of history for trend analysis
    DEBT_TO_EQUITY_WARNING = 2.0  # Alert if D/E > 2
    ROE_BENCHMARK = 0.15  # 15% ROE is good
    
    # ===== BUSINESS MOAT SCORING =====
    MOAT_ROE_THRESHOLD = 0.15  # ROE > 15% indicates moat strength
    MOAT_MARGIN_THRESHOLD = 0.20  # Gross margin > 20% indicates pricing power
    MOAT_SCORE_MAX = 100  # Moat score 0-100
    
    # ===== PORTFOLIO ANALYSIS =====
    PORTFOLIO_MAX_CORRELATION_WARNING = 0.8  # Alert if correlation > 80%
    PORTFOLIO_MAX_SECTOR_CONCENTRATION = 0.40  # Alert if single sector > 40%
    PORTFOLIO_DIVERSIFICATION_TARGET = 0.60  # Aim for 60% diversification score
    
    # ===== LOGGING =====
    LOG_LEVEL = os.getenv('FINANCE_TOOLBOX_LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('FINANCE_TOOLBOX_LOG_FILE', None)  # If None, logs to console only
    ENABLE_STRUCTURED_LOGGING = os.getenv('FINANCE_TOOLBOX_STRUCTURED_LOGS', 'false').lower() == 'true'
    ENABLE_METRICS_LOGGING = True
    
    # ===== DATA VALIDATION =====
    ALLOW_NEGATIVE_REVENUE = False
    ALLOW_MISSING_DATES = False
    VALIDATE_CONSISTENCY = True  # Revenue, COGS, can't exceed each other
    
    @classmethod
    def validate(cls) -> None:
        """Validate critical configuration."""
        if not cls.FMP_API_KEY:
            print("⚠️  Warning: FMP_API_KEY not set. FMP integration will fail.")
        
        if cls.DCF_DISCOUNT_RATE <= 0:
            raise ValueError("DCF_DISCOUNT_RATE must be positive")
        
        if cls.CACHE_MAX_SIZE_MB <= 0:
            raise ValueError("CACHE_MAX_SIZE_MB must be positive")

    @classmethod
    def to_dict(cls) -> dict:
        """Export configuration as dictionary."""
        return {k: getattr(cls, k) for k in dir(cls) if not k.startswith('_') and k.isupper()}
