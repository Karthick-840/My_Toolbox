import re
from typing import Tuple, Optional, Any, Union
from difflib import SequenceMatcher


class StringFunctions:
    """
    Comprehensive string manipulation and parsing utilities.
    Supports robust number parsing, currency handling, and text analysis.
    """
    
    CURRENCY_SYMBOLS = {
        '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', 
        '₹': 'INR', '₽': 'RUB', '¢': 'USD', 'C$': 'CAD'
    }
    
    MAGNITUDE_MULTIPLIERS = {
        'K': 1_000, 'k': 1_000,
        'M': 1_000_000, 'm': 1_000_000,
        'B': 1_000_000_000, 'b': 1_000_000_000,
        'T': 1_000_000_000_000, 't': 1_000_000_000_000,
    }
    
    def __init__(self, logger=None):
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
        
    def summarize(self, df, summary_col, aggregate_dicts):
        """
        Group a DataFrame by a column and aggregate using specified functions.
        
        Args:
            df: pandas DataFrame
            summary_col: Column name to group by
            aggregate_dicts: Dict mapping column names to aggregation functions ('mode', 'mean', etc.)
            
        Returns:
            Summarized DataFrame
        """
        def get_mode(x):
            return x.mode().iloc[0] if len(x.mode()) > 0 else None

        def get_mean_rounded(series):
            return round(series.mean(), 2)

        function_mapping = {'mode': get_mode, 'mean': get_mean_rounded}

        summary_df = df.groupby(
            summary_col).agg(
            {col: function_mapping.get(func, func) for col, func in aggregate_dicts.items()}).reset_index()

        return summary_df
    
    # ===== NEW ROBUST PARSING FUNCTIONS =====
    
    def safe_parse_number(
        self, 
        value: Any, 
        locale: str = 'US', 
        precision: Optional[int] = 2,
        default: Optional[float] = None
    ) -> Tuple[Optional[float], str, bool]:
        """
        Robustly parse a number from various formats.
        
        Handles: "$1,234.56", "€1.234,50", "-50%", "1.5K", "2.3M", "N/A", None
        
        Args:
            value: Input value (string, int, float, or None)
            locale: 'US' (1,234.56) or 'EU' (1.234,56)
            precision: Decimal precision to validate; None = no validation
            default: Default value if parsing fails
            
        Returns:
            (parsed_value, original_str, is_valid) tuple
            
        Examples:
            >>> sf.safe_parse_number("$1,234.56", locale="US")
            (1234.56, "$1,234.56", True)
            >>> sf.safe_parse_number("N/A", default=0)
            (0, "N/A", False)
        """
        original_str = str(value) if value is not None else ""
        
        # Handle None, empty, or non-numeric strings
        if value is None or original_str.strip() in ['', 'N/A', 'na', 'None', 'null']:
            return (default, original_str, False)
        
        try:
            # Already numeric
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                parsed = float(value)
                return (parsed, original_str, True)
            
            # String parsing
            text = str(value).strip()
            
            # Check for percentage
            is_negative = '-' in text or '(' in text  # Parentheses = negative in accounting
            
            # Remove currency symbols and whitespace
            for symbol in self.CURRENCY_SYMBOLS.keys():
                text = text.replace(symbol, '')
            
            # Remove other common symbols
            text = text.replace('(', '').replace(')', '').replace('%', '').strip()
            
            # Handle magnitude (K, M, B, T)
            multiplier = 1.0
            for mag, mult in self.MAGNITUDE_MULTIPLIERS.items():
                if text.lower().endswith(mag):
                    text = text[:-1].strip()
                    multiplier = mult
                    break
            
            # Detect locale-based decimal separator
            if locale.upper() == 'EU':
                # European: 1.234,56 → 1234.56
                text = text.replace('.', '')  # Remove thousand separator
                text = text.replace(',', '.')  # Convert decimal comma to period
            else:
                # US: 1,234.56 → 1234.56
                text = text.replace(',', '')  # Remove thousand separator
            
            # Extract numeric part (allow +, -)
            numeric_match = re.match(r'^[+-]?\d+\.?\d*$', text)
            if not numeric_match:
                return (default, original_str, False)
            
            parsed = float(text) * multiplier
            
            # Apply sign
            if is_negative and parsed > 0:
                parsed = -parsed
            
            return (parsed, original_str, True)
        
        except (ValueError, TypeError, AttributeError):
            return (default, original_str, False)
    
    def parse_currency(
        self, 
        value: Any, 
        currency_code: str = 'USD'
    ) -> Tuple[Optional[float], Optional[str], bool]:
        """
        Parse currency-aware values, detecting symbol and sign.
        
        Args:
            value: Currency string (e.g., "$1,234.56", "-€100", "(£50)")
            currency_code: Expected currency code (for validation)
            
        Returns:
            (amount, detected_currency, is_negative) tuple
            
        Example:
            >>> sf.parse_currency("($1,234.56)")
            (1234.56, 'USD', True)
        """
        text = str(value).strip() if value else ""
        detected_currency = None
        is_negative = False
        
        # Detect currency symbol
        for symbol, code in self.CURRENCY_SYMBOLS.items():
            if symbol in text:
                detected_currency = code
                text = text.replace(symbol, '')
                break
        
        # Detect negative (minus or parentheses)
        if '-' in text or text.startswith('('):
            is_negative = True
            text = text.replace('-', '').replace('(', '').replace(')', '')
        
        # Parse the number
        parsed, _, valid = self.safe_parse_number(text)
        
        if valid and is_negative and parsed is not None:
            parsed = -parsed
        
        return (parsed, detected_currency, is_negative)
    
    def validate_number(
        self, 
        value: Any, 
        min_val: Optional[float] = None, 
        max_val: Optional[float] = None, 
        allow_negative: bool = True,
        allow_zero: bool = True
    ) -> Tuple[bool, str]:
        """
        Validate if a value is numeric and within bounds.
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value (inclusive)
            max_val: Maximum allowed value (inclusive)
            allow_negative: Whether to allow negative values
            allow_zero: Whether to allow zero
            
        Returns:
            (is_valid, error_message) tuple
            
        Example:
            >>> sf.validate_number(50, min_val=0, max_val=100)
            (True, "")
        """
        try:
            parsed, _, is_valid = self.safe_parse_number(value)
            
            if not is_valid or parsed is None:
                return (False, "Value is not numeric")
            
            if not allow_negative and parsed < 0:
                return (False, "Negative values not allowed")
            
            if not allow_zero and parsed == 0:
                return (False, "Zero is not allowed")
            
            if min_val is not None and parsed < min_val:
                return (False, f"Value {parsed} is below minimum {min_val}")
            
            if max_val is not None and parsed > max_val:
                return (False, f"Value {parsed} exceeds maximum {max_val}")
            
            return (True, "")
        
        except Exception as e:
            return (False, str(e))
    
    def format_number(
        self, 
        value: float, 
        decimals: int = 2, 
        prefix: str = '', 
        suffix: str = '',
        locale: str = 'US',
        use_magnitude: bool = False
    ) -> str:
        """
        Format a number as a string with optional grouping, prefix, suffix.
        
        Args:
            value: Number to format
            decimals: Decimal places to display
            prefix: Prefix (e.g., '$', '€')
            suffix: Suffix (e.g., '%', ' USD')
            locale: 'US' (1,234.56) or 'EU' (1.234,56)
            use_magnitude: Use K/M/B/T suffix for large numbers
            
        Returns:
            Formatted string
            
        Example:
            >>> sf.format_number(1234567.89, decimals=2, prefix="$", locale="US")
            '$1,234,567.89'
        """
        if value is None:
            return "N/A"
        
        try:
            # Apply magnitude suffix if requested
            if use_magnitude:
                abs_val = abs(value)
                if abs_val >= 1_000_000_000:
                    formatted = f"{value / 1_000_000_000:.{decimals}f}B"
                elif abs_val >= 1_000_000:
                    formatted = f"{value / 1_000_000:.{decimals}f}M"
                elif abs_val >= 1_000:
                    formatted = f"{value / 1_000:.{decimals}f}K"
                else:
                    formatted = f"{value:.{decimals}f}"
            else:
                formatted = f"{value:.{decimals}f}"
            
            # Apply locale-specific grouping
            if locale.upper() == 'EU':
                # European: 1.234,56
                parts = formatted.split('.')
                integer_part = parts[0]
                decimal_part = parts[1] if len(parts) > 1 else "00"
                integer_grouped = '.'.join([integer_part[max(0, i-3):i] 
                                           for i in range(len(integer_part), 0, -3)][::-1])
                formatted = f"{integer_grouped},{decimal_part}"
            else:
                # US: 1,234.56
                parts = formatted.split('.')
                integer_part = parts[0]
                decimal_part = parts[1] if len(parts) > 1 else "00"
                integer_grouped = ','.join([integer_part[max(0, i-3):i] 
                                           for i in range(len(integer_part), 0, -3)][::-1])
                formatted = f"{integer_grouped}.{decimal_part}"
            
            return f"{prefix}{formatted}{suffix}"
        
        except Exception:
            return "N/A"
    
    def text_similarity(
        self, 
        str1: str, 
        str2: str, 
        threshold: float = 0.8
    ) -> Tuple[float, bool]:
        """
        Compute text similarity ratio and check if above threshold.
        
        Useful for matching ticker symbols, company names with typos.
        
        Args:
            str1: First string
            str2: Second string
            threshold: Similarity threshold (0-1)
            
        Returns:
            (similarity_ratio, is_similar) tuple
            
        Example:
            >>> sf.text_similarity("Apple Inc.", "AAPL")
            (0.22, False)
        """
        if not str1 or not str2:
            return (0.0, False)
        
        # Normalize strings
        s1 = str(str1).lower().strip()
        s2 = str(str2).lower().strip()
        
        # Compute ratio using SequenceMatcher
        ratio = SequenceMatcher(None, s1, s2).ratio()
        
        return (ratio, ratio >= threshold)
    
     