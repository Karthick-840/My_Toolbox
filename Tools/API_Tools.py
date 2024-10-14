import time
import requests
import time
import os
import json
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi
import subprocess

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

class Kaggle_Tools:
    def __init__(self, logger,kaggle_dir=None, move_to_read_only=False):
        self.logger = logger.info('Kaggle Data downloading...')
        self.logger = logger.getChild(__name__)
        if kaggle_dir:
            self.kaggle_dir = kaggle_dir
        if move_to_read_only:
            self.move_to_read_only = move_to_read_only

    def kaggle_auth(self):
        try:
            if 'KAGGLE_USERNAME' in os.environ and 'KAGGLE_KEY' in os.environ:
                print("Kaggle credentials found in environment variables.")
           
            else:
                print("Kaggle credentials not found in environment variables.")
                print("Proceeding to Credentails Import")
                self.setup_kaggle_credentials(self.kaggle_dir,self.move_to_read)        
            

        except Exception as e:
            print(f"Error setting up Kaggle credentials: {e}")
    
        
    def setup_kaggle_credentials(self):
        """Set up Kaggle credentials from the directory if provided, else from environment variables."""
        try:
            self.kaggle_json_path = os.path.join(self.kaggle_dir, 'kaggle.json')

            if os.path.exists(self.kaggle_json_path):
                with open(self.kaggle_json_path) as f:
                    kaggle_creds = json.load(f)

                os.environ['KAGGLE_USERNAME'],os.environ['KAGGLE_KEY'] = kaggle_creds['username'], kaggle_creds['key']
                    
                if self.move_to_read_only:
                    self.kaggle_move_to_read_only()
                    print(f"Kaggle credentials loaded from {self.kaggle_json_path}")
                else:
                    print(f"No kaggle.json file found in {self.kaggle_dir}.")

        except Exception as e:
            print(f"Error setting up Kaggle credentials: {e}")
            return False

    def kaggle_move_to_read_only(self):
        try:
            secure_kaggle_dir = os.path.expanduser('~/.kaggle')
            if not os.path.exists(secure_kaggle_dir):
                os.makedirs(secure_kaggle_dir)
                
            secure_kaggle_json_path = os.path.join(secure_kaggle_dir, 'kaggle.json')
            subprocess.run(['mv', self.kaggle_json_path, secure_kaggle_json_path ])
            subprocess.run(['chmod', '600', secure_kaggle_json_path])
            
            print(f"Moved kaggle.json to {secure_kaggle_json_path} and set it as readable only by the user.")
            
            if self.kaggle_json_path and os.path.exists(self.kaggle_json_path):
                os.remove(self.kaggle_json_path)
                print(f"Removed {self.kaggle_json_path}")
                
        except Exception as e:
            print(f"Error Moving or cleaning up Kaggle JSON file: {e}")
            
    def download_dataset(self, dataset_name: str):
        """Download a Kaggle dataset."""
        try:
            api = KaggleApi()
            api.authenticate()
            print("Successfully authenticated with Kaggle API.")
            api.dataset_download_files(dataset_name, path=os.getcwd(), unzip=False)
            print(f"Downloaded dataset: {dataset_name}")
        except Exception as e:
            print(f"Error downloading dataset: {e}")
                

# # NOTION TOOLS

# # Prerequesit Create Notion Integration
# # Create a database in Notion and share to get the database ID - https://www.youtube.com/watch?v=M1gu9MDucMA&list=PLe0U7sHuld_qIILgg-2ESRCPWu-WBalFJ&index=42
# """
# How to set up the Notion API
# How to set up the Python code
# How to create database entries
# How to query the database
# How to update database entries
# And how to delete entries.

# """

# import requests
# from datetime import datetime, timezone

# NOTION_TOKEN = ""
# DATABASE_ID = ""

# headers = {
#     "Authorization": "Bearer "+NOTION_TOKEN,
#     "Content-Type": "application/json",
#     "Notion-Version": "2024-06-28"
# }

# #Creating pages in your Notion database
# def create_page(data: dict):
#     create_url = "https://api.notion.com/v1/pages"

#     payload = {"parent": {"database_id": DATABASE_ID}, "properties": data}

#     res = requests.post(create_url, headers=headers, json=payload)
#     # print(res.status_code)
#     return res

# from datetime import datetime, timezone

# title = "Test Title"
# description = "Test Description"
# published_date = datetime.now().astimezone(timezone.utc).isoformat()
# data = {
#     "URL": {"title": [{"text": {"content": description}}]},
#     "Title": {"rich_text": [{"text": {"content": title}}]},
#     "Published": {"date": {"start": published_date, "end": None}}
# }
# https://developers.notion.com/reference/intro
# create_page(data)
# The corresponding data fields have to correspond to your table column names.

# The schema might look a bit complicated and differs for different data types (e.g. text, date, boolean etc.). To determine the exact schema, I recommend dumping the data (see next step) and inspecting the JSON file.

# In our example, we create data for the URL, the Title, and the Published columns like so:

# def get_pages(num_pages=None):
#     """
#     If num_pages is None, get all pages, otherwise just the defined number.
#     """
#     url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

#     get_all = num_pages is None
#     page_size = 100 if get_all else num_pages

#     payload = {"page_size": page_size}
#     response = requests.post(url, json=payload, headers=headers)

#     data = response.json()

#     # Comment this out to dump all data to a file
#     # import json
#     # with open('db.json', 'w', encoding='utf8') as f:
#     #    json.dump(data, f, ensure_ascii=False, indent=4)

#     results = data["results"]
#     while data["has_more"] and get_all:
#         payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
#         url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
#         response = requests.post(url, json=payload, headers=headers)
#         data = response.json()
#         results.extend(data["results"])

#     return results

# Querying Notion database and reading pages¶
# To query your database and read all entries, we can use the following function. It uses pagination to retrieve all entries:
# pages = get_pages()

# for page in pages:
#     page_id = page["id"]
#     props = page["properties"]
#     url = props["URL"]["title"][0]["text"]["content"]
#     title = props["Title"]["rich_text"][0]["text"]["content"]
#     published = props["Published"]["date"]["start"]
#     published = datetime.fromisoformat(published)
    
# Updating pages in your Notion databse¶
# To update a page, we have to send a PATCH request:

# def update_page(page_id: str, data: dict):
#     url = f"https://api.notion.com/v1/pages/{page_id}"

#     payload = {"properties": data}

#     res = requests.patch(url, json=payload, headers=headers)
#     return res
# For example, if we want to update the Published field, we send the following data. It is the same schema as for creating the page:
    
    

# update_page(page_id, update_data)

# Deleting pages in your Notion database¶
# Deleting a page is achieved with the same endpoint as for updating the page, but here we set the archived parameter to True:

# def delete_page(page_id: str):
#     url = f"https://api.notion.com/v1/pages/{page_id}"

#     payload = {"archived": True}

#     res = requests.patch(url, json=payload, headers=headers)
#     return res