import pytest
import requests
from unittest.mock import Mock, patch, mock_open, MagicMock
import os

from My_Toolbox.Git_Tools import Git_Tools

@pytest.fixture
def logger(caplog):
    # Using caplog to capture log messages
    return caplog

@pytest.fixture
def git_tools(logger):
    return Git_Tools(logger)

def test_create_local_repo(git_tools):
    with patch("os.makedirs") as mock_makedirs, \
         patch("os.chdir") as mock_chdir, \
         patch("subprocess.run") as mock_run:
        
        git_tools.create_local_repo("mock_repo", "/mock/path", "https://github.com/mock_repo.git")
        
        mock_makedirs.assert_called_with("/mock/path/mock_repo")
        mock_chdir.assert_called_with("/mock/path/mock_repo")
        mock_run.assert_any_call(["git", "init"])
        mock_run.assert_any_call(["git", "remote", "add", "origin", "https://github.com/mock_repo.git"])
        git_tools.logger.info.assert_any_call("Local repository 'mock_repo' created and initialized successfully.")

def test_create_requirements(git_tools):
    with patch("subprocess.check_call") as mock_check_call:
        git_tools.create_requirements("/mock/directory")
        mock_check_call.assert_called_with(["pipreqs", "/mock/directory", "--force"])
        git_tools.logger.info.assert_called_with("requirements.txt successfully generated!")
