import pytest
import requests
from unittest.mock import Mock, patch, mock_open, MagicMock
import os

from My_Toolbox.API_Tools import API_Tools
#from My_Toolbox.API_Tools import Kaggle_Tools, Git_Tools  # Replace 'your_module' with the actual module name

@pytest.fixture
def api_tools(logger):
    return API_Tools(logger)

def test_rapid_api_calls(api_tools, logger):
    mock_rapid_api_dict = {"url": "https://mockurl.com", "headers": {"Authorization": "mock_key"}}
    
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "response_data"}
        mock_get.return_value = mock_response
        
        result = api_tools.Rapid_API_calls(mock_rapid_api_dict, logger)
        assert result == {"data": "response_data"}
        logger.info.assert_called_with("Status code: {response.status_code}: Rapid API call Successfull")
    
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = api_tools.Rapid_API_calls(mock_rapid_api_dict, logger)
        assert result is None
        logger.info.assert_any_call("Status code: 404: Not Found: The requested resource could not be found.")

def test_handle_status_code(api_tools):
    api_tools.handle_status_code(400)
    api_tools.logger.info.assert_called_with("Status code: 400: Bad Request: The server could not understand the request.")

