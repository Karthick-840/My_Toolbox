"""
General-purpose data validation utilities.

Provides functions for validating emails, URLs, JSON schemas, and preventing injection attacks.
"""

import re
from typing import Tuple, Any, Dict, List, Optional
from .error_handling import ValidationError


class Validator:
    """Centralized data validation utilities."""
    
    # Email regex (RFC 5322 simplified)
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # URL regex
    URL_PATTERN = r'^https?://[^\s/$.?#].[^\s]*$'
    
    # Phone number patterns by country
    PHONE_PATTERNS = {
        'US': r'^(\+1)?[-.\s]?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}$',
        'UK': r'^(\+44)?[0-9]{10,11}$',
        'IN': r'^(\+91)?[6-9]\d{9}$',
    }
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            (is_valid, error_message) tuple
            
        Example:
            >>> Validator.validate_email("user@example.com")
            (True, "")
        """
        if not email or not isinstance(email, str):
            return (False, "Email must be a non-empty string")
        
        email = email.strip()
        
        if len(email) > 254:
            return (False, "Email address is too long (max 254 characters)")
        
        if not re.match(Validator.EMAIL_PATTERN, email):
            return (False, "Invalid email format")
        
        return (True, "")
    
    @staticmethod
    def validate_url(url: str, require_https: bool = False) -> Tuple[bool, str]:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            require_https: If True, only allow https://
            
        Returns:
            (is_valid, error_message) tuple
        """
        if not url or not isinstance(url, str):
            return (False, "URL must be a non-empty string")
        
        url = url.strip()
        
        if require_https and not url.startswith('https://'):
            return (False, "HTTPS URLs only")
        
        if not re.match(Validator.URL_PATTERN, url):
            return (False, "Invalid URL format")
        
        return (True, "")
    
    @staticmethod
    def validate_phone(phone: str, country: str = 'US') -> Tuple[bool, str]:
        """
        Validate phone number format by country.
        
        Args:
            phone: Phone number to validate
            country: Country code ('US', 'UK', 'IN')
            
        Returns:
            (is_valid, error_message) tuple
        """
        if not phone or not isinstance(phone, str):
            return (False, "Phone must be a non-empty string")
        
        if country not in Validator.PHONE_PATTERNS:
            return (False, f"Unsupported country code: {country}")
        
        pattern = Validator.PHONE_PATTERNS[country]
        
        if not re.match(pattern, phone):
            return (False, f"Invalid {country} phone format")
        
        return (True, "")
    
    @staticmethod
    def validate_json_schema(
        data: Any, 
        schema: Dict[str, Any], 
        strict: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Validate data against a schema dictionary.
        
        Basic schema format:
        {
            'field_name': {
                'type': 'str' | 'int' | 'float' | 'bool' | 'list' | 'dict',
                'required': True | False,
                'min_length': int,
                'max_length': int,
                'pattern': regex_string,
                'enum': [allowed_values],
            }
        }
        
        Args:
            data: Data to validate (dict)
            schema: Schema dict
            strict: If True, disallow extra fields not in schema
            
        Returns:
            (is_valid, errors_list) tuple
        """
        errors = []
        
        if not isinstance(data, dict):
            return (False, ["Data must be a dictionary"])
        
        # Check required fields and types
        for field_name, field_schema in schema.items():
            required = field_schema.get('required', False)
            field_type = field_schema.get('type', 'str')
            
            if field_name not in data:
                if required:
                    errors.append(f"Required field missing: {field_name}")
                continue
            
            value = data[field_name]
            
            # Type validation
            type_mapping = {
                'str': str,
                'int': int,
                'float': (int, float),
                'bool': bool,
                'list': list,
                'dict': dict,
            }
            
            expected_type = type_mapping.get(field_type)
            if expected_type and not isinstance(value, expected_type):
                errors.append(f"Field '{field_name}' must be {field_type}, got {type(value).__name__}")
                continue
            
            # Length validation (for strings and lists)
            if isinstance(value, (str, list)):
                min_len = field_schema.get('min_length')
                max_len = field_schema.get('max_length')
                
                if min_len is not None and len(value) < min_len:
                    errors.append(f"Field '{field_name}' length must be >= {min_len}")
                
                if max_len is not None and len(value) > max_len:
                    errors.append(f"Field '{field_name}' length must be <= {max_len}")
            
            # Pattern validation (regex for strings)
            pattern = field_schema.get('pattern')
            if pattern and isinstance(value, str):
                if not re.match(pattern, value):
                    errors.append(f"Field '{field_name}' does not match pattern: {pattern}")
            
            # Enum validation
            enum_values = field_schema.get('enum')
            if enum_values and value not in enum_values:
                errors.append(f"Field '{field_name}' must be one of {enum_values}")
        
        # Check for extra fields
        if strict:
            extra_fields = set(data.keys()) - set(schema.keys())
            if extra_fields:
                errors.append(f"Extra fields not in schema: {extra_fields}")
        
        return (len(errors) == 0, errors)
    
    @staticmethod
    def sanitize_input(
        input_str: str, 
        allowed_chars: Optional[str] = None,
        max_length: int = 1000
    ) -> str:
        """
        Sanitize user input to prevent injection attacks.
        
        Args:
            input_str: Input string to sanitize
            allowed_chars: Regex pattern of allowed characters; defaults to alphanumeric + spaces
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
            
        Example:
            >>> Validator.sanitize_input("Hello<script>alert(1)</script>World")
            "HelloscriptalertWorldscript"
        """
        if not isinstance(input_str, str):
            return ""
        
        # Truncate
        input_str = input_str[:max_length]
        
        # Default: allow alphanumeric, spaces, common punctuation
        if allowed_chars is None:
            allowed_chars = r'[a-zA-Z0-9\s\-_.,:;!?()&]'
        
        # Remove disallowed characters
        sanitized = re.sub(f'[^{re.escape(allowed_chars)}]', '', input_str)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_ticker(
        ticker: str, 
        min_length: int = 1, 
        max_length: int = 5
    ) -> Tuple[bool, str]:
        """
        Validate stock ticker symbol format.
        
        Args:
            ticker: Ticker symbol (e.g., "AAPL", "BRK.B")
            min_length: Minimum ticker length
            max_length: Maximum ticker length
            
        Returns:
            (is_valid, error_message) tuple
        """
        if not ticker or not isinstance(ticker, str):
            return (False, "Ticker must be a non-empty string")
        
        ticker = ticker.strip().upper()
        
        if len(ticker) < min_length or len(ticker) > max_length:
            return (False, f"Ticker length must be {min_length}-{max_length} characters")
        
        # Allow alphanumeric and period (for tickers like BRK.B)
        if not re.match(r'^[A-Z0-9.]+$', ticker):
            return (False, "Ticker can only contain uppercase letters, numbers, and periods")
        
        return (True, "")
    
    @staticmethod
    def validate_currency_code(currency_code: str) -> Tuple[bool, str]:
        """
        Validate ISO 4217 currency code (3-letter format).
        
        Args:
            currency_code: Currency code (e.g., "USD", "EUR")
            
        Returns:
            (is_valid, error_message) tuple
        """
        if not currency_code or not isinstance(currency_code, str):
            return (False, "Currency code must be a non-empty string")
        
        currency_code = currency_code.strip().upper()
        
        if len(currency_code) != 3:
            return (False, "Currency code must be 3 characters")
        
        if not re.match(r'^[A-Z]{3}$', currency_code):
            return (False, "Currency code must contain only uppercase letters")
        
        return (True, "")


# Convenience functions for direct import
def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email address."""
    return Validator.validate_email(email)


def validate_url(url: str, require_https: bool = False) -> Tuple[bool, str]:
    """Validate URL."""
    return Validator.validate_url(url, require_https)


def validate_phone(phone: str, country: str = 'US') -> Tuple[bool, str]:
    """Validate phone number."""
    return Validator.validate_phone(phone, country)


def validate_json_schema(
    data: Any, 
    schema: Dict[str, Any], 
    strict: bool = False
) -> Tuple[bool, List[str]]:
    """Validate data against schema."""
    return Validator.validate_json_schema(data, schema, strict)


def sanitize_input(
    input_str: str, 
    allowed_chars: Optional[str] = None,
    max_length: int = 1000
) -> str:
    """Sanitize user input."""
    return Validator.sanitize_input(input_str, allowed_chars, max_length)
