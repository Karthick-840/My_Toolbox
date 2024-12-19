
import os
import subprocess

class GitTools:
    
    def __init__(self,logger=None):
        if logger:
            self.logger = logger.info('My Git Tools Imported.')
            self.logger = logger.getChild(__name__)

    def create_local_repo(self,repo_name, folder_path=None,remote_url=None):
        # Change directory to the specified path
        
        if folder_path is None:
            folder_path = os.getcwd()
            
        repo_path = os.path.join(folder_path,repo_name)
    
        if not os.path.exists(repo_path):
        # Create the directory if it doesn't exist
            os.makedirs(repo_path)
            self.logger.info(f"Directory for project '{repo_name}' created.")
        else:
            self.logger.info(f"Directory for '{repo_name}' already exists.")
                
        os.chdir(repo_path)

        # Initialize Git repository
        subprocess.run(['git', 'init'])
        self.logger.info(f"Local repository '{repo_name}' created and initialized successfully.")
        
        if remote_url:
            subprocess.run(['git', 'remote', 'add', 'origin', remote_url])             # Link local repository to remote repository
            
            # Push changes to remote repository
            subprocess.run(['git', 'pull', 'origin', 'main'])

            self.logger.info(f"Repository '{repo_name}' linked to remote repository and changes pulled successfully.")

    def create_repos_from_file(self,repos_path_file):
        
         if not os.path.exists(repos_path_file):
             with open(repos_path_file, 'r') as file:
                for line in file:
                    repo_name, github_url = line.strip().split(',')
                    self.create_local_repo(repo_name, remote_url=github_url)

    def create_requirements(self,directory):
        try:
            self.logger.info(f"Generating requirements.txt for the directory: {directory}")
            # Use the full path to pipreqs in the virtual environment
            pipreqs_path = os.path.join(os.path.dirname(os.sys.executable), 'pipreqs.exe')
            print( pipreqs_path)
            subprocess.check_call([pipreqs_path, directory, '--force'])
            #subprocess.check_call([os.sys.executable, 'pipreqs.pipreqs', directory, '--force'])
            self.logger.info("requirements.txt successfully generated!")
        except subprocess.CalledProcessError as e:
            self.logger.info(f"Error occurred: {e}")
