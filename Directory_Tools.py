import os
import subprocess
import pandas as pd
import json
import datetime



class Data_Storage:
    
    def __init__(self,logger):
        self.logger = logger.info('Data Storage Initiated.')
        self.logger = logger.getChild(__name__)
        pass
    
    def upload_files(self, filepath):  # Better word is import files
        df = pd.DataFrame()  # Create an empty dataframe
        try:
            
            extension = filepath.split(".")[-1].lower()

            if extension == "csv":
                df = pd.read_csv(filepath, delimiter=',',skip_blank_lines=True)  # Use comma for CSV
            elif extension == "txt":
                df = pd.read_csv(filepath, delimiter='\t', skip_blank_lines=True, skipinitialspace=True)  # Use tab for TXT
            else:
                raise ValueError(f"Unsupported file extension: {extension}")
        except  FileNotFoundError:
            self.logger.info(f"Error: File not found at {filepath}") 
               
            pass  

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
            
    def save_file(self,data,filepath):
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
                data.to_csv(filepath, index=False)  # Use comma for CSV
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

def create_local_repo(repo_name, directory):
    # Change directory to the specified path
    os.chdir(directory)

    # Initialize Git repository
    subprocess.run(['git', 'init'])

    # Create README file
    with open('README.md', 'w') as readme_file:
        readme_file.write(f"# {repo_name}\n")

    # Stage files
    subprocess.run(['git', 'add', '.'])

    # Commit changes
    subprocess.run(['git', 'commit', '-m', 'Initial commit'])

    print(f"Local repository '{repo_name}' creation and initialization completed successfully.")

def link_remote_repo(repo_name, directory, github_url):
    # Change directory to the specified path
    os.chdir(directory)

    # Link local repository to remote repository
    subprocess.run(['git', 'remote', 'add', 'origin', github_url])

    # Push changes to remote repository
    subprocess.run(['git', 'push', '-u', 'origin', 'master'])

    print(f"Repository '{repo_name}' linked to remote repository and changes pushed successfully.")

# Read repository names and GitHub URLs from a text file
with open('repositories.txt', 'r') as file:
    for line in file:
        repo_name, github_url = line.strip().split(',')
        directory = os.path.join(os.getcwd(), repo_name)

        # Create local repository
        create_local_repo(repo_name, directory)

        # Link to remote repository
        link_remote_repo(repo_name, directory, github_url)
