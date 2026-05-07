# financial_data_processor.py

import pandas as pd
import requests
import os
from datetime import datetime
from utils import get_api_key, load_documents_from_csv
from langchain.docstore.document import Document

class FinancialDataProcessor:
    def __init__(self, api_key_name="FMP_API_KEY", base_url="https://financialmodelingprep.com/api/v3"):
        self.api_key = get_api_key(api_key_name)
        self.base_url = base_url

    def _make_api_request(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"
        all_params = {"apikey": self.api_key}
        if params:
            all_params.update(params)
        response = requests.get(url, params=all_params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()

    def fetch_economic_indicators(self):
        """Fetches major economic indicators."""
        print("Fetching major economic indicators...")
        data = self._make_api_request("economic_indicators")
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def fetch_company_key_metrics(self, symbol):
        """Fetches key metrics for a given company symbol."""
        print(f"Fetching key metrics for {symbol}...")
        data = self._make_api_request(f"key-metrics/{symbol}")
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def fetch_income_statement(self, symbol):
        """Fetches income statement for a given company symbol."""
        print(f"Fetching income statement for {symbol}...")
        data = self._make_api_request(f"income-statement/{symbol}")
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def fetch_balance_sheet_statement(self, symbol):
        """Fetches balance sheet statement for a given company symbol."""
        print(f"Fetching balance sheet statement for {symbol}...")
        data = self._make_api_request(f"balance-sheet-statement/{symbol}")
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def fetch_cash_flow_statement(self, symbol):
        """Fetches cash flow statement for a given company symbol."""
        print(f"Fetching cash flow statement for {symbol}...")
        data = self._make_api_request(f"cash-flow-statement/{symbol}")
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def fetch_all_company_data(self, symbol):
        """Fetches all relevant financial statements and key metrics for a company."""
        key_metrics_df = self.fetch_company_key_metrics(symbol)
        income_statement_df = self.fetch_income_statement(symbol)
        balance_sheet_df = self.fetch_balance_sheet_statement(symbol)
        cash_flow_statement_df = self.fetch_cash_flow_statement(symbol)
        
        return {
            "key_metrics": key_metrics_df,
            "income_statement": income_statement_df,
            "balance_sheet": balance_sheet_df,
            "cash_flow_statement": cash_flow_statement_df
        }

    def process_and_save_economic_indicators(self, output_dir="data"):
        """Fetches, processes, and saves economic indicators to a CSV."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        economic_df = self.fetch_economic_indicators()
        economic_df['Description'] = economic_df.apply(
            lambda row: f"Date: {row['date'].strftime('%Y-%m-%d')}, Indicator: {row['economicIndicator']}, Value: {row['value']}",
            axis=1
        )
        file_path = os.path.join(output_dir, "economic_indicators.csv")
        economic_df.to_csv(file_path, index=False)
        print(f"Economic indicators saved to {file_path}")
        return file_path
    
    def process_and_save_company_data(self, symbol, output_dir="data"):
        """Fetches, processes, and saves all company data to a CSV."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        company_data = self.fetch_all_company_data(symbol)
        
        all_company_docs = []
        for doc_type, df in company_data.items():
            if not df.empty:
                for _, row in df.iterrows():
                    # Create a meaningful description for the document content
                    description_parts = [f"Company: {symbol}, Type: {doc_type.replace('_', ' ').title()}"]
                    for col, value in row.items():
                        if pd.notna(value) and col != 'date': # 'date' handled separately if needed for metadata
                            description_parts.append(f"{col.replace('_', ' ').title()}: {value}")
                    
                    page_content = ", ".join(description_parts)
                    
                    # Include a date in metadata if available
                    metadata = {'symbol': symbol, 'doc_type': doc_type}
                    if 'date' in row and pd.notna(row['date']):
                        metadata['date'] = row['date'].strftime('%Y-%m-%d')

                    all_company_docs.append(Document(page_content=page_content, metadata=metadata))
        
        # This will save all processed data into one CSV
        # For simplicity, we'll convert Documents back to a DataFrame for saving
        # In a real scenario, you might save each type to a separate CSV or use a more complex structure
        if all_company_docs:
            df_to_save = pd.DataFrame([doc.dict() for doc in all_company_docs])
            file_path = os.path.join(output_dir, f"{symbol}_financial_data.csv")
            df_to_save.to_csv(file_path, index=False)
            print(f"Company financial data for {symbol} saved to {file_path}")
            return file_path
        else:
            print(f"No company financial data found for {symbol} to save.")
            return None
