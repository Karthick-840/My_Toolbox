import os
import json
from kaggle.api.kaggle_api_extended import KaggleApi


def Get_data_from_kaggle():
    # Directory to save the kaggle.json
    kaggle_dir = os.path.join(os.getcwd(), '.kaggle')

    # Create the .kaggle directory if it doesn't exist
    if not os.path.exists(kaggle_dir):
        os.makedirs(kaggle_dir)
        
    # Path to the kaggle.json file
    kaggle_json_path = os.path.join(kaggle_dir, 'kaggle.json')

    # Load credentials from JSON file
    with open('kaggle.json') as f:
        kaggle_creds = json.load(f)
        
    os.environ['KAGGLE_USERNAME'] = kaggle_creds['username']
    os.environ['KAGGLE_KEY'] = kaggle_creds['key']


    # Set the permissions to read-only (Optional but recommended)
    os.chmod(kaggle_json_path, 0o600)


    api = KaggleApi()
    api.authenticate()

    !kaggle datasets download -d kazanova/sentiment140

    os.remove(kaggle_json_path)
    
    zip_file = None
    for file in os.listdir():
        if file.endswith('.zip'):
            zip_file = file
            break
    
    if zip_file:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            extract_dir = os.path.splitext(zip_file)[0]  # Use the zip filename (without extension) as the extraction directory name
            zip_ref.extractall(extract_dir)
            print(f"Extracted {zip_file} to {extract_dir}/")
        else:
            print("No zip file found in the current directory.")
