from datetime import datetime, timedelta
from typing import Tuple, Optional, List, Dict
import pandas as pd


class DateFunctions:
    """
    Comprehensive date manipulation with business logic (fiscal periods, holidays, etc.)
    """
    
    # US holidays (expandable for other regions)
    US_HOLIDAYS = {
        'New Year': (1, 1),
        'MLK Day': (1, 3),  # 3rd Monday (approximate)
        'Presidents Day': (2, 3),  # 3rd Monday
        'Memorial Day': (5, -1),  # Last Monday
        'Independence Day': (7, 4),
        'Labor Day': (9, 1),  # 1st Monday
        'Columbus Day': (10, 2),  # 2nd Monday
        'Veterans Day': (11, 11),
        'Thanksgiving': (11, 4),  # 4th Thursday
        'Christmas': (12, 25),
    }

    def __init__(self, logger=None):
        self.today_str = datetime.today().strftime('%Y-%m-%d')
        self.logger = None
        if logger:
            logger.info('Date Manipulation Tools Initiated.')
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
        
    
    def get_next_business_day(self, date, holidays: Optional[List[datetime]] = None):
        """
        Get next business day (Monday-Friday), skipping weekends and optional holidays.
        
        Args:
            date: Date string or datetime object
            holidays: Optional list of holiday dates to skip
            
        Returns:
            Next business day as string (YYYY-MM-DD)
        """
        if isinstance(date, str):
            date = self.string_to_datetime(date, format='%Y-%m-%d')
        
        if date is None:
            return None
        
        # Start from the next day
        next_date = date + timedelta(days=1)
        
        # Skip weekends and holidays
        while next_date.weekday() >= 5 or (holidays and next_date in holidays):
            next_date += timedelta(days=1)
        
        return next_date.strftime("%Y-%m-%d")
        
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
        no_nav_df.loc[:, 'date'] = pd.to_datetime(no_nav_df['date'])
        nav_history.loc[:, 'date'] = pd.to_datetime(nav_history['date'])

        
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
    
    # ===== NEW FISCAL PERIOD UTILITIES =====
    
    def get_fiscal_period(
        self, 
        date: Optional[str] = None, 
        fiscal_year_start_month: int = 1
    ) -> Tuple[int, int, int]:
        """
        Get fiscal year, fiscal quarter, and fiscal month for a date.
        
        Args:
            date: Date string (YYYY-MM-DD); defaults to today
            fiscal_year_start_month: Month when fiscal year starts (1=Jan, 7=July, etc.)
            
        Returns:
            (fiscal_year, fiscal_quarter, fiscal_month) tuple
            
        Example:
            >>> df.get_fiscal_period("2023-05-15", fiscal_year_start_month=1)
            (2023, 2, 5)  # Fiscal Q2, month 5 of fiscal year
            
            >>> df.get_fiscal_period("2023-05-15", fiscal_year_start_month=7)
            (2022, 4, 11)  # Fiscal year starts July; May is in previous FY
        """
        if date is None:
            dt = datetime.today()
        else:
            dt = self.string_to_datetime(date, format='%Y-%m-%d')
        
        if dt is None:
            return (None, None, None)
        
        # Calculate fiscal year
        calendar_year = dt.year
        calendar_month = dt.month
        
        if calendar_month >= fiscal_year_start_month:
            fiscal_year = calendar_year + 1
            fiscal_month = calendar_month - fiscal_year_start_month + 1
        else:
            fiscal_year = calendar_year
            fiscal_month = calendar_month + (12 - fiscal_year_start_month + 1)
        
        # Calculate fiscal quarter (0-based to 1-based)
        fiscal_quarter = (fiscal_month - 1) // 3 + 1
        
        return (fiscal_year, fiscal_quarter, fiscal_month)
    
    def align_to_period_end(
        self, 
        date: str, 
        period: str = 'quarter', 
        fiscal_year_start_month: int = 1
    ) -> str:
        """
        Round date to the end of a fiscal period (quarter or year end).
        
        Args:
            date: Date string (YYYY-MM-DD)
            period: 'quarter' or 'year'
            fiscal_year_start_month: Month when fiscal year starts
            
        Returns:
            Period end date as string (YYYY-MM-DD)
            
        Example:
            >>> df.align_to_period_end("2023-05-15", period="quarter", fiscal_year_start_month=1)
            "2023-06-30"  # Q2 end
        """
        dt = self.string_to_datetime(date, format='%Y-%m-%d')
        if dt is None:
            return None
        
        fy, fq, _ = self.get_fiscal_period(date, fiscal_year_start_month)
        
        if period.lower() == 'quarter':
            # Calculate end date of fiscal quarter
            # Quarter 1 ends in (fiscal_start + 2 months)
            quarter_end_month = fiscal_year_start_month + (fq * 3 - 1)
            if quarter_end_month > 12:
                quarter_end_month -= 12
                # Find year
                if quarter_end_month >= fiscal_year_start_month:
                    year = fy
                else:
                    year = fy - 1
            else:
                year = fy - 1
            
            # Get last day of the month
            if quarter_end_month == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, quarter_end_month + 1, 1)
            
            period_end = next_month - timedelta(days=1)
        
        elif period.lower() == 'year':
            # Fiscal year ends one day before start of next fiscal year
            next_fy_start = datetime(fy, fiscal_year_start_month, 1) - timedelta(days=1)
            period_end = next_fy_start
        
        else:
            return None
        
        return period_end.strftime('%Y-%m-%d')
    
    def date_range_generator(
        self, 
        start_date: str, 
        end_date: str, 
        period: str = 'daily', 
        exclude_weekends: bool = False, 
        holidays: Optional[List[str]] = None
    ) -> List[str]:
        """
        Generate a sequence of dates between start and end.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
            exclude_weekends: Skip Sat/Sun if True
            holidays: List of holiday dates to skip (YYYY-MM-DD format)
            
        Returns:
            List of dates as strings
            
        Example:
            >>> df.date_range_generator("2023-01-01", "2023-01-10", period="daily")
            ['2023-01-01', '2023-01-02', ..., '2023-01-10']
        """
        start = self.string_to_datetime(start_date)
        end = self.string_to_datetime(end_date)
        
        if start is None or end is None:
            return []
        
        holiday_set = set()
        if holidays:
            holiday_set = {self.string_to_datetime(h) for h in holidays}
        
        dates = []
        current = start
        
        while current <= end:
            # Check if should include this date
            skip = False
            if exclude_weekends and current.weekday() >= 5:
                skip = True
            if current in holiday_set:
                skip = True
            
            if not skip:
                dates.append(current.strftime('%Y-%m-%d'))
            
            # Increment based on period
            if period == 'daily':
                current += timedelta(days=1)
            elif period == 'weekly':
                current += timedelta(weeks=1)
            elif period == 'monthly':
                month = current.month + 1
                year = current.year
                if month > 12:
                    month = 1
                    year += 1
                current = current.replace(year=year, month=month)
            elif period == 'quarterly':
                current += timedelta(days=90)  # Approximate
            elif period == 'yearly':
                current = current.replace(year=current.year + 1)
            else:
                break
        
        return dates
    
    def is_business_day(
        self, 
        date: str, 
        holidays: Optional[List[str]] = None
    ) -> bool:
        """
        Check if a date is a business day (Monday-Friday, not a holiday).
        
        Args:
            date: Date string (YYYY-MM-DD)
            holidays: List of holiday dates (YYYY-MM-DD format)
            
        Returns:
            True if business day, False otherwise
        """
        dt = self.string_to_datetime(date, format='%Y-%m-%d')
        if dt is None:
            return False
        
        # Check if weekend
        if dt.weekday() >= 5:
            return False
        
        # Check if holiday
        if holidays:
            if date in holidays:
                return False
        
        return True
    
    def quarters_between(
        self, 
        start_date: str, 
        end_date: str, 
        fiscal_year_start_month: int = 1
    ) -> int:
        """
        Count fiscal quarters between two dates.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            fiscal_year_start_month: Month when fiscal year starts
            
        Returns:
            Number of quarters between dates (inclusive of end quarter)
            
        Example:
            >>> df.quarters_between("2023-03-31", "2023-12-31", fiscal_year_start_month=1)
            3  # Q2, Q3, Q4
        """
        start_fy, start_q, _ = self.get_fiscal_period(start_date, fiscal_year_start_month)
        end_fy, end_q, _ = self.get_fiscal_period(end_date, fiscal_year_start_month)
        
        if start_fy is None or end_fy is None:
            return 0
        
        quarters = (end_fy - start_fy) * 4 + (end_q - start_q) + 1
        return max(0, quarters)
    
    def validate_date_range(
        self, 
        start_date: str, 
        end_date: str, 
        max_days: int = 365 * 5, 
        min_days: int = 1
    ) -> Tuple[bool, str]:
        """
        Validate that date range is sensible (not too large/small, proper order).
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            max_days: Maximum allowed range in days
            min_days: Minimum allowed range in days
            
        Returns:
            (is_valid, error_message) tuple
            
        Example:
            >>> df.validate_date_range("2023-01-01", "2023-12-31")
            (True, "")
        """
        start = self.string_to_datetime(start_date)
        end = self.string_to_datetime(end_date)
        
        if start is None:
            return (False, f"Invalid start date: {start_date}")
        if end is None:
            return (False, f"Invalid end date: {end_date}")
        
        if start > end:
            return (False, f"Start date {start_date} is after end date {end_date}")
        
        days_diff = (end - start).days
        
        if days_diff < min_days:
            return (False, f"Range is {days_diff} days, minimum is {min_days}")
        
        if days_diff > max_days:
            return (False, f"Range is {days_diff} days, maximum is {max_days}")
        
        return (True, "")
        

     