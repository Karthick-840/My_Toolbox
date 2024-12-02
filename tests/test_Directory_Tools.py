import os
import json
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch, mock_open
from My_Toolbox.Directory_Tools import Data_Storage, Zip_Tools  # Replace 'your_module' with the actual module name


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = MagicMock()
    return logger


@pytest.fixture
def data_storage(mock_logger):
    """Create a Data_Storage instance for testing."""
    return Data_Storage(logger=mock_logger)


@pytest.fixture
def sample_data():
    """Provide sample data for testing file saving."""
    return {"name": "Alice", "age": 30}


def test_upload_files_csv(data_storage, mock_logger):
    """Test uploading a CSV file."""
    test_csv = "test.csv"
    mock_data = "name,age\nAlice,30\nBob,25\n"
    
    with patch("builtins.open", mock_open(read_data=mock_data)):
        df = data_storage.upload_files(test_csv)
        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] == 2  # Two rows in the CSV


def test_upload_files_txt(data_storage, mock_logger):
    """Test uploading a TXT file."""
    test_txt = "test.txt"
    mock_data = "name\tage\nAlice\t30\nBob\t25\n"
    
    with patch("builtins.open", mock_open(read_data=mock_data)):
        df = data_storage.upload_files(test_txt)
        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] == 2  # Two rows in the TXT


def test_upload_files_json(data_storage, mock_logger):
    """Test uploading a JSON file."""
    test_json = "test.json"
    mock_data = json.dumps([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}])
    
    with patch("builtins.open", mock_open(read_data=mock_data)):
        df = data_storage.upload_files(test_json)
        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] == 2  # Two objects in the JSON


def test_upload_files_unsupported_format(data_storage, mock_logger):
    """Test unsupported file format handling."""
    test_unsupported = "test.doc"
    
    with pytest.raises(ValueError):
        data_storage.upload_files(test_unsupported)


def test_get_file_update_time(data_storage, mock_logger):
    """Test getting file update time."""
    test_file_path = "test.txt"
    
    with patch("os.path.getmtime", return_value=0):
        with patch("os.listdir", return_value=[test_file_path]):
            date, days = data_storage.get_file_update_time(".", Folder=True)
            assert isinstance(date, str)
            assert days == 0


def test_save_file_csv(data_storage, sample_data):
    """Test saving a DataFrame to a CSV file."""
    test_csv = "output.csv"
    
    with patch("pandas.DataFrame.to_csv") as mock_to_csv:
        data_storage.save_file(pd.DataFrame([sample_data]), test_csv)
        mock_to_csv.assert_called_once_with(test_csv, index=False, mode='w')


def test_save_file_json(data_storage, sample_data):
    """Test saving data to a JSON file."""
    test_json = "output.json"
    
    with patch("builtins.open", mock_open()) as mocked_file:
        data_storage.save_file(sample_data, test_json)
        mocked_file.assert_called_once_with(test_json, 'w')


def test_save_file_excel(data_storage, sample_data):
    """Test saving data to an Excel file."""
    test_excel = "output.xlsx"
    
    with patch("pandas.ExcelWriter") as mock_excel_writer:
        data_storage.save_file({'Sheet1': pd.DataFrame([sample_data])}, test_excel)
        mock_excel_writer.assert_called_once_with(test_excel)


def test_zip_tools(mock_logger):
    """Test ZIP tools for extracting zip files."""
    zip_file_name = "test.zip"
    
    # Mock the zip file extraction
    with patch("os.listdir", return_value=[zip_file_name]), \
         patch("zipfile.ZipFile.extractall") as mock_extract:
        
        zip_tools = Zip_Tools(mock_logger)
        zip_tools.extract_zip_file()
        
        mock_extract.assert_called_once_with(os.path.splitext(zip_file_name)[0])


def test_zip_tools_no_zip_file(mock_logger):
    """Test ZIP tools when no zip file is found."""
    with patch("os.listdir", return_value=[]):
        zip_tools = Zip_Tools(mock_logger)
        with patch("builtins.print") as mock_print:
            zip_tools.extract_zip_file()
            mock_print.assert_called_once_with("No zip file found in the current directory.")


if __name__ == "__main__":
    pytest.main()
