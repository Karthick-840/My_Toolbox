import os
import subprocess
import ast
import pkg_resources


class Git_Tools:
    
    def __init__(self,logger):
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
            self.logger.info(f"Directory '{repo_path}' created.")
        else:
            self.logger.info(f"Directory '{repo_path}' already exists.")
                
        os.chdir(repo_path)

        # Initialize Git repository
        subprocess.run(['git', 'init'])
        self.logger.info(f"Local repository '{repo_name}' creation and initialization completed successfully.")
        
        if remote_url:
            subprocess.run(['git', 'remote', 'add', 'origin', remote_url])             # Link local repository to remote repository
            
            # Create README file
            with open('README.md', 'w') as readme_file:
                readme_file.write(f"# {repo_name}\n")
            
                # Stage files and # Commit changes

            subprocess.run(['git', 'add', '.'])
            subprocess.run(['git', 'commit', '-m', 'Initial commit'])
            
            # Push changes to remote repository
            subprocess.run(['git', 'push', '-u', 'origin', 'main'])

            self.logger.info(f"Repository '{repo_name}' linked to remote repository and changes pushed successfully.")

    def create_repos_from_file(self,repos_path_file):
        
         if not os.path.exists(repos_path_file):
             with open(repos_path_file, 'r') as file:
                for line in file:
                    repo_name, github_url = line.strip().split(',')
                    self.create_local_repo(repo_name, remote_url=github_url)

    def create_requirements(self,directory):
        try:
            self.logger.info(f"Generating requirements.txt for the directory: {directory}")
            subprocess.check_call([os.sys.executable, '-m', 'pipreqs', directory, '--force'])
            self.logger.info("requirements.txt successfully generated!")
        except subprocess.CalledProcessError as e:
            self.logger.info(f"Error occurred: {e}")
            self.logger.info("Attempting to generate requirements.txt manually...")
             
            try:
                all_imports = self.get_all_imports_from_directory(directory)
                requirements = self.get_installed_versions(all_imports)

                requirements_path  = os.path.join(directory,"requirements.txt")
                # Write the requirements to a file
                with open(requirements_path, 'w') as f:
                    for req in requirements:
                        f.write(f"{req}\n")

                self.logger.info("requirements.txt file generated.")
            except Exception as e:
                self.logger.info(f"Error occurred while manually generating requirements.txt: {e}")
 
    def get_imports_from_file(self,filepath):
        """Extract all imports from a Python file."""
        self.logger.info(f"Importing from file {filepath}")
        with open(filepath, "r", encoding="utf-8") as file:
            tree = ast.parse(file.read(), filename=filepath)
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])  # Only get the base module
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])  # Only get the base module
        return imports

    def get_all_imports_from_directory(self,directory):
        """Get all unique imports from all Python files in the directory."""
        imports_set = set()
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    imports = self.get_imports_from_file(filepath)
                    imports_set.update(imports)
        
        return sorted(imports_set)

    def get_installed_versions(self,imports):
        """Get the installed versions of each imported package."""
        installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
        requirements = []
        
        for imp in imports:
            if imp in installed_packages:
                requirements.append(f"{imp}=={installed_packages[imp]}")
            else:
                requirements.append(imp)  # If version not found, just add the package name

        return requirements

