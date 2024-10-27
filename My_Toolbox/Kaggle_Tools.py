
import os
import ast
import json
import time
import requests
import platform
import subprocess




class Kaggle_Tools:
    def __init__(self, logger=None,kaggle_dir=None, move_to_read_only=True):
        if logger:
            self.logger = logger.info('Kaggle API is Initiated...')
            self.logger = logger.getChild(__name__)
        if kaggle_dir:
            self.kaggle_dir = kaggle_dir
        else:
            self.kaggle_dir = os.getcwd()
        self.move_to_read_only = move_to_read_only

    def apply(self,dataset_name):
        self.kaggle_auth()
        self.download_dataset(dataset_name)
        
    
    def kaggle_auth(self):
        try:
            if 'KAGGLE_USERNAME' in os.environ and 'KAGGLE_KEY' in os.environ:
                self.logger.info("Kaggle credentials found in environment variables.")
           
            else:
                self.logger.info("Kaggle credentials not found in environment variables.")
                self.logger.info("Proceeding to Credentails Import")
                self.setup_kaggle_credentials()        
            

        except Exception as e:
            self.logger.info(f"Error setting up Kaggle credentials: {e}")
    
        
    def setup_kaggle_credentials(self):
        """Set up Kaggle credentials from the directory if provided, else from environment variables."""
        try:
            self.kaggle_json_path = os.path.join(self.kaggle_dir, 'kaggle.json')
            self.logger.info(self.kaggle_json_path)

            if os.path.exists(self.kaggle_json_path):
                with open(self.kaggle_json_path) as f:
                    kaggle_creds = json.load(f)
                
                os.environ['KAGGLE_USERNAME'],os.environ['KAGGLE_KEY'] = kaggle_creds['username'], kaggle_creds['key']
                
                self.logger.info("Json File Imported and loaded into environment")

                if self.move_to_read_only is not None:
                    self.kaggle_move_to_read_only()
                    self.logger.info(f"Kaggle credentials loaded from {self.kaggle_json_path}")
                else:
                    self.logger.info(f"kaggle.json not moved from {self.kaggle_dir}.")

        except Exception as e:
            self.logger.info(f"Error setting up Kaggle credentials: {e}")
            return False

    def kaggle_move_to_read_only(self):
        try:
            secure_kaggle_dir = os.path.expanduser('~/.kaggle')
            if not os.path.exists(secure_kaggle_dir):
                os.makedirs(secure_kaggle_dir)
            secure_kaggle_json_path = os.path.join(secure_kaggle_dir, 'kaggle.json')

            if platform.system() == "Windows":
                try:                
                    os.rename(self.kaggle_json_path, secure_kaggle_json_path)
                    self.logger.info(f'Moved Kaggle JSON to {secure_kaggle_json_path}')
                except Exception as e:
                    self.logger.info(f'Error moving Kaggle JSON file in Windows: {e}')

                    # Verify that the file has been moved
                    if os.path.exists(secure_kaggle_json_path):
                        self.logger.info(f'Success! The file has been moved to: {secure_kaggle_json_path}')
                    
            else:
                # On Unix-like systems, use chmod
                try:
                    subprocess.run(['mv', self.kaggle_json_path, secure_kaggle_json_path ])
                    subprocess.run(['chmod', '600', secure_kaggle_json_path], check=True)
                    self.logger.info(f'Set permissions for {secure_kaggle_json_path} to 600.')
                except Exception as e:
                    self.logger.info(f'Error setting permissions in UNIX: {e}')
                
            
            self.logger.info(f"Moved kaggle.json to {secure_kaggle_json_path} and set it as readable only by the user.")
            
            if self.kaggle_json_path and os.path.exists(self.kaggle_json_path):
                os.remove(self.kaggle_json_path)
                self.logger.info(f"Removed {self.kaggle_json_path}")
                
        except Exception as e:
            self.logger.info(f"Error Moving or cleaning up Kaggle JSON file: {e}")
            
    def download_dataset(self, dataset_name: str):
        """Download a Kaggle dataset."""
        from kaggle.api.kaggle_api_extended import KaggleApi

        try:
            api = KaggleApi()
            api.authenticate()
            self.logger.info("Successfully authenticated with Kaggle API.")
            api.dataset_download_files(dataset_name, path=os.getcwd(), unzip=True)
            self.logger.info(f"Downloaded dataset: {dataset_name}")
        except Exception as e:
            self.logger.info(f"Error downloading dataset: {e}")
                