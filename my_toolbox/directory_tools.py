
"""
Module: directory_tools
This module provides tools for data storage and manipulation, as well as handling ZIP files. 
It includes functionalities for uploading, saving, and retrieving file information, 
as well as extracting ZIP files, data validation, and atomic writes.

"""
import datetime
import json
import os
import zipfile
import shutil
import tempfile
from typing import Tuple, List, Optional

import pandas as pd

try:
    from openpyxl.utils.dataframe import dataframe_to_rows
except Exception:  # pragma: no cover
    dataframe_to_rows = None


class DataStorage:
    """
    A class used to handle data storage operations such as uploading, saving, and retrieving file information.
    Data_Storage: Provides methods for uploading, saving, and retrieving file information.
    Zip_Tools: Provides methods for extracting ZIP files.
    -------
    """
    
    def __init__(self,logger=None):
        if logger:
            self.logger = logger.info('Data Storage Tools Initiated.')
            self.logger = logger.getChild(__name__)
       
    def import_files(self, filepath): 
        """
        Imports data from a file into a pandas DataFrame.
        Parameters:
        filepath (str): The path to the file to be imported.
        Returns:
        pd.DataFrame: A DataFrame containing the data from the file. Returns an empty DataFrame if the file is not found or has an unsupported extension.
        Supported file types:
        - CSV (.csv)
        - Text (.txt)
        - JSON (.json)
        """
        df = pd.DataFrame()  
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
            
        except ValueError as e:
            self.logger.info(str(e))
            return df  # Return the empty DataFrame in case of an unsupported file type

        self.logger.info(f'{extension} file found & {filepath} is read to dataframe.')
        df = df.dropna(how='all') 
        return df
    
    def save_files(self, data, filepath, mode='w'):
        """
        Save data to a specified file path in various formats (CSV, TXT, JSON, Excel).
        Parameters:
        data (dict or list): The data to be saved.
        filepath (str): The path where the file will be saved.
        mode (str): The mode in which the file is opened (default is 'w' for write).
        Returns:
        None
        """
        try:
            if isinstance(data, (dict, list)):
                data = pd.json_normalize(data)
                self.logger.info("JSON File Normalized")
        except FileNotFoundError:
            self.logger.info(f"Error: File not found at {filepath}")
      
        try:           
            extension = filepath.split(".")[-1].lower()
            if extension == "csv":
                data.to_csv(filepath, index=False, mode=mode) 
            elif extension =="txt":
                with open(filepath, mode, encoding='utf-8') as output:
                    output.write(data)
            elif extension == "json":
                with open(filepath, mode, encoding='utf-8') as f:
                    json.dump(data, f)
            else:
                if dataframe_to_rows is None:
                    raise ImportError(
                        "openpyxl is required for Excel export. "
                        "Install with: pip install openpyxl"
                    )
                with pd.ExcelWriter(filepath) as writer:
                    for sheet_name, df in data.items():
                        sheet = writer.book.create_sheet(sheet_name)
                        for row in dataframe_to_rows(df, index=False, header=True):
                            sheet.append(row)
                        # Make the first sheet visible to avoid the IndexError
                        if writer.book.active is None:
                            writer.book.active = len(writer.book.worksheets) - 1
                        
            self.logger.info(f'Written to Folder {filepath}.')
        except FileNotFoundError as e:
            self.logger.info(f"Error: File cannot be saved at {filepath}: {e}")

    def get_file_update_time(self,path,folder=False):
        """
        Get the last update time of a file or the latest file in a folder.
        Args:
            path (str): The path to the file or folder.
            Folder (bool): If True, find the latest file in the folder.
        Returns:
            tuple: A tuple containing the current date in ISO format and 
            the number of days since the file was last updated.
        """
        self.logger.info(f"Looking for file at: {path}")
        if folder:
            files = os.listdir(path)
            latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(path, x)))
            path= os.path.join(path,latest_file)
            self.logger.info(f"Latest File is: {path}")
            """
            Get the last modification time of the file
            Convert the modification time to a datetime object
            Calculate how many days ago the file was update
            """
        try: 
            file_mod_time = os.path.getmtime(path)
            mod_time = datetime.datetime.fromtimestamp(file_mod_time)
            today = datetime.datetime.now()
            days_since_update = (today - mod_time).days
            self.logger.info(f"{path} file last updated in {days_since_update} days")
            return today.date().isoformat(),days_since_update

        except FileNotFoundError:
            print(f"File '{path}' not found.")
            return None
    
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

    def flatten_directory(self, target_dir, extension_filter=None):
        """
        Moves all files from subdirectories into the target_dir and removes empty folders.
        """
        for root, dirs, files in os.walk(target_dir, topdown=False):
            for file in files:
                if extension_filter and not file.lower().endswith(extension_filter):
                    continue
                source_path = os.path.join(root, file)
                destination_path = os.path.join(target_dir, file)
                
                # Handle naming collisions
                if os.path.exists(destination_path) and source_path != destination_path:
                    base, ext = os.path.splitext(file)
                    destination_path = os.path.join(target_dir, f"{base}_{int(datetime.datetime.now().timestamp())}{ext}")
                
                shutil.move(source_path, destination_path)
            
            # Clean up empty sub-folders
            if root != target_dir and not os.listdir(root):
                os.rmdir(root)
        self.logger.info(f"Directory {target_dir} flattened.")

    def create_backup(self, folder_path, backup_name=None):
        """Creates a timestamped ZIP archive of a directory."""
        if not backup_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            backup_name = f"backup_{os.path.basename(folder_path)}_{timestamp}"
        
        output_filename = shutil.make_archive(backup_name, 'zip', folder_path)
        self.logger.info(f"Backup created: {output_filename}")
        return output_filename
    
    # ===== NEW VALIDATION & ROBUSTNESS METHODS =====
    
    def validate_dataframe(
        self,
        df: pd.DataFrame,
        required_columns: Optional[List[str]] = None,
        dtypes: Optional[dict] = None,
        allow_nulls: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Validate a DataFrame against schema constraints.
        
        Args:
            df: DataFrame to validate
            required_columns: List of columns that must be present
            dtypes: Dict mapping column names to expected dtypes (e.g., {'revenue': 'float64', 'date': 'datetime64'})
            allow_nulls: If False, raise error on any NaN values
            
        Returns:
            (is_valid, errors_list) tuple
            
        Example:
            >>> valid, errors = ds.validate_dataframe(df, 
            ...     required_columns=['ticker', 'price'],
            ...     dtypes={'price': 'float64'},
            ...     allow_nulls=False)
        """
        errors = []
        
        # Check if empty
        if df.empty:
            errors.append("DataFrame is empty")
            return (False, errors)
        
        # Check required columns
        if required_columns:
            missing = set(required_columns) - set(df.columns)
            if missing:
                errors.append(f"Missing required columns: {missing}")
        
        # Check dtypes
        if dtypes:
            for col, expected_dtype in dtypes.items():
                if col not in df.columns:
                    errors.append(f"Column '{col}' not found for dtype validation")
                    continue
                if str(df[col].dtype) != expected_dtype:
                    errors.append(f"Column '{col}' dtype is {df[col].dtype}, expected {expected_dtype}")
        
        # Check for nulls
        if not allow_nulls:
            null_cols = df.columns[df.isnull().any()].tolist()
            if null_cols:
                errors.append(f"Columns with NaN values: {null_cols}")
        
        return (len(errors) == 0, errors)
    
    def import_files_with_validation(
        self,
        filepath: str,
        required_columns: Optional[List[str]] = None,
        dtypes: Optional[dict] = None,
        skip_invalid: bool = False
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Import file and validate the resulting DataFrame.
        
        Args:
            filepath: Path to file (CSV/JSON/TXT)
            required_columns: Required columns
            dtypes: Expected dtypes
            skip_invalid: If True, skip validation errors; if False, raise on error
            
        Returns:
            (dataframe, errors_list) tuple
            
        Example:
            >>> df, errors = ds.import_files_with_validation(
            ...     'data.csv',
            ...     required_columns=['ticker', 'price'],
            ...     skip_invalid=False)
        """
        df = self.import_files(filepath)
        
        is_valid, errors = self.validate_dataframe(df, required_columns, dtypes)
        
        if not is_valid and not skip_invalid:
            error_msg = "; ".join(errors)
            if self.logger:
                self.logger.error(f"Validation failed for {filepath}: {error_msg}")
        
        return (df, errors)
    
    def save_files_atomic(
        self,
        data,
        filepath: str,
        backup: bool = True,
        mode: str = 'w'
    ) -> bool:
        """
        Save file atomically (write to temp file, then atomic rename).
        
        Prevents data corruption if process crashes mid-write.
        Optionally backs up existing file before overwrite.
        
        Args:
            data: Data to save (DataFrame, dict, or string)
            filepath: Target file path
            backup: If True, backup existing file before overwrite
            mode: File mode ('w' for write, 'a' for append)
            
        Returns:
            True if successful, False otherwise
            
        Example:
            >>> success = ds.save_files_atomic(df, 'output.csv', backup=True)
        """
        import tempfile
        
        try:
            # Create backup if file exists and backup=True
            if backup and os.path.exists(filepath):
                backup_path = f"{filepath}.backup"
                shutil.copy2(filepath, backup_path)
                if self.logger:
                    self.logger.info(f"Backup created: {backup_path}")
            
            # Write to temporary file first
            temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(filepath) or '.')
            
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
                    extension = filepath.split(".")[-1].lower()
                    
                    if isinstance(data, pd.DataFrame):
                        if extension == "csv":
                            data.to_csv(temp_file, index=False)
                        elif extension == "json":
                            data.to_json(temp_file)
                        else:
                            data.to_csv(temp_file, index=False)
                    elif isinstance(data, (dict, list)):
                        json.dump(data, temp_file, indent=2)
                    else:
                        temp_file.write(str(data))
                
                # Atomic rename
                shutil.move(temp_path, filepath)
                
                if self.logger:
                    self.logger.info(f"File saved atomically: {filepath}")
                
                return True
            
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise e
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Atomic save failed for {filepath}: {e}")
            return False
    
    def export_compressed(
        self,
        data,
        filepath: str,
        format: str = 'csv',
        compression: str = 'gzip'
    ) -> bool:
        """
        Export DataFrame as compressed file (CSV/JSON + gzip).
        
        Reduces file size for large datasets.
        
        Args:
            data: DataFrame to export
            filepath: Output file path (e.g., 'data.csv.gz')
            format: 'csv' or 'json'
            compression: 'gzip' (default) or 'bz2', 'zip', 'xz'
            
        Returns:
            True if successful, False otherwise
            
        Example:
            >>> success = ds.export_compressed(df, 'large_data.csv.gz', format='csv')
        """
        try:
            if not isinstance(data, pd.DataFrame):
                if self.logger:
                    self.logger.error("Data must be a pandas DataFrame for compression")
                return False
            
            if format == 'csv':
                data.to_csv(filepath, index=False, compression=compression)
            elif format == 'json':
                data.to_json(filepath, compression=compression)
            else:
                if self.logger:
                    self.logger.error(f"Unsupported format: {format}")
                return False
            
            if self.logger:
                self.logger.info(f"Compressed export completed: {filepath}")
            
            return True
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Compression export failed: {e}")
            return False
    
    def list_files_in_dir(
        self,
        directory: str,
        pattern: str = '*',
        recursive: bool = False,
        sort_by: str = 'name'
    ) -> List[str]:
        """
        List files in directory matching a pattern.
        
        Args:
            directory: Directory path
            pattern: Glob pattern (e.g., '*.csv', '*.json')
            recursive: If True, search subdirectories
            sort_by: 'name' or 'date' (modification time)
            
        Returns:
            List of file paths (sorted)
            
        Example:
            >>> csv_files = ds.list_files_in_dir('./data', pattern='*.csv', recursive=True)
        """
        import glob
        
        try:
            if recursive:
                search_pattern = os.path.join(directory, '**', pattern)
                files = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = os.path.join(directory, pattern)
                files = glob.glob(search_pattern)
            
            # Sort by name or date
            if sort_by == 'date':
                files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            else:
                files.sort()
            
            if self.logger:
                self.logger.info(f"Found {len(files)} files in {directory}")
            
            return files
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing files: {e}")
            return []


    def batch_import(self, folder_path, extension=".csv"):
        """Finds all files of an extension and merges them into one DataFrame."""
        all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(extension)]
        df_list = [self.import_files(f) for f in all_files]
        
        combined_df = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
        self.logger.info(f"Batch imported {len(all_files)} files from {folder_path}.")
        return combined_df

    def purge_old_files(self, folder_path, days=30):
        """Deletes files in a directory older than the specified number of days."""
        critical_time = datetime.datetime.now() - datetime.timedelta(days=days)
        count = 0
        for f in os.listdir(folder_path):
            path = os.path.join(folder_path, f)
            if os.path.getmtime(path) < critical_time.timestamp():
                os.remove(path)
                count += 1
        self.logger.info(f"Purged {count} files older than {days} days.")