import os
import ast
import json
import time
import requests
import platform
import subprocess
#import pkg_resources


class API_Tools:
    def __init__(self,logger):
        self.logger = logger.info('API Tools Initiated.')
        self.logger = logger.getChild(__name__)
        

    def Rapid_API_calls(self,rapid_api_dict, logger, params=None):
        time.sleep(1)

        url = rapid_api_dict.get("url")
        headers = rapid_api_dict.get("headers")
        self.logger.info(f"Initiating Call for {url}")
        
        try:
            if not headers:
                response = requests.get(url,verify=False)
            elif params:
                response = requests.get(url, headers=headers, params=params, verify=False)
            else:
                response = requests.get(url, headers=headers, verify=False)
            
            if response.status_code == 200:
                logger.info("Status code: {response.status_code}: Rapid API call Successfull")
                response_json = response.json()
                if 'data' in response:
                    response_json = response_json['data']
                return response_json
            else:
                self.handle_status_code(response.status_code)
        except Exception as e:
            logger.info(f"Status code: {response.status_code}: An error occurred: {e}")
                
            
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
