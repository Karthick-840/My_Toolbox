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
            
    
  
 
# NOTION TOOLS

# Prerequesit Create Notion Integration
# Create a database in Notion and share to get the database ID - https://www.youtube.com/watch?v=M1gu9MDucMA&list=PLe0U7sHuld_qIILgg-2ESRCPWu-WBalFJ&index=42
"""
How to set up the Notion API
How to set up the Python code
How to create database entries
How to query the database
How to update database entries
And how to delete entries.

"""

import requests
from datetime import datetime, timezone

NOTION_TOKEN = ""
DATABASE_ID = ""

headers = {
    "Authorization": "Bearer "+NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2024-06-28"
}

#Creating pages in your Notion database
def create_page(data: dict):
    create_url = "https://api.notion.com/v1/pages"

    payload = {"parent": {"database_id": DATABASE_ID}, "properties": data}

    res = requests.post(create_url, headers=headers, json=payload)
    # print(res.status_code)
    return res

from datetime import datetime, timezone

title = "Test Title"
description = "Test Description"
published_date = datetime.now().astimezone(timezone.utc).isoformat()
data = {
    "URL": {"title": [{"text": {"content": description}}]},
    "Title": {"rich_text": [{"text": {"content": title}}]},
    "Published": {"date": {"start": published_date, "end": None}}
}
https://developers.notion.com/reference/intro
create_page(data)
The corresponding data fields have to correspond to your table column names.

The schema might look a bit complicated and differs for different data types (e.g. text, date, boolean etc.). To determine the exact schema, I recommend dumping the data (see next step) and inspecting the JSON file.

In our example, we create data for the URL, the Title, and the Published columns like so:

def get_pages(num_pages=None):
    """
    If num_pages is None, get all pages, otherwise just the defined number.
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)

    data = response.json()

    # Comment this out to dump all data to a file
    # import json
    # with open('db.json', 'w', encoding='utf8') as f:
    #    json.dump(data, f, ensure_ascii=False, indent=4)

    results = data["results"]
    while data["has_more"] and get_all:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])

    return results

Querying Notion database and reading pages¶
To query your database and read all entries, we can use the following function. It uses pagination to retrieve all entries:
pages = get_pages()

for page in pages:
    page_id = page["id"]
    props = page["properties"]
    url = props["URL"]["title"][0]["text"]["content"]
    title = props["Title"]["rich_text"][0]["text"]["content"]
    published = props["Published"]["date"]["start"]
    published = datetime.fromisoformat(published)
    
Updating pages in your Notion databse¶
To update a page, we have to send a PATCH request:

def update_page(page_id: str, data: dict):
    url = f"https://api.notion.com/v1/pages/{page_id}"

    payload = {"properties": data}

    res = requests.patch(url, json=payload, headers=headers)
    return res
For example, if we want to update the Published field, we send the following data. It is the same schema as for creating the page:
    
    

update_page(page_id, update_data)

Deleting pages in your Notion database¶
Deleting a page is achieved with the same endpoint as for updating the page, but here we set the archived parameter to True:

def delete_page(page_id: str):
    url = f"https://api.notion.com/v1/pages/{page_id}"

    payload = {"archived": True}

    res = requests.patch(url, json=payload, headers=headers)
    return res