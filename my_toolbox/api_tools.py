"""
    api_tools.py
    This module provides tools for making API calls, specifically designed to work with Rapid API.
    Classes:
        ApiTools: A class that provides methods to make API calls and handle responses.
"""

import time
import requests

class ApiTools:

    """
    A class to handle API calls and responses.
    Methods:
        __init__(logger):
            Initializes the ApiTools class with a logger instance.
        Rapid_API_calls(rapid_api_dict, logger, params=None):
            Makes an API call to the specified URL with given headers and parameters.
        handle_status_code(response_status_code):
            Handles different status codes with appropriate log messages.
    """
    def __init__(self,logger):
        self.logger = logger.info('API Tools Initiated.')
        self.logger = logger.getChild(__name__)

    def rapid_api_calls(self,rapid_api_dict, logger, params=None):

        """
        Makes a call to a Rapid API endpoint with the given parameters and headers.
        Args:
            rapid_api_dict (dict): A dictionary containing the 'url' and 'headers' for the API call.
            logger (logging.Logger): A logger instance to log information and errors.
            params (dict, optional): A dictionary of query parameters to include in the API call. 
            Defaults to None.
        Returns:
            dict: The JSON response from the API call. 
            If the response contains a 'data' field, returns the content of 'data'.
        Raises:
            Exception: If an error occurs during the API call, 
            it logs the error and raises an exception.
        """
        time.sleep(1)
        response_json = ""
        url = rapid_api_dict.get("url")
        headers = rapid_api_dict.get("headers")
        self.logger.info(f"Initiating Call for {url}")
        try:
            if not headers:
                response = requests.get(url,verify=False,timeout=10)
            elif params:
                response = requests.get(url, headers=headers, params=params, verify=False,timeout=10)
            else:
                response = requests.get(url, headers=headers, verify=False,timeout=10)
            if response.status_code == 200:
                logger.info("Status code: {response.status_code}: Rapid API call Successfull")
                response_json = response.json()
                if 'data' in response:
                    response_json = response_json['data']
            else:
                self.handle_status_code(response.status_code)
        except Exception as e:
            logger.info(f"Status code: {response.status_code}: An error occurred: {e}")

        return response_json

    def handle_status_code(self,response_status_code):
        """Handle different status codes with appropriate log messages."""
        status_code_messages = {
            400: "Bad Request: The server could not understand the request.",
            401: "Unauthorized: Access is denied due to invalid credentials.",
            403: "Forbidden: You do not have permission to access this resource.",
            404: "Not Found: The requested resource could not be found.",
            429: "Too Many Requests: You have exceeded the rate limit.",
            500: "Internal Server Error: The server encountered an error."
        }

        if response_status_code in status_code_messages:
            self.logger.info(f"Status code: {response_status_code}: {status_code_messages[response_status_code]}")
        else:
            self.logger.info(f"Status code: {response_status_code}: Unexpected status code")
