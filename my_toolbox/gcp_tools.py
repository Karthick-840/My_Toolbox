import os
import base64
import csv
from datetime import datetime

import gspread
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe
from google.auth.exceptions import GoogleAuthError
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account
import json

from pprint import pprint
from google.cloud import storage, datastore, bigquery

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

class GoogleSheets:
    def __init__(self,sheet_id,settings=None,logger=None,scopes=None):
        
        self.SF = settings.SF
        self.DS = settings.DS
        self.DATE = settings.DATE
        
        self.input_folder = settings.INPUT_FOLDER
        self.output_folder = settings.OUTPUT_FOLDER

        if logger:
            self.logger = logger.info('IGspread Function Initiated')
            self.logger = logger.getChild(__name__)
        
        self.sheet_id = sheet_id
        if not scopes:
            SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        self.sheet = self.check_credentials(self.sheet_id, scopes=SCOPES)

    def check_credentials(self,sheet_id,scopes):
        creds,sheet = None, None
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Get the parent directory path
        token_path = os.path.join(parent_dir, "token.json")  # Build the path to token.json in the parent directory

        try:
            if os.path.exists(token_path):
                creds = Credentials.from_service_account_file(token_path, scopes=scopes)
                client = gspread.authorize(creds)
                sheet = client.open_by_key(sheet_id)
                self.logger.info("Authentication successful.")
                
            else:
                self.logger.info(" Authentication Token is missing")     
            
        except GoogleAuthError as auth_error:
            # If there's an authentication error, return the error message
           self.logger.info(f"Authentication failed: {str(auth_error)}")
        
        except Exception as e:
            # Handle any other errors that may occur
            self.logger.info(f"An error occurred: {str(e)}")

        return sheet

    def get_workbook(self):
        
        for worksheet in self.sheet.worksheets():
            sheet_name = worksheet.title
            values = worksheet.get_all_values()

            # Define the file path within the output folder
            file_path = os.path.join(self.input_folder, f"{sheet_name}.txt")
            
            # Write the sheet's data to a text file in the output folder. Change this to use DS.
            with open(file_path, "w") as f:
                for row in values:
                    f.write("\t".join(row) + "\n")
            
            self.logger.info(f"Saved {file_path}")

    def write_dataframe_to_sheet(self, dataframe, worksheet_name):
        """Write a DataFrame to a specified worksheet in a Google Sheets file."""
        try:
                # Get all existing worksheets
            existing_worksheets = [ws.title for ws in self.sheet.worksheets()]

            if worksheet_name in existing_worksheets:
                # If the worksheet exists, clear it
                worksheet = self.sheet.worksheet(worksheet_name)
                worksheet.clear()
                self.logger.info(f"Cleared existing worksheet '{worksheet_name}'.")
            else:
                # If the worksheet does not exist, create it
                worksheet = self.sheet.add_worksheet(title=worksheet_name, rows="100", cols="20")
                self.logger.info(f"Created new worksheet '{worksheet_name}'.")

            # Write the DataFrame to the specified worksheet
            set_with_dataframe(worksheet, dataframe)
        
            self.logger.info(f"DataFrame written to {worksheet_name} in Google Sheets.")
        except Exception as e:
            self.logger.info(f"An error occurred while writing DataFrame to sheet: {str(e)}")

class GoogleCloudStorage:
    def __init__(self, credentials_path, project=None):
        """
        Initialize the Google Cloud Storage client.
        :param credentials_path: Path to the Google Cloud credentials JSON file.
        :param project: (Optional) Google Cloud project ID.
        """
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        self.storage_client = storage.Client(project=project)

    def list_buckets(self, max_results=100):
        """
        List all buckets in the project.
        :param max_results: Maximum number of buckets to list.
        :return: List of bucket names.
        """
        buckets = self.storage_client.list_buckets(max_results=max_results)
        bucket_names = [bucket.name for bucket in buckets]
        print("Buckets:")
        pprint(bucket_names)
        return bucket_names
    
    def get_bucket(self, bucket_name):
        """
        Retrieve a bucket.
        :param bucket_name: Name of the bucket to retrieve.
        :return: Bucket object.
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
        pprint(vars(bucket))
        pprint(details)
        return bucket,details

    def create_bucket(self, bucket_name, storage_class='COLDLINE', location='US'):
        """
        Create a new bucket.
        :param bucket_name: Name of the bucket to create.
        :param storage_class: Storage class of the bucket (e.g., 'COLDLINE', 'STANDARD').
        :param location: Location of the bucket (e.g., 'US', 'EU').
        :return: Bucket object.
        """
        bucket = self.storage_client.bucket(bucket_name)
        bucket.storage_class = storage_class
        bucket.location = location
        bucket = self.storage_client.create_bucket(bucket)
        pprint(vars(bucket))
        return bucket

    def upload_to_bucket(self, blob_name, file_path, bucket_name):
        """
        Upload a file to a bucket.
        :param blob_name: Name of the blob (object) in the bucket.
        :param file_path: Path to the local file to upload.
        :param bucket_name: Name of the target bucket.
        :return: Blob object.
        """
        bucket = self.storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(file_path)
        print(f"Uploaded {file_path} to {bucket_name} as {blob_name}.")
        return blob
    
    def download_file_from_bucket(self, blob_name, file_path, bucket_name):
        """
        Download a file from a bucket.
        :param blob_name: Name of the blob (object) in the bucket.
        :param file_path: Path to save the downloaded file locally.
        :param bucket_name: Name of the source bucket.
        """
        bucket = self.storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        with open(file_path, 'wb') as f:
            self.storage_client.download_blob_to_file(blob, f)
        print(f"Downloaded {blob_name} from {bucket_name} to {file_path}.")
    
    def download_file_uri(self, uri, file_path):
        """
        Download a file using its URI.
        :param uri: URI of the blob (e.g., 'gs://bucket_name/blob_name').
        :param file_path: Path to save the downloaded file locally.
        """
        with open(file_path, 'wb') as f:
            self.storage_client.download_blob_to_file(uri, f)
        print(f"Downloaded from {uri} to {file_path}.")

# class GoogleDatastore:
#     def __init__(self, project_id, credentials_path=None):
#         """
#         Initialize the Datastore client.
#         :param project_id: Google Cloud project ID.
#         :param credentials_path: (Optional) Path to the service account JSON credentials.
#         """
#         if credentials_path:
#             os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
#         self.client = datastore.Client(project=project_id)

#     def list_entities(self, kind, filters=None, limit=None, cursor=None):
#         """
#         List entities of a specific kind with optional filters.
#         :param kind: Datastore kind (e.g., 'Question', 'Book').
#         :param filters: List of filters as tuples [(property, operator, value)].
#         :param limit: Maximum number of entities to fetch.
#         :param cursor: Start cursor for pagination.
#         :return: List of entities and next cursor.
#         """
#         query = self.client.query(kind=kind)
#         if filters:
#             for prop, op, val in filters:
#                 query.add_filter(prop, op, val)
#         query_iterator = query.fetch(limit=limit, start_cursor=cursor)
#         entities = list(query_iterator)
#         next_cursor = query_iterator.next_page_token.decode('utf-8') if query_iterator.next_page_token else None
#         return entities, next_cursor

#     def get_entity(self, kind, entity_id):
#         """
#         Fetch a single entity by its key.
#         :param kind: Datastore kind.
#         :param entity_id: ID of the entity.
#         :return: Entity object or None.
#         """
#         key = self.client.key(kind, entity_id)
#         return self.client.get(key)

#     def save_entity(self, kind, data, entity_id=None):
#         """
#         Save (create or update) an entity.
#         :param kind: Datastore kind.
#         :param data: Dictionary of entity properties.
#         :param entity_id: (Optional) ID for the entity. If None, a new entity is created.
#         :return: Saved entity.
#         """
#         key = self.client.key(kind, entity_id) if entity_id else self.client.key(kind)
#         entity = datastore.Entity(key=key)
#         entity.update(data)
#         self.client.put(entity)
#         return entity

#     def delete_entity(self, kind, entity_id):
#         """
#         Delete an entity by its key.
#         :param kind: Datastore kind.
#         :param entity_id: ID of the entity.
#         """
#         key = self.client.key(kind, entity_id)
#         self.client.delete(key)
#         print(f"Entity {entity_id} deleted from kind {kind}.")

#     def batch_write(self, project, kind, csv_file, bucket):
#         """
#         Batch write data to Datastore using Apache Beam.
#         :param project: Google Cloud project ID.
#         :param kind: Datastore kind.
#         :param csv_file: Path to the CSV file in Cloud Storage.
#         :param bucket: Google Cloud Storage bucket name.
#         """
#         options = PipelineOptions(project=project)
#         p = beam.Pipeline(options=options)

#         def to_entity(line):
#             fields = line.split(',')  # Assuming CSV format: id,name,startYear,...
#             entity_id = int(fields[0])
#             key = Key([kind, entity_id])
#             entity = Entity(key)
#             entity.set_properties({
#                 'id': entity_id,
#                 'name': fields[1],
#                 'startYear': int(fields[2]),
#                 'endYear': int(fields[3]),
#                 'details': fields[4:]
#             })
#             return entity

#         lines = p | 'Read from Cloud Storage' >> beam.io.ReadFromText(f'gs://{bucket}/{csv_file}')
#         entities = lines | 'To Entity' >> beam.Map(to_entity)
#         entities | 'Write to Datastore' >> WriteToDatastore(project)
#         p.run().wait_until_finish()

#         print("Batch write completed.")

#     def list_kinds(self):
#         """
#         List all kinds in the Datastore project.
#         Note: Requires Datastore index access or query setup.
#         """
#         query = self.client.query(kind='__kind__')
#         kinds = [entity.key.id_or_name for entity in query.fetch()]
#         return kinds
    
#     # def create_database(self, db_name, metadata=None):
#     #     """
#     #     Simulates creating a database in Google Datastore.
#     #     :param db_name: Name of the logical database (kind).
#     #     :param metadata: Optional metadata to associate with the database.
#     #     :return: Created database entity.
#     #     """
#     #     kind = 'Database'
#     #     key = self.client.key(kind, db_name)  # Using the database name as the ID
#     #     entity = datastore.Entity(key=key)

#     #     entity.update({
#     #          'name': db_name,  # Explicitly set the 'name' property
#     #         'createdAt': datetime.utcnow().isoformat(),
#     #         'metadata': metadata or {}
#     #     })
#     #     self.client.put(entity)
#     #     print(f"Database '{db_name}' created with Metadata: {metadata}.")
#     #     return entity

#     # def list_databases(self):
#     #     query = self.client.query(kind='Database')
#     #     databases = list(query.fetch())
#     #     return databases
    
#     # def delete_database(self, db_name):
#     #     key = self.client.key('Database', db_name)
#     #     self.client.delete(key)
#     #     print(f"Database '{db_name}' deleted.")

#     # def add_property(self, db_name, property_name, property_value):
#     #     """
#     #     Adds a property to an existing database entity in Google Datastore.
#     #     :param db_name: Name of the logical database (used as key name).
#     #     :param property_name: Name of the property to add.
#     #     :param property_value: Value of the property to add.
#     #     :return: Updated entity.
#     #     """
#     #     key = self.client.key('Database', db_name)
#     #     entity = self.client.get(key)

#     #     if not entity:
#     #         raise ValueError(f"Database with name '{db_name}' does not exist.")

#     #     # Add or update the property
#     #     entity[property_name] = property_value
#     #     self.client.put(entity)
#     #     print(f"Property '{property_name}' added/updated successfully for '{db_name}'.")
#     #     return entity

#     # def remove_property(self, db_name, property_name):
#     #     """
#     #     Removes a property from an existing database entity in Google Datastore.
#     #     :param db_name: Name of the logical database (used as key name).
#     #     :param property_name: Name of the property to remove.
#     #     :return: Updated entity.
#     #     """
#     #     key = self.client.key('Database', db_name)
#     #     entity = self.client.get(key)

#     #     if not entity:
#     #         raise ValueError(f"Database with name '{db_name}' does not exist.")

#     #     # Remove the property if it exists
#     #     if property_name in entity:
#     #         del entity[property_name]
#     #         self.client.put(entity)
#     #         print(f"Property '{property_name}' removed successfully from '{db_name}'.")
#     #     else:
#     #         print(f"Property '{property_name}' does not exist in '{db_name}'.")
        
#     #     return entity

#     #  def create_thing(self, db_name, metadata=None):
#     #     """
#     #     Creates a new 'thing' entity with optional metadata.
#     #     :param db_name: Name of the 'thing'.
#     #     :param metadata: Optional metadata to associate with the 'thing'.
#     #     :return: Created entity.
#     #     """
#     #     key = self.client.key('Thing', db_name)
#     #     entity = datastore.Entity(key=key)
#     #     data = {
#     #         'name': db_name,
#     #         'createdAt': datetime.utcnow().isoformat(),
#     #         'metadata': metadata or {}
#     #     }
#     #     entity.update(data)
#     #     self.client.put(entity)
#     #     print(f"Thing '{db_name}' created.")
#     #     return entity

#     # def retrieve_thing(self, id):
#     #     """
#     #     Retrieves a 'thing' entity by its ID.
#     #     :param id: ID of the 'thing' to retrieve.
#     #     :return: Retrieved entity.
#     #     """
#     #     key = self.client.key('Thing', int(id))
#     #     return self.client.get(key)

#     # def update_thing(self, thing):
#     #     """
#     #     Updates an existing 'thing' entity.
#     #     :param thing: The entity to update.
#     #     :return: Updated entity.
#     #     """
#     #     self.client.put(thing)
#     #     print(f"Thing with ID {thing.key.id} updated.")
#     #     return thing

#     # def delete_thing(self, id):
#     #     """
#     #     Deletes a 'thing' entity by its ID.
#     #     :param id: ID of the 'thing' to delete.
#     #     """
#     #     key = self.client.key('Thing', int(id))
#     #     self.client.delete(key)
#     #     print(f"Thing with ID {id} deleted.")

#     # def get_things(self):
#     #     """
#     #     Retrieves all 'thing' entities.
#     #     :return: List of entities.
#     #     """
#     #     result = []
#     #     query = self.client.query(kind='Thing')
#     #     for entity in query.fetch():
#     #         result.append(entity)
#     #     return result

#     # def add_property(self, db_name, property_name, property_value):
#     #     """
#     #     Adds a property to an existing 'thing' entity.
#     #     :param db_name: Name of the 'thing'.
#     #     :param property_name: Property name to add.
#     #     :param property_value: Property value to add.
#     #     :return: Updated entity.
#     #     """
#     #     key = self.client.key('Thing', db_name)
#     #     entity = self.client.get(key)
        
#     #     if not entity:
#     #         raise ValueError(f"Thing with name '{db_name}' does not exist.")
        
#     #     entity[property_name] = property_value
#     #     self.client.put(entity)
#     #     print(f"Property '{property_name}' added/updated successfully for '{db_name}'.")
#     #     return entity

#     # def remove_property(self, db_name, property_name):
#     #     """
#     #     Removes a property from an existing 'thing' entity.
#     #     :param db_name: Name of the 'thing'.
#     #     :param property_name: Property name to remove.
#     #     :return: Updated entity.
#     #     """
#     #     key = self.client.key('Thing', db_name)
#     #     entity = self.client.get(key)
        
#     #     if not entity:
#     #         raise ValueError(f"Thing with name '{db_name}' does not exist.")
        
#     #     if property_name in entity:
#     #         del entity[property_name]
#     #         self.client.put(entity)
#     #         print(f"Property '{property_name}' removed successfully from '{db_name}'.")
#     #     else:
#     #         print(f"Property '{property_name}' does not exist in '{db_name}'.")
        
#     #     return entity

class GoogleBigQueryHelper:
    def __init__(self, project_id=None, credentials_json=None):
        """
        Initializes the BigQuery Helper.
        :param project_id: Google Cloud Project ID (if not set, defaults to environment variable).
        :param credentials_json: Path to service account credentials JSON (optional).
        """
        if credentials_json:
            self.credentials = service_account.Credentials.from_service_account_file(credentials_json)
            self.client = bigquery.Client(project=project_id, credentials=self.credentials)
        else:
            self.client = bigquery.Client(project=project_id)

    def create_dataset(self, dataset_name):
        """
        Creates a new dataset in BigQuery.
        :param dataset_name: Name of the dataset to create.
        :return: Created dataset.
        """
        dataset_id = f"{self.client.project}.{dataset_name}"
        dataset = bigquery.Dataset(dataset_id)
        
        try:
            dataset = self.client.create_dataset(dataset)  # API request
            print(f"Dataset {dataset_name} created successfully.")
            return dataset
        except NotFound:
            print(f"Dataset {dataset_name} already exists.")
            return None

    def infer_schema_from_csv(self, csv_file_path):
        """
        Infers the schema from a CSV file by checking the headers and first few rows.
        :param csv_file_path: Path to the CSV file.
        :return: A list of BigQuery schema fields.
        """
        with open(csv_file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # Read the first row (headers)

            # Read the first few rows to infer types (up to 10 rows for inference)
            sample_rows = []
            for i, row in enumerate(reader):
                if i >= 10:  # Limit to 10 rows for performance
                    break
                sample_rows.append(row)

            # Define a function to infer the type of each column
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

            # Initialize schema fields list
            schema_fields = []
            for col_index, header in enumerate(headers):
                # Use the first row of sample data to infer the type
                sample_value = sample_rows[0][col_index] if sample_rows else ''
                col_type = infer_type(sample_value)
                schema_fields.append(bigquery.SchemaField(header, col_type, mode="NULLABLE"))

            return schema_fields

    def create_table_from_csv(self, dataset_name, table_name, csv_file_path):
        """
        Creates a BigQuery table from a CSV file's schema.
        :param dataset_name: Dataset name.
        :param table_name: Table name.
        :param csv_file_path: Path to the CSV file.
        :return: Created BigQuery table.
        """
        schema = self.infer_schema_from_csv(csv_file_path)
        return self.create_table(dataset_name, table_name, schema)

    def create_table(self, dataset_name, table_name, schema):
        """
        Creates a new table in the specified dataset.
        :param dataset_name: Dataset name.
        :param table_name: Table name.
        :param schema: List of bigquery.SchemaField objects representing table schema.
        :return: Created table.
        """
        dataset_ref = self.client.dataset(dataset_name)
        table_ref = dataset_ref.table(table_name)
        table = bigquery.Table(table_ref, schema=schema)
        
        try:
            table = self.client.create_table(table)  # API request
            print(f"Table {table_name} created in dataset {dataset_name}.")
            return table
        except NotFound:
            print(f"Table {table_name} already exists in dataset {dataset_name}.")
            return None

    def insert_rows(self, dataset_name, table_name, rows):
        """
        Inserts rows of data into a BigQuery table.
        :param dataset_name: Dataset name.
        :param table_name: Table name.
        :param rows: List of rows to insert into the table (as dictionaries).
        :return: Insertion status.
        """
        dataset_ref = self.client.dataset(dataset_name)
        table_ref = dataset_ref.table(table_name)
        table = self.client.get_table(table_ref)  # Fetch the table schema
        
        errors = self.client.insert_rows_json(table, rows)  # Insert rows
        if errors == []:
            print(f"Successfully inserted rows into {table_name}.")
        else:
            print(f"Errors occurred while inserting rows: {errors}")
        return errors

    def query_data(self, query):
        """
        Queries BigQuery using SQL.
        :param query: SQL query string.
        :return: Query results.
        """
        query_job = self.client.query(query)  # Make an API request.
        
        results = query_job.result()  # Wait for the query to finish.
        print(f"Query finished. {len(results)} rows retrieved.")
        return results

    def read_table(self, dataset_name, table_name):
        """
        Reads all rows from a BigQuery table.
        :param dataset_name: Dataset name.
        :param table_name: Table name.
        :return: Table rows as a list of dictionaries.
        """
        dataset_ref = self.client.dataset(dataset_name)
        table_ref = dataset_ref.table(table_name)
        table = self.client.get_table(table_ref)  # Fetch the table
        rows = self.client.list_rows(table)  # List all rows
        
        result = [dict(row.items()) for row in rows]
        print(f"Read {len(result)} rows from {table_name}.")
        return result