import os
import subprocess
import pandas as pd
import json
import datetime
import zipfile


class Data_Storage:
    
    def __init__(self,logger=None):
        if logger:
            self.logger = logger.info('Data Storage Tools Initiated.')
            self.logger = logger.getChild(__name__)
       
    def upload_files(self, filepath):  # Better word is import files
        df = pd.DataFrame()  # Create an empty dataframe
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
               
            pass  

        except ValueError as e:
            self.logger.info(str(e))
            return df  # Return the empty DataFrame in case of an unsupported file type

        self.logger.info(f'{extension} file found & {filepath} is read to dataframe.')
        df = df.dropna(how='all') 
        return df
        
    def get_file_update_time(self,path,Folder=False):
        
        self.logger.info(f"Looking for file at: {path}")
        if Folder:
            files = os.listdir(path)
            latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(path, x)))
            path= os.path.join(path,latest_file)
            self.logger.info(f"Latest File is: {path}")
            
        try:
            file_mod_time = os.path.getmtime(path)                          # Get the last modification time of the file
            mod_time = datetime.datetime.fromtimestamp(file_mod_time)       # Convert the modification time to a datetime object
            today = datetime.datetime.now()                                 # Calculate how many days ago the file was update
            days_since_update = (today - mod_time).days
            self.logger.info(f"{path} file last updated in {days_since_update} days")
            
            return today.date().isoformat(),days_since_update
        
        except FileNotFoundError:
            print(f"File '{path}' not found.")
            return None
            
    def save_file(self,data,filepath,mode ='w'):
        try:
            if isinstance(data, (dict, list)):
                data = pd.json_normalize(data)
                self.logger.info(f"JSON File Normalized")
        except FileNotFoundError:
            self.logger.info(f"Error: File not found at {filepath}")
            return None  
            
        try:           
            extension = filepath.split(".")[-1].lower()
            if extension == "csv":
                data.to_csv(filepath, index=False,mode =mode)  # Use comma for CSV
            elif extension == "txt":
                with open(filepath, 'w') as output:
                    output.write(data)
            elif extension == "json":
                with open(filepath , 'w') as f:
                    json.dump(data,f)
            else:
                with pd.ExcelWriter(filepath) as writer:
                    for sheet_name, df in data.items():
                        sheet = writer.book.create_sheet(sheet_name)
                        for row in dataframe_to_rows(group, index=False, header=True):
                            sheet.append(row)
                        # Make the first sheet visible to avoid the IndexError
                        if writer.book.active is None:
                            writer.book.active = len(writer.book.worksheets) - 1
                        
            self.logger.info(f'Written to Folder {filepath}.')
        except  FileNotFoundError as e:
            self.logger.info(f"Error: File cannot be saved at {filepath}: {e}") 
               
    def save_csv(self,data,filepath):
        try:
            if isinstance(data, (dict, list)):
                data = pd.json_normalize(data)
            
        except FileNotFoundError:
            print("Error: File not found at", filepath)
            return None    
        
    def save_json(self,data,json_output_path):
        try:
            with open(json_output_path , 'w') as f:
                json.dump(data,f)
            print(f"Data saved successfully to {json_output_path}")
        except FileNotFoundError:
            print("Error: File not found at", json_output_path)
            return None   
        
    def save_excel(self, data, filepath):
        try:
            with pd.ExcelWriter(filepath) as writer:
                for sheet_name, df in data.items():
                    sheet = writer.book.create_sheet(sheet_name)
                    for row in dataframe_to_rows(group, index=False, header=True):
                        sheet.append(row)
                    # Make the first sheet visible to avoid the IndexError
                    if writer.book.active is None:
                        writer.book.active = len(writer.book.worksheets) - 1

        except FileNotFoundError:
            print(f"Error: File not found at {filepath}")            


class Zip_Tools:
    def __init__(self,logger):
        self.logger = logger.info('ZIP Tools Initiated.')
        self.logger = logger.getChild(__name__)
        
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