import os
import csv
from typing import Optional, List, Dict, Any, Tuple
from pprint import pprint

try:
    import gspread
    from google.auth.exceptions import GoogleAuthError
    from google.oauth2.service_account import Credentials
    from gspread_dataframe import set_with_dataframe
except Exception:  # pragma: no cover
    gspread = None
    Credentials = None
    set_with_dataframe = None
    GoogleAuthError = Exception

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

try:
    import polars as pl
except Exception:  # pragma: no cover
    pl = None

try:
    from google.cloud import bigquery, datastore, storage
except Exception:  # pragma: no cover
    storage = None
    datastore = None
    bigquery = None

try:
    from google.cloud.exceptions import NotFound
except Exception:  # pragma: no cover
    NotFound = Exception

try:
    from google.oauth2 import service_account
except Exception:  # pragma: no cover
    service_account = None

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _require_google_sheets_deps():
    if not all([gspread, Credentials, set_with_dataframe]):
        raise ImportError(
            "Google Sheets dependencies are missing. "
            "Install requirements with: pip install -r requirements.txt"
        )


def _require_google_cloud_storage_deps():
    if storage is None:
        raise ImportError(
            "google-cloud-storage dependency is missing. "
            "Install requirements with: pip install -r requirements.txt"
        )


def _require_bigquery_deps():
    if bigquery is None:
        raise ImportError(
            "google-cloud-bigquery dependency is missing. "
            "Install requirements with: pip install -r requirements.txt"
        )


def _require_datastore_deps():
    if datastore is None:
        raise ImportError(
            "google-cloud-datastore dependency is missing. "
            "Install requirements with: pip install -r requirements.txt"
        )


class GoogleSheets:
    """Helper class for Google Sheets operations."""

    def __init__(self, sheet_id: str, settings=None, logger=None, scopes: Optional[List[str]] = None):
        """Initialize Google Sheets handler.

        Args:
            sheet_id: Google Sheet ID
            settings: Settings object containing folder paths
            logger: Logger instance
            scopes: Optional list of OAuth scopes
        """
        _require_google_sheets_deps()

        if settings is not None:
            self.SF = settings.SF
            self.DS = settings.DS
            self.DATE = settings.DATE
            self.input_folder = settings.INPUT_FOLDER
            self.output_folder = settings.OUTPUT_FOLDER
        else:
            self.SF = None
            self.DS = None
            self.DATE = None
            self.input_folder = None
            self.output_folder = None

        if logger:
            logger.info('Google Sheets Function Initiated')
            self.logger = logger.getChild(__name__)
        else:
            self.logger = None

        self.sheet_id = sheet_id
        if not scopes:
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        self.sheet = self.check_credentials(self.sheet_id, scopes=scopes)

    def check_credentials(self, sheet_id: str, scopes: List[str]) -> Optional[Any]:
        """Check and load Google Sheets credentials.

        Args:
            sheet_id: Google Sheet ID
            scopes: List of OAuth scopes

        Returns:
            Spreadsheet object or None if authentication fails
        """
        creds, sheet = None, None
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        token_path = os.path.join(parent_dir, "token.json")

        try:
            if os.path.exists(token_path):
                creds = Credentials.from_service_account_file(token_path, scopes=scopes)
                client = gspread.authorize(creds)
                sheet = client.open_by_key(sheet_id)
                if self.logger:
                    self.logger.info("Authentication successful.")
            else:
                if self.logger:
                    self.logger.error("Authentication Token is missing")
        except GoogleAuthError as auth_error:
            if self.logger:
                self.logger.error(f"Authentication failed: {str(auth_error)}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"An error occurred: {str(e)}")

        return sheet

    def get_workbook(self) -> None:
        """Download all worksheets from the Google Sheet as text files.

        Saves each worksheet as a tab-separated text file in the input folder.
        """
        if not self.sheet:
            if self.logger:
                self.logger.error("No sheet available to download")
            return

        for worksheet in self.sheet.worksheets():
            sheet_name = worksheet.title
            values = worksheet.get_all_values()
            file_path = os.path.join(self.input_folder, f"{sheet_name}.txt")
            with open(file_path, "w") as f:
                for row in values:
                    f.write("\t".join(row) + "\n")
            if self.logger:
                self.logger.info(f"Saved {file_path}")

    def write_dataframe_to_sheet(self, dataframe: Any, worksheet_name: str) -> None:
        """Write a DataFrame to a specified worksheet in a Google Sheets file.

        Args:
            dataframe: pandas DataFrame to write to the sheet
            worksheet_name: Name of the worksheet to write to
        """
        if not self.sheet:
            if self.logger:
                self.logger.error("No sheet available to write to")
            return

        try:
            existing_worksheets = [ws.title for ws in self.sheet.worksheets()]

            if worksheet_name in existing_worksheets:
                worksheet = self.sheet.worksheet(worksheet_name)
                worksheet.clear()
                if self.logger:
                    self.logger.info(f"Cleared existing worksheet '{worksheet_name}'.")
            else:
                worksheet = self.sheet.add_worksheet(title=worksheet_name, rows="100", cols="20")
                if self.logger:
                    self.logger.info(f"Created new worksheet '{worksheet_name}'.")

            set_with_dataframe(worksheet, dataframe)

            if self.logger:
                self.logger.info(f"DataFrame written to {worksheet_name} in Google Sheets.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"An error occurred while writing DataFrame to sheet: {str(e)}")

    def write_to_sheets(self) -> None:
        """Write all CSV files from output folder to Google Sheets.

        Each CSV file becomes a separate worksheet in the Google Sheet.
        """
        if pd is None:
            raise ImportError("pandas is required for write_to_sheets.")
        csv_directory = self.output_folder
        csv_files = [f for f in os.listdir(csv_directory) if f.endswith('.csv')]

        for csv_file in csv_files:
            file_path = os.path.join(csv_directory, csv_file)
            try:
                df = pd.read_csv(file_path)
                worksheet_name = os.path.splitext(csv_file)[0]
                self.write_dataframe_to_sheet(df, worksheet_name)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to write {csv_file} to Google Sheets: {str(e)}")


class GoogleCloudStorage:
    """Helper class for Google Cloud Storage operations."""

    def __init__(self, credentials_info: Optional[Dict[str, Any]] = None, logger=None,
                 project: Optional[str] = None, credentials_path: Optional[str] = None):
        """Initialize the Google Cloud Storage client.

        Args:
            credentials_info: Dictionary containing GCP service account credentials
            logger: Optional logger instance
            project: Optional Google Cloud project ID
            credentials_path: Path to a service account JSON file (alternative to credentials_info)
        """
        _require_google_cloud_storage_deps()
        if credentials_info:
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            project_id = project or credentials_info.get('project_id')
            self.storage_client = storage.Client(credentials=credentials, project=project_id)
        elif credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            self.storage_client = storage.Client(project=project)
        else:
            self.storage_client = storage.Client(project=project)
        self.logger = logger

    def list_buckets(self, max_results: int = 100) -> List[str]:
        """List all buckets in the project.

        Args:
            max_results: Maximum number of buckets to list

        Returns:
            List of bucket names
        """
        buckets = self.storage_client.list_buckets(max_results=max_results)
        bucket_names = [bucket.name for bucket in buckets]
        print("Buckets:")
        pprint(bucket_names)
        return bucket_names

    def get_bucket(self, bucket_name: str) -> Tuple[Any, Dict[str, Any]]:
        """Retrieve a bucket and its details.

        Args:
            bucket_name: Name of the bucket to retrieve

        Returns:
            Tuple of (Bucket object, dictionary of bucket details)
        """
        bucket = self.storage_client.get_bucket(bucket_name)
        details = {
            "name": bucket.name,
            "selfLink": bucket._properties.get('selfLink', 'N/A'),
            "id": bucket._properties.get('id', 'N/A'),
            "location": bucket._properties.get('location', 'N/A'),
            "timeCreated": bucket._properties.get('timeCreated', 'N/A'),
            "storageClass": bucket._properties.get('storageClass', 'N/A'),
            "updated": bucket._properties.get('updated', 'N/A'),
        }
        return bucket, details

    def create_bucket(self, bucket_name: str, storage_class: str = 'COLDLINE', location: str = 'US') -> Any:
        """Create a new bucket.

        Args:
            bucket_name: Name of the bucket to create
            storage_class: Storage class of the bucket (e.g., 'COLDLINE', 'STANDARD')
            location: Location of the bucket (e.g., 'US', 'EU')

        Returns:
            Created Bucket object
        """
        bucket = self.storage_client.bucket(bucket_name)
        bucket.storage_class = storage_class
        bucket.location = location
        bucket = self.storage_client.create_bucket(bucket)
        pprint(vars(bucket))
        return bucket

    def upload_to_bucket(self, blob_name: str, file_path: str, bucket_name: str) -> Any:
        """Upload a file to a bucket.

        Args:
            blob_name: Name of the blob (object) in the bucket
            file_path: Path to the local file to upload
            bucket_name: Name of the target bucket

        Returns:
            Uploaded Blob object
        """
        bucket = self.storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(file_path)
        print(f"Uploaded {file_path} to {bucket_name} as {blob_name}.")
        if self.logger:
            self.logger.info(f"Uploaded {file_path} to {bucket_name} as {blob_name}.")
        return blob

    def download_file_from_bucket(self, blob_name: str, file_path: str, bucket_name: str) -> None:
        """Download a file from a bucket.

        Args:
            blob_name: Name of the blob (object) in the bucket
            file_path: Path to save the downloaded file locally
            bucket_name: Name of the source bucket
        """
        bucket = self.storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        with open(file_path, 'wb') as f:
            self.storage_client.download_blob_to_file(blob, f)
        print(f"Downloaded {blob_name} from {bucket_name} to {file_path}.")

    def download_file_uri(self, uri: str, file_path: str) -> None:
        """Download a file using its URI.

        Args:
            uri: URI of the blob (e.g., 'gs://bucket_name/blob_name')
            file_path: Path to save the downloaded file locally
        """
        with open(file_path, 'wb') as f:
            self.storage_client.download_blob_to_file(uri, f)
        print(f"Downloaded from {uri} to {file_path}.")


class GoogleBigQueryHelper:
    """Helper class for Google BigQuery operations."""

    def __init__(self, project_id: Optional[str] = None, credentials_json: Optional[str] = None):
        """Initializes the BigQuery Helper.

        Args:
            project_id: Google Cloud Project ID (if not set, defaults to environment variable)
            credentials_json: Path to service account credentials JSON (optional)
        """
        _require_bigquery_deps()
        if credentials_json:
            self.credentials = service_account.Credentials.from_service_account_file(credentials_json)
            self.client = bigquery.Client(project=project_id, credentials=self.credentials)
        else:
            self.client = bigquery.Client(project=project_id)

    def create_dataset(self, dataset_name: str) -> Optional[Any]:
        """Creates a new dataset in BigQuery.

        Args:
            dataset_name: Name of the dataset to create

        Returns:
            Created dataset or None if it already exists
        """
        dataset_id = f"{self.client.project}.{dataset_name}"
        dataset = bigquery.Dataset(dataset_id)
        try:
            dataset = self.client.create_dataset(dataset)
            print(f"Dataset {dataset_name} created successfully.")
            return dataset
        except NotFound:
            print(f"Dataset {dataset_name} already exists.")
            return None

    def infer_schema_from_csv(self, csv_file_path: str) -> List[Any]:
        """Infers the schema from a CSV file.

        Args:
            csv_file_path: Path to the CSV file

        Returns:
            A list of BigQuery SchemaField objects
        """
        with open(csv_file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)
            sample_rows = []
            for i, row in enumerate(reader):
                if i >= 10:
                    break
                sample_rows.append(row)

            def infer_type(value):
                try:
                    int(value)
                    return "INTEGER"
                except ValueError:
                    try:
                        float(value)
                        return "FLOAT"
                    except ValueError:
                        return "STRING"

            schema_fields = []
            for col_index, header in enumerate(headers):
                sample_value = sample_rows[0][col_index] if sample_rows else ''
                col_type = infer_type(sample_value)
                schema_fields.append(bigquery.SchemaField(header, col_type, mode="NULLABLE"))

            return schema_fields

    def create_table_from_csv(self, dataset_name: str, table_name: str, csv_file_path: str) -> Optional[Any]:
        """Creates a BigQuery table from a CSV file's schema.

        Args:
            dataset_name: Dataset name
            table_name: Table name
            csv_file_path: Path to the CSV file

        Returns:
            Created BigQuery table
        """
        schema = self.infer_schema_from_csv(csv_file_path)
        return self.create_table(dataset_name, table_name, schema)

    def create_table(self, dataset_name: str, table_name: str, schema: List[Any]) -> Optional[Any]:
        """Creates a new table in the specified dataset.

        Args:
            dataset_name: Dataset name
            table_name: Table name
            schema: List of bigquery.SchemaField objects

        Returns:
            Created table or None if it already exists
        """
        dataset_ref = self.client.dataset(dataset_name)
        table_ref = dataset_ref.table(table_name)
        table = bigquery.Table(table_ref, schema=schema)
        try:
            table = self.client.create_table(table)
            print(f"Table {table_name} created in dataset {dataset_name}.")
            return table
        except NotFound:
            print(f"Table {table_name} already exists in dataset {dataset_name}.")
            return None

    def insert_rows(self, dataset_name: str, table_name: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Inserts rows of data into a BigQuery table.

        Args:
            dataset_name: Dataset name
            table_name: Table name
            rows: List of rows to insert (as dictionaries)

        Returns:
            List of errors (empty if successful)
        """
        dataset_ref = self.client.dataset(dataset_name)
        table_ref = dataset_ref.table(table_name)
        table = self.client.get_table(table_ref)
        errors = self.client.insert_rows_json(table, rows)
        if errors == []:
            print(f"Successfully inserted rows into {table_name}.")
        else:
            print(f"Errors occurred while inserting rows: {errors}")
        return errors

    def query_data(self, query: str) -> Any:
        """Queries BigQuery using SQL.

        Args:
            query: SQL query string

        Returns:
            Query results iterator
        """
        query_job = self.client.query(query)
        results = query_job.result()
        print(f"Query finished. Total bytes processed: {query_job.total_bytes_processed}")
        return results

    def read_table(self, dataset_name: str, table_name: str, max_rows: int = 1000) -> List[Dict[str, Any]]:
        """Reads rows from a BigQuery table with an upper limit.

        Args:
            dataset_name: Dataset name
            table_name: Table name
            max_rows: Maximum number of rows to read (default: 1000)

        Returns:
            Table rows as a list of dictionaries
        """
        dataset_ref = self.client.dataset(dataset_name)
        table_ref = dataset_ref.table(table_name)
        table = self.client.get_table(table_ref)
        rows = self.client.list_rows(table, max_results=max_rows)
        result = [dict(row.items()) for row in rows]
        print(f"Read {len(result)} rows from {table_name} (max: {max_rows}).")
        return result

    def query_data_to_df(self, query: str) -> Any:
        """Queries BigQuery and returns results as a pandas DataFrame.

        Args:
            query: SQL query string

        Returns:
            pandas DataFrame with query results
        """
        if pd is None:
            raise ImportError("pandas is required for query_data_to_df.")
        query_job = self.client.query(query)
        df = query_job.to_dataframe()
        print(f"Query finished. {len(df)} rows retrieved as DataFrame.")
        return df

    def query_data_to_polars(self, query: str) -> Any:
        """Queries BigQuery and returns results as a polars DataFrame.

        Args:
            query: SQL query string

        Returns:
            polars DataFrame with query results
        """
        if pl is None:
            raise ImportError("polars is required for query_data_to_polars.")
        if pd is None:
            raise ImportError("pandas is required for query_data_to_polars.")
        query_job = self.client.query(query)
        df_pandas = query_job.to_dataframe()
        df_polars = pl.from_pandas(df_pandas)
        print(f"Query finished. {len(df_polars)} rows retrieved as Polars DataFrame.")
        return df_polars


class GoogleDatastore:
    """Helper class for Google Cloud Datastore operations."""

    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        """Initialize Google Datastore client.

        Args:
            project_id: Google Cloud project ID
            credentials_path: Optional path to credentials JSON file
        """
        _require_datastore_deps()
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        self.client = datastore.Client(project=project_id)

    def get(self, kind: str, entity_id: int) -> Optional[Any]:
        """Fetch any entity by kind and ID.

        Args:
            kind: Entity kind (table name)
            entity_id: Entity ID

        Returns:
            Entity object or None if not found
        """
        return self.client.get(self.client.key(kind, entity_id))

    def save(self, kind: str, data: Dict[str, Any], entity_id: Optional[int] = None) -> Any:
        """Create or update any entity.

        Args:
            kind: Entity kind (table name)
            data: Dictionary of entity data
            entity_id: Optional entity ID (creates new entity if not provided)

        Returns:
            Saved entity
        """
        key = self.client.key(kind, entity_id) if entity_id else self.client.key(kind)
        entity = datastore.Entity(key=key)
        entity.update(data)
        self.client.put(entity)
        return entity

    def list(self, kind: str, filters: Optional[List[Tuple[str, str, Any]]] = None,
             limit: Optional[int] = None, cursor: Optional[bytes] = None) -> Tuple[List[Any], Optional[str]]:
        """Generic list with filtering and pagination.

        Args:
            kind: Entity kind (table name)
            filters: Optional list of filters as (property, operator, value) tuples
            limit: Optional maximum number of entities to return
            cursor: Optional pagination cursor from previous query

        Returns:
            Tuple of (list of entities, next page cursor)
        """
        query = self.client.query(kind=kind)
        if filters:
            for prop, op, val in filters:
                query.add_filter(prop, op, val)
        query_iter = query.fetch(limit=limit, start_cursor=cursor)
        entities = list(query_iter)
        next_cursor = query_iter.next_page_token.decode('utf-8') if query_iter.next_page_token else None
        return entities, next_cursor

    def delete(self, kind: str, entity_id: int) -> None:
        """Delete any entity.

        Args:
            kind: Entity kind (table name)
            entity_id: Entity ID to delete
        """
        self.client.delete(self.client.key(kind, entity_id))

    def update_properties(self, kind: str, entity_id: int,
                          props_to_add: Optional[Dict[str, Any]] = None,
                          props_to_remove: Optional[List[str]] = None) -> Any:
        """Update entity properties by adding or removing fields.

        Args:
            kind: Entity kind (table name)
            entity_id: Entity ID to update
            props_to_add: Optional dictionary of properties to add/update
            props_to_remove: Optional list of property names to remove

        Returns:
            Updated entity

        Raises:
            ValueError: If entity not found
        """
        entity = self.get(kind, entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found.")
        if props_to_add:
            entity.update(props_to_add)
        if props_to_remove:
            for p in props_to_remove:
                entity.pop(p, None)
        self.client.put(entity)
        return entity
