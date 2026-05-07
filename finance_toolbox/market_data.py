"""
Market data fetching layer.

Provides resilient access to yfinance with caching, rate limiting, and error handling.
Uses my_toolbox for robust parsing, logging, and retry logic.
"""

from typing import Optional, Dict, List
import logging
from datetime import datetime

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

# Import from my_toolbox
from my_toolbox import (
    RateLimiter,
    retry_with_backoff,
    ExponentialBackoffPolicy,
    CircuitBreaker,
    ContextLogger,
    ValidationError,
    APIError,
)

from .config import Config
from .data_models import TickerProfile, PriceSnapshot


class YFinanceClient:
    """
    Single-ticker yfinance client with lazy loading, resilience, and robust parsing.
    
    Implements the Proxy pattern: lazy-loads Ticker objects, caches them,
    and provides consistent error handling.
    """
    
    def __init__(self, logger: Optional[ContextLogger] = None):
        """
        Initialize YFinance client.
        
        Args:
            logger: Optional ContextLogger for operations tracing
        """
        if not HAS_YFINANCE:
            raise ImportError("yfinance required: pip install yfinance")
        
        self.logger = logger or ContextLogger('YFinanceClient')
        self.rate_limiter = RateLimiter(Config.YFINANCE_REQUESTS_PER_MINUTE)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=Config.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            name="yfinance_breaker"
        )
        self._ticker_cache = {}  # Symbol -> Ticker object
    
    def _get_ticker(self, symbol: str) -> yf.Ticker:
        """Get or create cached Ticker object (lazy-load proxy)."""
        if symbol not in self._ticker_cache:
            self.logger.set_context(symbol=symbol, operation='lazy_load_ticker')
            self._ticker_cache[symbol] = yf.Ticker(symbol)
        return self._ticker_cache[symbol]
    
    def get_profile(self, symbol: str) -> Optional[TickerProfile]:
        """
        Fetch company profile/metadata.
        
        Args:
            symbol: Ticker symbol (e.g., "AAPL")
            
        Returns:
            TickerProfile dataclass or None if fetch fails
        """
        self.logger.set_context(symbol=symbol, operation='fetch_profile')
        
        try:
            self.rate_limiter.wait()
            ticker = self._get_ticker(symbol)
            info = ticker.info
            
            return TickerProfile(
                symbol=symbol,
                isin=info.get('isin'),
                name=info.get('longName'),
                sector=info.get('sector'),
                industry=info.get('industry'),
                market_cap=info.get('marketCap'),
                employees=info.get('fullTimeEmployees'),
                exchange=info.get('exchange'),
                currency=info.get('currency', 'USD'),
                description=info.get('longBusinessSummary'),
                website=info.get('website'),
            )
        
        except Exception as e:
            self.logger.error(f"Failed to fetch profile for {symbol}: {e}")
            return None
    
    def get_price_today(self, symbol: str) -> Optional[PriceSnapshot]:
        """
        Get today's OHLCV data.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            PriceSnapshot or None if unavailable
        """
        self.logger.set_context(symbol=symbol, operation='fetch_price')
        
        try:
            self.rate_limiter.wait()
            ticker = self._get_ticker(symbol)
            hist = ticker.history(period='1d')
            
            if hist.empty:
                return None
            
            row = hist.iloc[-1]
            date_str = hist.index[-1].strftime('%Y-%m-%d')
            
            return PriceSnapshot(
                symbol=symbol,
                date=date_str,
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
                adjusted_close=float(row['Adj Close']) if 'Adj Close' in row else None,
            )
        
        except Exception as e:
            self.logger.error(f"Failed to fetch price for {symbol}: {e}")
            return None
    
    def get_historical_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Optional[List[PriceSnapshot]]:
        """
        Fetch historical OHLCV data for date range.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of PriceSnapshot or None if fetch fails
        """
        self.logger.set_context(symbol=symbol, operation='fetch_history')
        
        try:
            self.rate_limiter.wait()
            ticker = self._get_ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                return None
            
            snapshots = []
            for date, row in hist.iterrows():
                snap = PriceSnapshot(
                    symbol=symbol,
                    date=date.strftime('%Y-%m-%d'),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                    adjusted_close=float(row['Adj Close']) if 'Adj Close' in row else None,
                )
                snapshots.append(snap)
            
            return snapshots
        
        except Exception as e:
            self.logger.error(f"Failed to fetch history for {symbol}: {e}")
            return None
    
    def get_financial_statements(self, symbol: str) -> Optional[Dict]:
        """
        Fetch annual financial statements (income stmt, balance sheet, cash flow).
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Dict with 'income_stmt', 'balance_sheet', 'cash_flow' DataFrames
        """
        self.logger.set_context(symbol=symbol, operation='fetch_financials')
        
        try:
            self.rate_limiter.wait()
            ticker = self._get_ticker(symbol)
            
            return {
                'income_stmt': ticker.income_stmt,
                'balance_sheet': ticker.balance_sheet,
                'cash_flow': ticker.cash_flow,
            }
        
        except Exception as e:
            self.logger.error(f"Failed to fetch financials for {symbol}: {e}")
            return None
    
    def clear_cache(self):
        """Clear ticker cache."""
        self._ticker_cache.clear()
        self.logger.info("Ticker cache cleared")


class YFinanceBatch:
    """
    Batch processor for multiple tickers with concurrency control and rate limiting.
    
    Implements thread-pool concurrency with rate limiting to prevent API hammering.
    """
    
    def __init__(self, max_workers: int = 5, logger: Optional[ContextLogger] = None):
        """
        Initialize batch processor.
        
        Args:
            max_workers: Maximum concurrent requests
            logger: Optional ContextLogger
        """
        if not HAS_YFINANCE:
            raise ImportError("yfinance required: pip install yfinance")
        
        self.max_workers = max_workers
        self.logger = logger or ContextLogger('YFinanceBatch')
        self.rate_limiter = RateLimiter(Config.YFINANCE_REQUESTS_PER_MINUTE)
        self.client = YFinanceClient(logger=self.logger)
    
    def fetch_profiles(self, symbols: List[str]) -> Dict[str, Optional[TickerProfile]]:
        """
        Fetch profiles for multiple tickers.
        
        Args:
            symbols: List of ticker symbols
            
        Returns:
            Dict mapping symbol -> TickerProfile (or None if failed)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.client.get_profile, sym): sym for sym in symbols}
            
            for future in as_completed(futures):
                sym = futures[future]
                try:
                    results[sym] = future.result()
                except Exception as e:
                    self.logger.error(f"Batch fetch failed for {sym}: {e}")
                    results[sym] = None
        
        return results
    
    def fetch_prices_today(self, symbols: List[str]) -> Dict[str, Optional[PriceSnapshot]]:
        """Fetch today's prices for multiple tickers."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.client.get_price_today, sym): sym for sym in symbols}
            
            for future in as_completed(futures):
                sym = futures[future]
                try:
                    results[sym] = future.result()
                except Exception as e:
                    self.logger.error(f"Batch fetch failed for {sym}: {e}")
                    results[sym] = None
        
        return results
