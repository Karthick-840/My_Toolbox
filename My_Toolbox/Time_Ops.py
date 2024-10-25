import pandas as pd
from datetime import datetime, timedelta
import calendar
import time
import json


class Date_Manipulations:

    def __init__(self,logger=None):
        self.today_str = datetime.today().strftime('%Y-%m-%d')
        if logger:
            self.logger = logger.info('Date Manipulation Tools Initiated.')
            self.logger = logger.getChild(__name__)

    def update_end_date(self, text):
        
        if isinstance(text, str) and text.upper() == "TILL":
            return datetime.today().strftime('%Y-%m-%d')
        else:
            return text
  
    def convert_to_standard_date(self, date_str):
        try:
            # Try parsing the date assuming it's already in YYYY-MM-DD format
            return pd.to_datetime(date_str, format='%Y-%m-%d', errors='raise').strftime('%Y-%m-%d')
        except ValueError:
            try:
                # If it fails, try parsing it in the other format (e.g., '6-May-20')
                return pd.to_datetime(date_str, format='%d-%b-%y').strftime('%Y-%m-%d')
            except Exception as e:
                # Log the error with the row index and problematic date_str
                print(f"Error converting date '{date_str}': {e}")
                raise e

    def string_to_datetime(self, text,format='%Y-%m-%d'):
        
        try:
            return pd.to_datetime(text, format=format)
        except ValueError:
            return None
        
    def datetime_to_string(self, date_string,format='%Y-%m-%d'):
        
        try:
            dt = pd.to_datetime(date_string, errors='coerce')
            if pd.isna(dt):
                return None
            return dt.strftime(format)
        except Exception as e:
        # Handle any other unforeseen errors
            print(f"Error: {e}")
            return None
        
    
    def get_next_business_day(self,date):
      # Convert string to datetime object
      #date = datetime.strptime(date, '%Y-%m-%d')
      
      date = self.string_to_datetime(date, format='%Y-%m-%d')

      # Check if weekend (Saturday or Sunday)
      if date.isocalendar()[1] in [6, 7]:
      # Calculate next Monday's date
        offset_days = (calendar.MONDAY - date.isocalendar()[1]) % 7
        next_monday = date + timedelta(days=offset_days)
      else:
        # Weekday, return original date
        next_monday = date

      # Format the date as 'YYYY-MM-DD'
      return next_monday.strftime("%Y-%m-%d")
    
    def date_generator(self,sdate,edate,delay=0):
        
        sdate = self.string_to_datetime(sdate)
        edate= self.string_to_datetime(edate)
        delay = int(delay)
        
        
        date_interval = pd.date_range(sdate - timedelta(days=30), edate, freq='MS') 
        
        #pd.date_range gerneate only dates from month start or mid or end. genreating custom dates is difficult. SO the idea here is that we generate the dates, add offset, which the exact date the trasnaction took place and add delays which is th delay days that the bank takes.
        
        # Generate monthly dates with a offset (can adjust offset as needed) as the pd.date_range generate only first month.
        
        date_interval += timedelta(days=delay+sdate.day)
        new_date_interval = [self.get_next_business_day(date) for date in date_interval] # Add days to get the next business day (Monday)
        
        return new_date_interval
    
    def find_closest_date(self,row,nav_df):
        scheme = row['scheme']
        date = self.string_to_datetime(row['date'])
        
    
        # Filter nav_df for the same scheme
        filtered_nav_df = nav_df[nav_df['scheme'] == scheme]
        
        # Calculate the absolute difference between dates
        filtered_nav_df['date_diff'] = abs(filtered_nav_df['date'] - date)
        
        
        # Find the row with the minimum date difference
        closest_row = filtered_nav_df.loc[filtered_nav_df['date_diff'].idxmin()]
        
        # Return closest date and corresponding value
        return pd.Series([closest_row['date'], closest_row['nav']], index=['date', 'nav']) 
    
    def merge_on_closest_date(self,no_nav_df, nav_history):
        
        # Convert the 'date' columns to datetime format
        no_nav_df['date'] = pd.to_datetime(no_nav_df['date'])
        nav_history['date'] = pd.to_datetime(nav_history['date'])
         # Sort by 'date' only
        no_nav_df = no_nav_df.sort_values(by='date')
        nav_history = nav_history.sort_values(by='date')

        # Merge the dataframes using the closest dates
        merged_df = pd.merge_asof(no_nav_df,nav_history,  on='date', direction='nearest')
            
        return merged_df
    
    def merge_schemes_on_closest_date(self,no_nav_df, nav_history):
        
        result_list = []

        # Get unique schemes
        schemes = no_nav_df['scheme'].unique()

        for scheme in schemes:
            no_nav_group = no_nav_df[no_nav_df['scheme'] == scheme]
            nav_history_group = nav_history[nav_history['scheme'] == scheme]
            
            merged_group = self.merge_on_closest_date(no_nav_group, nav_history_group)
            result_list.append(merged_group)

        # Combine all results into a single DataFrame
        result = pd.concat(result_list, ignore_index=True)
        result['date'] = result['date'].apply(lambda x: self.datetime_to_string(x))
        
        return result
        

     