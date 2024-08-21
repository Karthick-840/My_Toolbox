import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt 
from dateutil import relativedelta
import datetime
from datetime import timedelta
import numpy as np
import datetime
import math
import time
import requests
import os
import pandas as pd
import json
import time


def Rapid_API_calls(rapid_api_dict, local_save=False, file_name=None, params=None):
    time.sleep(1)
    
    url = rapid_api_dict.get("url")
    headers = rapid_api_dict.get("headers")
    
    if not headers:
        response = requests.get(url,verify=False)
    elif params:
        print(params)
        response = requests.get(url, headers=headers, params=params, verify=False)
    else:
        response = requests.get(url, headers=headers, verify=False)
     
    if response.status_code == 200:
        return response.json()
    else:
        print("Wrong response")
        return None


def Rapid_API_calls1(rapid_api_dict, local_save=False, file_name=None, params=None):
    with open(r"C:\Users\gksme\PycharmProjects\Local_Git_Projects\profile\portfolio\Outputs\STOXX50global_index_price.json", 'r') as file:
    response = json.load(file)

            # Convert the JSON data to a DataFrame
    if 'data' in response:
        df = pd.DataFrame(response["data"])
    else:
        df = pd.DataFrame(response)
    print(df)



def Dividend_History(ticker_data,purchase_data):
    
    Withhold_tax_Summary = {"Netherlands":0.15,"Belgium":.30,"Austria":0.275,"Germany":0.26375,"United States":0.15,"France":0.28,"Spain":0.19,"Italy":0.26,'United Kingdom':0,'Switzerland':0.35}
    
    dividend_data = ticker_data.dividends
    dates = list(purchase_data['Purchase date'].agg(['min', 'max']))
    dividends = dividend_data[str(dates[0]):str(dates[1])].to_frame().reset_index(level=0)
    dividends['Date'] = pd.to_datetime(dividends['Date'].dt.date)

    dividends[['yfinance_ticker','Currency','Country','Withholding_Tax']] = [ticker_data.info['symbol'],ticker_data.info['currency'],ticker_data.info['country'], Withhold_tax_Summary[ticker_data.info['country']]]
    
    
    dividends['Units_Held'] = dividends.apply(lambda x: 
                                              purchase_data.loc[(purchase_data['Purchase date'] <= x.Date), 'UNITS'].sum(), axis=1)
    
    dividends['Gross_Dividend'] = dividends['Units_Held']*dividends['Dividends']  
    dividends['Gross_Dividend'] = np.where(dividends['Dividends']>20,
                                           dividends['Gross_Dividend']/100, 
                                           dividends['Gross_Dividend'])
    
    dividends['Net_Dividend'] = dividends['Gross_Dividend'] - dividends['Gross_Dividend']*dividends['Withholding_Tax']
    
    
    dividends = dividends.merge(hist_exchange_data, on=['Date','Currency'], how='outer')
    
    dividends['Price_in EUR/INR'] = np.where(dividends['Close'].isnull(),dividends['Net_Dividend'],dividends['Net_Dividend']*dividends['Close']) 
    
    dividends = dividends[['Date','yfinance_ticker','Dividends','Units_Held','Gross_Dividend',
                           'Currency','Country','Withholding_Tax','Net_Dividend','Close','Price_in EUR/INR']]
    individual_stock_grouped = stock_purchase.groupby('YAHOO SYMBOL')

    
    
    return dividends


    
def currency_convert(df):
    
    df['currentPrice_in_EUR'] = df['currentPrice']
    df.loc[df['currency']=='GBp','currentPrice_in_EUR'] = df['currentPrice']/100
        
    currency_values = list(df['currency'].unique())
    currency_values.remove('INR')
    for cur in currency_values:
        exchange_rate = yf.Ticker(cur+ 'EUR=X').info['previousClose']
        df['currentPrice_in_EUR'] = np.where(df['currency'].isin([cur]),df['currentPrice_in_EUR']*exchange_rate, df['currentPrice_in_EUR'])
            
    return df

    Final_Portfolio = pd.merge(stock_details,pd.concat(concat_list),right_on='symbol',left_on='yfinance_ticker')


    Final_Portfolio = currency_convert(Final_Portfolio)

    Final_Portfolio['Current_value'] = Final_Portfolio['Avaliable_Units']*Final_Portfolio['currentPrice']
    Final_Portfolio['P/L'] = Final_Portfolio['Current_value'] - Final_Portfolio['Final Price_Buy'] + Final_Portfolio['Final Price_Sell']
    Final_Portfolio.loc[Final_Portfolio['Security_Status']=='Sold','P/L'] = Final_Portfolio['Final Price_Sell'] - Final_Portfolio['Final Price_Buy']

    Final_Portfolio['Return'] = Final_Portfolio['P/L']/Final_Portfolio['Final Price_Buy']
    Final_Portfolio['Annualized_Return'] = ((1+Final_Portfolio['Return'])**(365/Final_Portfolio['Holding_Period']))-1
    Final_Portfolio.loc[Final_Portfolio['longName'].isnull(),'longName'] = Final_Portfolio['shortName']

    Final_Portfolio['First_Purchase'],Final_Portfolio['Last_Purchase'] = Final_Portfolio['First_Purchase'].dt.date,Final_Portfolio['Last_Purchase'].dt.date

    Final_Portfolio = Final_Portfolio[['YAHOO SYMBOL','longName','Current_value','P/L','Return','Annualized_Return',
                                    'currentPrice','Avaliable_Units','Final Price_Buy','UNITS_Buy', 
                                    'Final Price_Sell','UNITS_Sell','Holding_Period','shortName',
                                    'First_Purchase', 'Last_Purchase','exDividendDate', 'lastDividendDate',
                                    'Security_Status','sector', 'industry', 'currency','quoteType','exchange',
                                    'symbol', 'logo_url','yfinance_ticker']]


    Final_Portfolio.loc[Final_Portfolio['Avaliable_Units']>0]


    Final_Portfolio.to_csv("Stock_Portfolio Complete.csv") 


    ticker = 'EMBASSY.BO'
    ticker_data = yf.Ticker(ticker)
    ticker_info = stock_data_extract(ticker_data)
    ticker_info


    # Dividend History
    Dividend_df = pd.concat(Dividend_list)

    Dividend_df

    df[['column_new_1', 'column_new_2', 'column_new_3']] = ['EUR','Germany','tax']

    df1 = pd.read_csv("CHFEUR=X.csv")
    df1.insert(0,column='Currency',value='CHF')
    df2=pd.read_csv("EUR=X.csv")
    df2.insert(0,column='Currency',value='USD')
    df3=pd.read_csv("GBPEUR=X.csv")
    df3.insert(0,column='Currency',value='GBP')

    hist_exchange_data = pd.concat([df1,df2,df3]).drop(["Open","High","Low","Adj Close","Volume"], axis=1)
    hist_exchange_data.loc[hist_exchange_data['Currency']=='GBP','Currency'] = 'GBp'
    hist_exchange_data = pd.read_csv("Currency_exchange.csv")

    pd.concat(concat_list)
    pd.concat(Dividend_list)



    individual_stock_grouped = stock_purchase.groupby('YAHOO SYMBOL')

    concat_list = []
    Dividend_list = []
    for index,row in stock_details.iterrows():
        ticker = row['yfinance_ticker']
        purchase_data = individual_stock_grouped.get_group(row['YAHOO SYMBOL'])
        try:
            # Getting Stock data----
            ticker_data = yf.Ticker(ticker)
            ticker_info = stock_data_extract(ticker_data)
            concat_list.append(ticker_info)

            del ticker_data,ticker_info
        except Exception:
            pass
                
        del ticker
    
class Redundant_Functions():
    def __init__(self,) -> None:
    def apply(self):
        pass
    
    def gold_rate_history(self):
    
    # 50 per month

    url = "https://gold-rates-india.p.rapidapi.com/api/gold-city-history"

    querystring = {"type":"monthly"}

    headers = {
      "x-rapidapi-key": "513455dd81msh1a3cf1901196937p109fbdjsnbe2ae109fbad",
      "x-rapidapi-host": "gold-rates-india.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    json_output_path = os.path.join(self.output_folder,"gold_rate_history.json")
    with open(json_output_path, 'w') as f:
      json.dump(response.json(), f, indent=4)   
            
    
  
 
  
        