import re
import pandas as pd


class String_Functions:
    def __init__(self):
        pass
        
    def convert_frequency(self,frequency):
        frequency_dict = {"monthly": 12,"quarterly": 4}

        try:
            return frequency_dict[frequency.lower()]
        except KeyError:
            return 12
        
    def string_2_text(self,text):
        
    # Replace with your specific pattern to extract numbers (consider symbols and decimals)
         # Extract numbers from relevant columns (assuming specific format)

        try:
            if not isinstance(text, str):  # Check for string type
                return 0  # Return None for non-string inputs

        # Replace with your specific pattern to extract numbers (consider symbols and decimals)
            return float(re.sub(r"[^\d\-+\.]", "", text))  # Extract numbers, ., -, +
        except ValueError:
        # Handle cases where the conversion to float fails (e.g., non-numeric text)
            return None
        
    def string_to_number(self,text, number_type=float):
        """
        Converts a string to a number (int or float).

        Args:
        text (str): The input text to be converted.
        number_type (type): The type of number to convert to (int or float). Default is int.

        Returns:
        int/float: The converted number, or None if conversion fails.
        """
        try:
            if isinstance(text, (int, float)):  # If the input is already a number, return it directly
                return number_type(text)
        
            if not isinstance(text, str) or not isinstance(text, (int, float)):  # Check if the input is a string
                return None
            
            # Extract numbers, ., -, +
            number_str = re.sub(r"[^\d\-+\.]", "", text)
            
            # Convert to the specified number type
            return number_type(number_str)
        except (ValueError, TypeError):
            # Handle cases where conversion fails
            return None

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

    
    
    
     