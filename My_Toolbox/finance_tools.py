import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import yfinance as yf
import requests
from requests.adapters import HTTPAdapter
#from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
adapter = HTTPAdapter(pool_connections=40, pool_maxsize=40)  # Adjust pool size as needed
session.mount('https://', adapter)
session.mount('http://', adapter)


class FinanceTools:
    """Class for handling financial data operations using Yahoo Finance."""

    def __init__(self, logger=None):
        if logger:
            self.logger = logger.info('Finance Tools Initiated.')
            self.logger = logger.getChild(__name__)

    def get_yfinance_info(self, yahoo_summary, data_type, save_path, process):
        """Fetch Yahoo Finance data based on the provided summary.

        Args:
            yahoo_summary (DataFrame): Summary DataFrame containing tickers.
            data_type (str): Type of data to fetch Fund/ETF or Stock.
            save_path (str): Path to save output files.
            process (str): Process type, e.g., "get_history".

        Returns:
            list: History of fetched data.
        """
        self.logger.info('Initiating Yfinance Data Import.')

        if process != "get_history":
            yahoo_summary = yahoo_summary[yahoo_summary['Security_Status'] != 'Sold']
            yahoo_summary['min_start'] = pd.to_datetime(pd.Timestamp.now().replace(day=1))

        # Using threading for concurrent API calls
        history = []
        unavailable = []

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.fetch_ticker_data, row, data_type)
                       for _, row in yahoo_summary.iterrows()]


        for future in as_completed(futures):
            try:
                result = future.result()  # This will raise an exception if the task failed
                if result:
                    history.append(result)
                else:
                    unavailable.append(futures[future]['Yahoo_Ticker'])  # Row should be available
            except Exception as e:  # Add to unavailable if an exception occurs
                unavailable.append(futures[future]['Yahoo_Ticker']) 
                self.logger.error(
                    f"Error fetching data for ticker: {futures[future]['Yahoo_Ticker']}, Error: {e}")

        # Save merged JSON file for all tickers
        output_file_path = os.path.join(save_path, f'New_{data_type}_Info.json')
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(history, f)

        if unavailable:  # Save `Unavailable` data if any
            unavailable_output_path = os.path.join(save_path, f'Unavailable_{data_type}.json')
            with open(unavailable_output_path, 'w', encoding='utf-8') as f:
                json.dump(unavailable, f)

        self.logger.info(f"Merged JSON saved to {output_file_path}")
        self.logger.info(f"Securities unavailable: {', '.join(unavailable)}")

        return history

    def fetch_ticker_data(self, row, data_type):
        """Fetch data for a specific ticker.

        Args:
            row (Series): A row from the summary DataFrame.
            data_type (str): Type of data to fetch.

        Returns:
            dict: Fetched data or error information.
        """
        ticker = row['Yahoo_Ticker']
        try:
            min_start = pd.to_datetime(row['min_start']).date()
            max_end = pd.to_datetime(row['max_end']).date()

            # Pause to avoid rate limits
            time.sleep(1)

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
                columns=[col for col in columns_to_drop if col in price_df.columns])

            if data_type == 'SIP':
                price_df = price_df.drop(['Dividends', 'Stock Splits'], axis=1)
            else:
                price_df = price_df[(price_df['Dividends'] > 0) | (price_df['Stock Splits'] > 0)]
                price_df = price_df.drop(['Close'], axis=1)

            if 'Date' in price_df.columns:
                price_df['Date'] = price_df['Date'].astype(str)

            json_file = {'Yahoo_Ticker': ticker, "info": info,
                         "prices": price_df.to_dict(orient='records') if not price_df.empty else {}}

            self.logger.info(f'Query for {ticker} data between {min_start} and {max_end}')
            return json_file  # Return data for further processing in main function

        except Exception as e:
            self.logger.error(f"Error processing {ticker}: {e}")
            return {'Yahoo_Ticker': ticker}  # Return None if data fetching fails

    @staticmethod
    def include_stamp_duty(value: float, transaction_date: str) -> float:
        """Calculate the stamp duty on a given value based on the transaction date.

        Args:
            value (float): The monetary value of the asset or security.
            transaction_date (str): The date of the transaction in 'YYYY-MM-DD' format.

        Returns:
            float: The value after applying stamp duty, rounded to 2 decimal places.
        """
        # Convert the transaction date to a datetime object and check against the effective date.
        effective_date = pd.to_datetime('2020-07-01')

        if pd.to_datetime(transaction_date) > effective_date:
            return round(value * (1 - 0.00005), 2)
        return float(value)
