import os
import json
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from My_Toolbox.Finance_Tools import Finance_Tools  # Replace 'your_module' with the actual module name


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = MagicMock()
    return logger


@pytest.fixture
def sample_yahoo_summary():
    """Create a sample DataFrame for testing."""
    data = {
        'Yahoo_Ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'Security_Status': ['Active', 'Active', 'Sold'],
        'min_start': [pd.Timestamp.now(), pd.Timestamp.now(), pd.Timestamp.now()],
        'max_end': [pd.Timestamp.now(), pd.Timestamp.now(), pd.Timestamp.now()]
    }
    return pd.DataFrame(data)


@pytest.fixture
def finance_tools(mock_logger):
    """Create a Finance_Tools instance for testing."""
    return Finance_Tools(logger=mock_logger)


@patch('yfinance.Ticker')
def test_get_yfinance_info(mock_ticker, finance_tools, sample_yahoo_summary):
    """Test the Get_yfinance_info method."""
    # Set up the mock ticker
    mock_instance = mock_ticker.return_value
    mock_instance.history.return_value = pd.DataFrame({
        'Date': [pd.Timestamp('2022-01-01'), pd.Timestamp('2022-01-02')],
        'Close': [150, 155],
        'Dividends': [0, 0],
        'Stock Splits': [0, 0]
    })

    mock_instance.info = {'longName': 'Apple Inc.'}

    # Call the method
    history = finance_tools.Get_yfinance_info(sample_yahoo_summary, 'SIP', '.', 'get_history')

    # Verify results
    assert len(history) == 1  # Should only process one active ticker
    assert 'Yahoo_Ticker' in history[0]
    assert history[0]['Yahoo_Ticker'] == 'AAPL'  # Check if AAPL is processed

    # Verify logging
    mock_logger.info.assert_any_call('Initiating Yfinance Data Import.')
    mock_logger.info.assert_any_call('Query for AAPL data between', any='value')  # Check log message


@patch('yfinance.Ticker')
def test_fetch_ticker_data(mock_ticker, finance_tools):
    """Test the fetch_ticker_data method."""
    # Set up the mock ticker
    mock_instance = mock_ticker.return_value
    mock_instance.history.return_value = pd.DataFrame({
        'Date': [pd.Timestamp('2022-01-01'), pd.Timestamp('2022-01-02')],
        'Close': [150, 155],
        'Dividends': [0, 0],
        'Stock Splits': [0, 0]
    })

    mock_instance.info = {'longName': 'Apple Inc.'}

    sample_row = {
        'Yahoo_Ticker': 'AAPL',
        'min_start': pd.Timestamp.now(),
        'max_end': pd.Timestamp.now()
    }

    result = finance_tools.fetch_ticker_data(sample_row, 'SIP', '.')

    # Verify results
    assert result['Yahoo_Ticker'] == 'AAPL'
    assert 'info' in result
    assert len(result['prices']) == 2  # Two rows of historical data

    # Verify logging
    finance_tools.logger.info.assert_any_call('Query for AAPL data between', any='value')  # Check log message


@patch('yfinance.Ticker')
def test_include_stamp_duty(finance_tools):
    """Test Include_stamp_duty method."""
    # Test cases
    assert finance_tools.Include_stamp_duty(1000, '2021-06-30') == 1000.0  # Before stamp duty date
    assert finance_tools.Include_stamp_duty(1000, '2021-07-02') == 999.95  # After stamp duty date


@patch('yfinance.Ticker')
def test_get_yfinance_info_unavailable(mock_ticker, finance_tools, sample_yahoo_summary):
    """Test the Get_yfinance_info method with unavailable tickers."""
    # Mock behavior to simulate an error
    mock_ticker.side_effect = Exception("Ticker not found")

    # Call the method
    history = finance_tools.Get_yfinance_info(sample_yahoo_summary, 'SIP', '.', 'get_history')

    # Verify results
    assert len(history) == 0  # Should not process any tickers due to the exception
    finance_tools.logger.info.assert_any_call('Securities unavailable:', any='value')  # Check log message


# Add more tests as needed...

if __name__ == "__main__":
    pytest.main()
