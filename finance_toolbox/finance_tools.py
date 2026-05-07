"""
Finance tools for yfinance data fetching and processing.
Provides utilities for querying Yahoo Finance data with concurrent processing.
"""

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:  # pragma: no cover
    HAS_YFINANCE = False


# Configure session for better connection pooling
_session = requests.Session()
_adapter = HTTPAdapter(pool_connections=40, pool_maxsize=40)
_session.mount('https://', _adapter)
_session.mount('http://', _adapter)


class FinanceTools:
    """
    Finance data fetching and processing tools using yfinance API.
    
    Supports concurrent ticker data retrieval, filtering, and JSON export.
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize FinanceTools.
        
        Args:
            logger: Optional logger instance. If provided, logs will be sent to it.
        
        Raises:
            ImportError: If yfinance is not installed.
        """
        if not HAS_YFINANCE:  # pragma: no cover
            raise ImportError(
                "yfinance is required for FinanceTools. "
                "Install it with: pip install yfinance"
            )
        
        if logger:
            logger.info('Finance Tools Initiated.')
            self.logger = logger.getChild(__name__)
        else:
            self.logger = logging.getLogger(__name__)

    def get_yfinance_info(
        self,
        yahoo_summary: pd.DataFrame,
        data_type: str = "SIP",
        save_path: str = ".",
        process: str = "get_history",
    ) -> List[Dict[str, Any]]:
        """
        Fetch Yahoo Finance data for multiple tickers concurrently.
        
        Args:
            yahoo_summary: DataFrame with columns 'Yahoo_Ticker', 'min_start',
                'max_end', 'Security_Status'
            data_type: Type of data ('SIP' or other). Affects which columns
                are retained
            save_path: Directory to save output JSON files
            process: Process type ('get_history' or other)
        
        Returns:
            List of dictionaries containing ticker info and price data for successful fetches
        """
        self.logger.info('Initiating Yfinance Data Import.')

        if process != "get_history":
            yahoo_summary = yahoo_summary[yahoo_summary['Security_Status'] != 'Sold'].copy()
            yahoo_summary['min_start'] = pd.to_datetime(pd.Timestamp.now().replace(day=1))

        history = []
        unavailable = []

        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(
                    self.fetch_ticker_data, row, data_type, save_path
                ): row['Yahoo_Ticker']
                for _, row in yahoo_summary.iterrows()
            }

            for future in as_completed(futures):
                result = future.result()
                if result and 'prices' in result and result['prices']:
                    history.append(result)
                elif result:
                    unavailable.append(result.get('Yahoo_Ticker', 'Unknown'))

        # Save merged JSON file for all tickers
        output_file_path = os.path.join(save_path, f'New_{data_type}_Info.json')
        os.makedirs(save_path, exist_ok=True)
        with open(output_file_path, 'w') as f:
            json.dump(history, f, indent=2)

        if unavailable:
            unavailable_path = os.path.join(save_path, f'Unavailable_securities_{data_type}.json')
            with open(unavailable_path, 'w') as f:
                json.dump(unavailable, f, indent=2)
            self.logger.info(f"Securities unavailable: {', '.join(unavailable)}")

        self.logger.info(f"Merged JSON saved to {output_file_path}")
        return history

    def fetch_ticker_data(
        self,
        row: pd.Series,
        data_type: str = "SIP",
        save_path: str = ".",
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch data for a single ticker from Yahoo Finance.
        
        Args:
            row: Series containing 'Yahoo_Ticker', 'min_start', 'max_end'
            data_type: Type of data ('SIP' or other)
            save_path: Directory path for potential file saves
        
        Returns:
            Dictionary with ticker info and prices, or None on error
        """
        ticker = row['Yahoo_Ticker']
        try:
            min_start = pd.to_datetime(row['min_start']).date()
            max_end = pd.to_datetime(row['max_end']).date()

            # Pause to avoid rate limits
            time.sleep(4)

            # Fetch Yahoo Finance data
            ticker_data = yf.Ticker(ticker)
            price_df = ticker_data.history(period="max")
            price_df.reset_index(inplace=True)
            price_df['Date'] = pd.to_datetime(price_df['Date']).dt.date
            price_df = price_df[(price_df['Date'] >= min_start) & (price_df['Date'] <= max_end)]

            # Process ticker info and price data
            info = ticker_data.info
            columns_to_drop = ['Open', 'High', 'Low', 'Volume']
            price_df = price_df.drop(
                columns=[col for col in columns_to_drop if col in price_df.columns]
            )

            if data_type == 'SIP':
                price_df = price_df.drop(
                    columns=[
                        col
                        for col in ['Dividends', 'Stock Splits']
                        if col in price_df.columns
                    ],
                    errors='ignore',
                )
            else:
                price_df = price_df[
                    (price_df['Dividends'] > 0) | (price_df['Stock Splits'] > 0)
                ]
                if 'Close' in price_df.columns:
                    price_df = price_df.drop(['Close'], axis=1)

            if 'Date' in price_df.columns:
                price_df['Date'] = price_df['Date'].astype(str)

            json_file = {
                'Yahoo_Ticker': ticker,
                'info': info,
                'prices': (
                    price_df.to_dict(orient='records')
                    if not price_df.empty
                    else {}
                )
            }

            self.logger.info(f'Query for {ticker} data between {min_start} and {max_end}')
            return json_file

        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error processing {ticker}: {e}")
            return {'Yahoo_Ticker': ticker}

    @staticmethod
    def include_stamp_duty(value: float, transaction_date: str) -> float:
        """
        Apply India stamp duty calculation to a transaction value.
        
        Stamp duty is 0.005% of transaction value for purchases after 2020-07-01.
        
        Args:
            value: Transaction value in rupees
            transaction_date: Transaction date as string
        
        Returns:
            Value after stamp duty deduction
        """
        if pd.to_datetime(transaction_date) > pd.to_datetime('2020-07-01'):
            return round(int(value) * (1 - 0.00005), 2)
        return int(value)
