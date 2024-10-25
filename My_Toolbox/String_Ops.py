import re
import pandas as pd

class String_Functions:
    def __init__(self,logger=None):
        if logger:
            self.logger = logger.info('String Manipulation Tools Initiated.')
            self.logger = logger.getChild(__name__)
        
    def convert_frequency(self,frequency):
        frequency_dict = {"monthly": 12,"quarterly": 4}

        try:
            return frequency_dict[frequency.lower()]
        except KeyError:
            return 12
        
    
    def string_2_num(self, text, number_type=float):
        try:
            # If the input is a string or object, process it
            if isinstance(text, (str, object)) or not isinstance(text, (int,float)):
                # Replace commas in the number, if any
                #text = text.replace(",", "")
                # Remove non-numeric characters except digits, ., -, and +
                number_str = re.sub(r"[^\d\-+\.]", "", text)
                
                # Check if the result is a valid number
                if number_str:
                    return number_type(number_str)  # Convert to the desired type
                
            # If it's already a number, return it as-is
            return number_type(text)
        
        except (ValueError, TypeError):
            # Return None or some default value on failure to convert
            return text



    def number_to_string(self,number):
        """
        Converts a number to a string.

        Args:
        number (int/float): The number to be converted.

        Returns:
        str: The number as a string, or an empty string if the input is not a number.
        """
        try:
            if isinstance(number, (int, float)):  # Check if the input is a number
                return str(number)
            else:
                return ""
        except (ValueError, TypeError):
            # Handle cases where conversion fails
            return ""
        
    def summarize(self,df,summary_col,aggregate_dicts):
    
        def get_mode(x):
            return x.mode().iloc[0] 

        def get_mean_rounded(series):
            return round(series.mean(), 2)

        # Define a dictionary to map functions
        function_mapping = {'mode': get_mode,'mean':get_mean_rounded}

        # Perform groupby and aggregation
        summary_df = df.groupby(
            summary_col).agg(
            {col: function_mapping.get(func, func) for col, func in aggregate_dicts.items()}).reset_index()

        return summary_df

    
    
    
     
    
     