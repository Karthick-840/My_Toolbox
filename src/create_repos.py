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
