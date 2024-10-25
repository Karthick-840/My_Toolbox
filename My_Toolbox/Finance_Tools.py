import requests
from requests.adapters import HTTPAdapter
#from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
adapter = HTTPAdapter(pool_connections=40, pool_maxsize=40)  # Adjust pool size as needed
session.mount('https://', adapter)
session.mount('http://', adapter)

import pandas as pd
import time
import yfinance as yf
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

class Finance_Tools:
    
    def __init__(self,logger=None):
        if logger:
            self.logger = logger.info('Finance Tools Initiated.')
            self.logger = logger.getChild(__name__)
        

    def Get_yfinance_info(self, yahoo_summary, type, save_path, Process):
        self.logger.info('Initiating Yfinance Data Import.')

        if Process != "get_history":
            yahoo_summary = yahoo_summary[yahoo_summary['Security_Status'] != 'Sold']
            yahoo_summary['min_start'] = pd.to_datetime(pd.Timestamp.now().replace(day=1))

        # Using threading for concurrent API calls
        History = []
        Unavailable = []

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.fetch_ticker_data, row, type, save_path) for _, row in yahoo_summary.iterrows()]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    History.append(result)
                else:
                    Unavailable.append(result['Yahoo_Ticker'])

        # Save merged JSON file for all tickers
        output_file_path = os.path.join(save_path, f'New_{type}_Info.json')
        with open(output_file_path, 'w') as f:
            json.dump(History, f)
        
                # Save `Unavailable` data if any
        if Unavailable:
            unavailable_output_path = os.path.join(save_path, f'Unavailable_securities_{type}.json')
            with open(unavailable_output_path, 'w') as f:
                json.dump(Unavailable, f)
        
        
        self.logger.info(f"Merged JSON saved to {output_file_path}")
        self.logger.info(f"Securities unavailable: {', '.join(Unavailable)}")
        
        return History
        
         
    def fetch_ticker_data(self, row, type, save_path):
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
            price_df = price_df.drop(columns=[col for col in columns_to_drop if col in price_df.columns])

            if type == 'SIP':
                price_df = price_df.drop(['Dividends', 'Stock Splits'], axis=1)
            else:
                price_df = price_df[(price_df['Dividends'] > 0) | (price_df['Stock Splits'] > 0)]
                price_df = price_df.drop(['Close'], axis=1)
                
            if 'Date' in price_df.columns:
                price_df['Date'] = price_df['Date'].astype(str)

            json_file = {'Yahoo_Ticker': ticker, "info": info, 
                         "prices": price_df.to_dict(orient='records') if not price_df.empty else {}}
            
            # output_file_path = os.path.join(save_path, f'New_{type}_{ticker}_Info.json')
            # with open(output_file_path, 'w') as f:
            #     json.dump(json_file, f)
            
            self.logger.info(f'Query for {ticker} data between {min_start} and {max_end}')
            return json_file  # Return data for further processing in main function

        except Exception as e:
            self.logger.error(f"Error processing {ticker}: {e}")
            return  {'Yahoo_Ticker': ticker}  # Return None if data fetching fails
        
        
    @staticmethod
    def Include_stamp_duty(value,transaction_date):
            # Stamp duty is a form of tax levied on the purchase or sale of an asset or security.It is collected at a meagre rate of 0.005% of the overall purchase made and is effective from 1 July 2020 as per the government’s order. 
            if pd.to_datetime(transaction_date) > pd.to_datetime('2020-07-01'):
                return round(int(value)*(1-0.00005),2)
            else:
                return int(value)
            
            
    
    def Get_yfinance_info1(self,yahoo_summary,type,save_path, Process):
        
        self.logger.info('Initiating Yfinance Data Import.')
        
        if Process != "get_history":
            yahoo_summary = yahoo_summary[yahoo_summary['Security_Status'] != 'Sold']
            yahoo_summary['min_start'] =  pd.to_datetime(pd.Timestamp.now().replace(day=1))

        History = []
        Unavailable = []
        price_df = pd.DataFrame()
        
        for index, row in yahoo_summary.iterrows():
                ticker = row['Yahoo_Ticker']
                try:
                    min_start = pd.to_datetime(row['min_start']).date()
                    max_end = pd.to_datetime(row['max_end']).date()
                    
                    time.sleep(4)
                    ticker_data = yf.Ticker(ticker)
                    price_df = ticker_data.history(period="max")
                    price_df.reset_index(inplace=True)
                    
                    price_df['Date'] = pd.to_datetime(price_df['Date']).dt.date
                    price_df = price_df[(price_df['Date'] >= min_start) & (price_df['Date'] <= max_end)]
                    info = ticker_data.info
                    min_date_str = price_df['Date'].min().strftime('%Y-%m-%d')  # Convert to string
                    max_date_str = price_df['Date'].max().strftime('%Y-%m-%d')  # Convert to string
                    columns_to_drop = ['Open', 'High', 'Low', 'Volume']
                    # Only drop columns that exist in the DataFrame
                    price_df = price_df.drop(columns=[col for col in columns_to_drop if col in price_df.columns])


                    if type =='SIP':
                        price_df = price_df.drop(['Dividends','Stock Splits'], axis=1)
                    else:
                        price_df = price_df[(price_df['Dividends'] > 0) | (price_df['Stock Splits'] > 0)]
                        price_df = price_df.drop(['Close'], axis=1)
                        
                    if 'Date' in price_df.columns:
                        price_df['Date'] = price_df['Date'].astype(str)

                    json_file = { 'Yahoo_Ticker': ticker,"info": info , 
                    "prices": price_df.to_dict(orient='records') if isinstance(price_df, pd.DataFrame) and not price_df.empty else {}}

                    output_file_path = os.path.join(save_path, f'New_{type}_{ticker}_Info.json')
                    with open(output_file_path , 'w') as f:
                        json.dump(json_file,f)
                    History.append(json_file)
                    
                    #min_date, max_date = price_df['Date'].min().strftime('%Y-%m-%d'), price_df['Date'].max().strftime('%Y-%m-%d')
                    self.logger.info(f'Query for {ticker}  data between {min_start} and {max_end}')
                except Exception as e:
                    self.logger.info(f"Error processing {ticker}: {e}")     # Print the ticker and the error message
                    Unavailable.append(ticker)
            
        output_file_path = os.path.join(save_path, f'New_{type}_Info.json')
        with open(output_file_path , 'w') as f:
            json.dump(History,f)   
        self.logger.info(f"Merged JSON saved to {output_file_path}")   
        self.logger.info(f"Securities unavailable: {', '.join(Unavailable)}")
