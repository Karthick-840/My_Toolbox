import pandas as pd
import yfinance as yf
import logging
import json
from typing import Dict, Any, Optional

class YFTools:
    """
    Leaner utility for long-term investors using Cached Proxy logic.
    Optimizes API access and ensures the tool is pickle-safe.
    """

    def __init__(self, symbol: str, logger: Optional[logging.Logger] = None):
        self.symbol = symbol
        self.logger = logger or logging.getLogger(__name__)
        self._ticker = None  # The Proxy placeholder

    @property
    def ticker(self) -> yf.Ticker:
        """
        Proxy Property: Lazy loads the Ticker and caches it for the session.
        This prevents creating multiple thread locks and redundant objects.
        """
        if self._ticker is None:
            self.logger.info(f"Initializing yfinance Ticker for {self.symbol}")
            self._ticker = yf.Ticker(self.symbol)
        return self._ticker

    def __getstate__(self):
        """
        Ensures pickle safety by removing the unpickleable _ticker (RLock).
        Allows you to save the tool's state without crashing.
        """
        state = self.__dict__.copy()
        state['_ticker'] = None 
        return state

    def _apply_date_filter(self, df: pd.DataFrame, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Internal helper to filter DataFrames by Date index, handling timezone awareness."""
        if df is None or df.empty:
            return df
        
        # 1. Ensure index is datetime
        df.index = pd.to_datetime(df.index)

        # 2. Convert string inputs to Timestamps
        start_ts = pd.to_datetime(start_date) if start_date else None
        end_ts = pd.to_datetime(end_date) if end_date else None

        # 3. Handle Timezone Awareness
        # If the DataFrame has a timezone, the filter must match it
        if df.index.tz is not None:
            if start_ts and start_ts.tz is None:
                # Use tz_localize instead of localize
                start_ts = start_ts.tz_localize(df.index.tz)
            if end_ts and end_ts.tz is None:
                end_ts = end_ts.tz_localize(df.index.tz)
        else:
            # If the DataFrame is naive, ensure the filters are naive
            if start_ts and start_ts.tz is not None:
                start_ts = start_ts.tz_localize(None)
            if end_ts and end_ts.tz is not None:
                end_ts = end_ts.tz_localize(None)

        # 4. Perform the comparison[cite: 1]
        if start_ts:
            df = df[df.index >= start_ts]
        if end_ts:
            df = df[df.index <= end_ts]
            
        return df

    def get_full_profile(self) -> Dict[str, Any]:
        """Get Metadata (Info), ISIN, and Business Summary."""
        info = self.ticker.info
        return {
            "symbol": self.symbol,
            "isin": self.ticker.isin,
            "metadata": info,
            "summary": info.get("longBusinessSummary", "N/A"),
            "sector": info.get("sector", "N/A")
        }

    def get_financial_statements(self, quarterly: bool = False) -> Dict[str, pd.DataFrame]:
        """Fetch Income Statement, Balance Sheet, and Cash Flow."""
        # Using the Cached Proxy prevents re-initializing the network session
        t = self.ticker
        if quarterly:
            return {
                "income_stmt": t.quarterly_income_stmt,
                "balance_sheet": t.quarterly_balance_sheet,
                "cash_flow": t.quarterly_cash_flow
            }
        return {
            "income_stmt": t.income_stmt,
            "balance_sheet": t.balance_sheet,
            "cash_flow": t.cash_flow
        }

    def get_dividends_and_splits(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Get all History of Dividends and Stock Splits."""
        actions = self.ticker.actions 
        return self._apply_date_filter(actions, start_date, end_date)

    def get_dividends_and_splits_unadjusted(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Get the true, unadjusted History of Dividends and Stock Splits."""
        # 1. Grab the actions from Yahoo (which are already pre-adjusted)
        actions = self.ticker.actions.copy()
        
        if actions.empty:
            return actions

        # 2. Reverse the Adjustment
        # 'Stock Splits' are usually > 1 (e.g., 3.0 for a 3-for-1 split).
        # We need to work backwards from the most recent date.
        # We calculate a multiplier that is 1.0 for the newest stuff 
        # and increases as we go back in time past split events.
        
        # This replaces any 0.0 splits with 1.0 so we don't multiply by zero
        split_ratios = actions['Stock Splits'].replace(0, 1)
        
        # Calculate the cumulative product moving backwards
        # This creates the multiplier needed for each specific era
        multiplier = split_ratios.iloc[::-1].cumprod().iloc[::-1]
        
        # Apply the fix
        actions['Dividends'] = actions['Dividends'] * multiplier

        # 3. Apply your existing date filter
        return self._apply_date_filter(actions, start_date, end_date)

    def get_analysis_estimates(self) -> Dict[str, pd.DataFrame]:
        """Get Analyst Price Targets and Earnings/Revenue Estimates."""
        t = self.ticker
        return {
            "earnings_estimate": t.earnings_estimate,
            "revenue_estimate": t.revenue_estimate,
            "price_targets": t.analyst_price_targets
        }

    def get_ownership_data(self) -> Dict[str, pd.DataFrame]:
        """Get Major, Institutional, and Mutual Fund holders."""
        t = self.ticker
        return {
            "major_holders": t.major_holders,
            "institutional_holders": t.institutional_holders,
            "mutualfund_holders": t.mutualfund_holders
        }

    def get_price_history(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Fetch Full Price History with optional date filtering."""
        history = self.ticker.history(period="max")
        history = history[['Close', 'Dividends', 'Stock Splits']]
        return self._apply_date_filter(history, start_date, end_date)

    def export_full_snapshot_json(self) -> str:
        """Exports everything to a JSON file. Handles Pandas-to-JSON conversion."""
        raw_bundle = {
            "profile": self.get_full_profile(),
            "financials_annual": self.get_financial_statements(quarterly=False),
            "financials_quarterly": self.get_financial_statements(quarterly=True),
            "actions": self.get_dividends_and_splits_unadjusted(),
            "ownership": self.get_ownership_data(),
            "estimates": self.get_analysis_estimates()
        }

        def json_safe(obj):
            # 1. Handle DataFrames/Series first
            if isinstance(obj, (pd.DataFrame, pd.Series)):
                d = obj.to_dict()
                return {
                    (k.strftime('%Y-%m-%d') if hasattr(k, 'strftime') else str(k)): json_safe(v) 
                    for k, v in d.items()
                }
            
            # 2. Handle Dictionaries
            if isinstance(obj, dict):
                return {str(k): json_safe(v) for k, v in obj.items()}
            
            # 3. Handle Lists/Tuples
            if isinstance(obj, (list, tuple)):
                return [json_safe(i) for i in obj]

            # 4. Handle Timestamps/Dates
            if hasattr(obj, 'strftime'):
                return obj.strftime('%Y-%m-%d')

            # 5. Handle Nulls/NaNs safely (This was the likely "Ambiguous" culprit)
            if pd.api.types.is_scalar(obj) and pd.isna(obj):
                return None
            
            # 6. Fallback for basic types (int, float, str, etc.)
            return obj

        filename = f"{self.symbol}_snapshot.json"
        with open(filename, "w") as f:
            json.dump(json_safe(raw_bundle), f, indent=4)
        
        return filename