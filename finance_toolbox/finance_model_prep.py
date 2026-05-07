import os
import requests
import certifi
import json
import pandas as pd

class FinanceModelPrep():
    def __init__(self,api_key,ticker,exchange):
        self.api_key = api_key
        self.ticker = ticker
        self.exchange = exchange
        self.file_path = f'docs/{self.ticker}.csv'

    def apply(self):
        # Check if the file already exists
        if os.path.exists(self.file_path):
            # Load existing DataFrame from CSV file
            eco_ind = pd.read_csv(self.file_path)
            
        else:
            # Fetch data from API and create DataFrame
            eco_ind = pd.DataFrame(self.get_jsonparsed_data())
             # Save the DataFrame to CSV
            eco_ind.to_csv(self.file_path, index=False)
        
        eco_ind = self.preprocess_economic_data(eco_ind)
        return eco_ind

    def get_jsonparsed_data(self):
        if self.exchange == "NSE":
            url = f"https://financialmodelingprep.com/api/v3/search?query={self.ticker}&exchange=NSE&apikey={self.api_key}"
        else:
            url = f"https://financialmodelingprep.com/api/v3/quote/{self.ticker}?apikey={self.api_key}"

        # Make a GET request to the API, verifying with certifi's CA file
        response = requests.get(url, verify=certifi.where())
        response.raise_for_status()  # Raise an error for bad HTTP status codes

        return response.json()  # Automatically parse JSON response
    
    def preprocess_economic_data(self,df):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['earningsAnnouncement'] = pd.to_datetime(df['earningsAnnouncement'])
        return df

