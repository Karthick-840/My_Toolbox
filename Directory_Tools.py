import pandas as pd


class Data_Storage:
    
    def __init__(self):
        pass
    
    def upload_files(self, filepath):  # Better word is import files
        df = pd.DataFrame()  # Create an empty dataframe
        try:
            
            extension = filepath.split(".")[-1].lower()

            if extension == "csv":
                df = pd.read_csv(filepath, delimiter=',')  # Use comma for CSV
            elif extension == "txt":
                df = pd.read_csv(filepath, delimiter='\t')  # Use tab for TXT
            else:
                raise ValueError(f"Unsupported file extension: {extension}")
        except  FileNotFoundError:
            print("Error: File not found at", filepath)        

        return df
        
    def save_csv(self,data,filepath):
        try:
            if isinstance(data, (dict, list)):
                data = pd.json_normalize(data)
            data.to_csv(filepath, index=False)
        except FileNotFoundError:
            print("Error: File not found at", filepath)
            return None    
        
    def save_json(self,data,json_output_path):
        try:
            with open(json_output_path , 'w') as f:
                f.write(data.text)
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
            
import os
import subprocess

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
