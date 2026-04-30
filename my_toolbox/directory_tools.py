
"""
Module: directory_tools
This module provides tools for data storage and manipulation, as well as handling ZIP files. 
It includes functionalities for uploading, saving, and retrieving file information, 
as well as extracting ZIP files.

"""
import os
import json
import datetime
import zipfile
import pandas as pd

class DataStorage:
    """
    A class used to handle data storage operations such as uploading, saving, and retrieving file information.
    Data_Storage: Provides methods for uploading, saving, and retrieving file information.
    Zip_Tools: Provides methods for extracting ZIP files.
    -------
    """
    
    def __init__(self,logger=None):
        if logger:
            self.logger = logger.info('Data Storage Tools Initiated.')
            self.logger = logger.getChild(__name__)
       
    def import_files(self, filepath): 
        """
        Imports data from a file into a pandas DataFrame.
        Parameters:
        filepath (str): The path to the file to be imported.
        Returns:
        pd.DataFrame: A DataFrame containing the data from the file. Returns an empty DataFrame if the file is not found or has an unsupported extension.
        Supported file types:
        - CSV (.csv)
        - Text (.txt)
        - JSON (.json)
        """
        df = pd.DataFrame()  
        try:
            extension = filepath.split(".")[-1].lower()

            if extension == "csv":
                df = pd.read_csv(filepath, delimiter=',',skip_blank_lines=True)  # Use comma for CSV
            elif extension == "txt":
                df = pd.read_csv(filepath, delimiter='\t', skip_blank_lines=True, skipinitialspace=True)  # Use tab for TXT
            elif extension == "json":
                df = pd.read_json(filepath)  # Read JSON file into a DataFrame
            else:
                raise ValueError(f"Unsupported file extension: {extension}")
        except  FileNotFoundError:
            self.logger.info(f"Error: File not found at {filepath}")                
            
        except ValueError as e:
            self.logger.info(str(e))
            return df  # Return the empty DataFrame in case of an unsupported file type

        self.logger.info(f'{extension} file found & {filepath} is read to dataframe.')
        df = df.dropna(how='all') 
        return df
    
    def save_files(self, data, filepath, mode='w'):
        """
        Save data to a specified file path in various formats (CSV, TXT, JSON, Excel).
        Parameters:
        data (dict or list): The data to be saved.
        filepath (str): The path where the file will be saved.
        mode (str): The mode in which the file is opened (default is 'w' for write).
        Returns:
        None
        """
        try:
            if isinstance(data, (dict, list)):
                data = pd.json_normalize(data)
                self.logger.info("JSON File Normalized")
        except FileNotFoundError:
            self.logger.info(f"Error: File not found at {filepath}")
      
        try:           
            extension = filepath.split(".")[-1].lower()
            if extension == "csv":
                data.to_csv(filepath, index=False, mode=mode) 
            elif extension =="txt":
                with open(filepath, mode, encoding='utf-8') as output:
                    output.write(data)
            elif extension == "json":
                with open(filepath, mode, encoding='utf-8') as f:
                    json.dump(data, f)
            else:
                with pd.ExcelWriter(filepath) as writer:
                    for sheet_name, df in data.items():
                        sheet = writer.book.create_sheet(sheet_name)
                        for row in dataframe_to_rows(df, index=False, header=True):
                            sheet.append(row)
                        # Make the first sheet visible to avoid the IndexError
                        if writer.book.active is None:
                            writer.book.active = len(writer.book.worksheets) - 1
                        
            self.logger.info(f'Written to Folder {filepath}.')
        except FileNotFoundError as e:
            self.logger.info(f"Error: File cannot be saved at {filepath}: {e}")

    def get_file_update_time(self,path,folder=False):
        """
        Get the last update time of a file or the latest file in a folder.
        Args:
            path (str): The path to the file or folder.
            Folder (bool): If True, find the latest file in the folder.
        Returns:
            tuple: A tuple containing the current date in ISO format and 
            the number of days since the file was last updated.
        """
        self.logger.info(f"Looking for file at: {path}")
        if folder:
            files = os.listdir(path)
            latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(path, x)))
            path= os.path.join(path,latest_file)
            self.logger.info(f"Latest File is: {path}")
            """
            Get the last modification time of the file
            Convert the modification time to a datetime object
            Calculate how many days ago the file was update
            """
        try: 
            file_mod_time = os.path.getmtime(path)
            mod_time = datetime.datetime.fromtimestamp(file_mod_time)
            today = datetime.datetime.now()
            days_since_update = (today - mod_time).days
            self.logger.info(f"{path} file last updated in {days_since_update} days")
            return today.date().isoformat(),days_since_update

        except FileNotFoundError:
            print(f"File '{path}' not found.")
            return None
    
    def extract_zip_file(self):
        """Extract a .zip file if found in the current directory."""
        try:
            zip_file = None
            for file in os.listdir():
                if file.endswith('.zip'):
                    zip_file = file
                    break

            if zip_file:
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    extract_dir = os.path.splitext(zip_file)[0]  # Use zip filename as directory
                    zip_ref.extractall(extract_dir)
                    print(f"Extracted {zip_file} to {extract_dir}/")
            else:
                print("No zip file found in the current directory.")
        except Exception as e:
            print(f"Error extracting zip file: {e}")
