
import pytest
import requests
from unittest.mock import Mock, patch, mock_open, MagicMock
import os

from My_Toolbox.Kaggle_Tools import Kaggle_Tools

@pytest.fixture
def logger(caplog):
    # Using caplog to capture log messages
    return caplog

@pytest.fixture
def kaggle_tools(logger):
    return Kaggle_Tools(logger=logger, kaggle_dir="/mock/dir", move_to_read_only=False)

def test_kaggle_auth(kaggle_tools):
    with patch.dict("os.environ", {"KAGGLE_USERNAME": "mock_user", "KAGGLE_KEY": "mock_key"}):
        kaggle_tools.kaggle_auth()
        kaggle_tools.logger.info.assert_called_with("Kaggle credentials found in environment variables.")

    with patch("builtins.open", mock_open(read_data='{"username": "mock_user", "key": "mock_key"}')):
        kaggle_tools.setup_kaggle_credentials()
        assert os.environ["KAGGLE_USERNAME"] == "mock_user"
        assert os.environ["KAGGLE_KEY"] == "mock_key"
        kaggle_tools.logger.info.assert_called_with("Json File Imported and loaded into environment")

def test_download_dataset(kaggle_tools):
    with patch("kaggle.api.kaggle_api_extended.KaggleApi.authenticate") as mock_authenticate, \
         patch("kaggle.api.kaggle_api_extended.KaggleApi.dataset_download_files") as mock_download:
        mock_authenticate.return_value = True
        kaggle_tools.download_dataset("mock-dataset")
        kaggle_tools.logger.info.assert_any_call("Successfully authenticated with Kaggle API.")
        kaggle_tools.logger.info.assert_any_call("Downloaded dataset: mock-dataset")
