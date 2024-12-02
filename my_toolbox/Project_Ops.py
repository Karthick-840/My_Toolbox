import os
import pandas as pd
import argparse
from Tools import Log_Tools, API_Tools

if __name__ == "__main__":
    
    today = pd.to_datetime('today').date()
    # Create the parser
    parser = argparse.ArgumentParser(description="Creating a Project.")

    # Add multiple arguments
    parser.add_argument("--repo_name", type=str, help="Name of the Repo you want to create")
    parser.add_argument("--folder_path", type=str, help="Give the folder path where the Repo is to be created locally")
    parser.add_argument("--remote_url", type=str, help="Give in the URL of the Remote Github Repo")
    parser.add_argument("--kaggle_dataset", type=str, help="Give in the URL of the Remote Github Repo")


    # Parse the arguments
    args = parser.parse_args()
    
    if args.folder_path is None:
        folder_path = os.getcwd()
    else:
        folder_path = args.folder_path

    if args.remote_url is None:
        remote_url = None
    else:
        remote_url = args.remote_url
        
    
    repo_path = os.path.join(folder_path,args.repo_name)
    if not os.path.exists(repo_path):
        os.makedirs(repo_path)      # Create the directory if it doesn't exist

    logger = Log_Tools.Logger(f'Logger Initiated','INFO',filename=f'{repo_path}/Log-{today}.log',filemode='w').logger
    logger = logger.getChild(__name__)
    logger.info(f'{args.repo_name} Project is Initiated')
    
    os.chdir(repo_path)

    logger.info(f"Inside the repo Directory '{args.repo_name}' ")
    
    git_tools = API_Tools.Git_Tools(logger)
    git_tools.create_local_repo(args.repo_name, folder_path=folder_path,remote_url=remote_url)
    
    if args.kaggle_dataset:
        kaggle_tools = API_Tools.Kaggle_Tools(logger)
        kaggle_tools.apply(args.kaggle_dataset)
        logger.info(f'{args.kaggle_dataset} is downloaded')