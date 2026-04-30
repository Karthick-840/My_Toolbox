from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import pandas as pd
import os

import psycopg2
from psycopg2 import sql

class PostgreSQLDatabase:
    def __init__(self, db_name, user, password, host='localhost', port='5432'):
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        """Connect to the PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            print("Connection to database successful.")
        except Exception as e:
            print(f"Error connecting to database: {e}")

    def create_database(self, new_db_name):
        """Create a new database."""
        try:
            with psycopg2.connect(user=self.user, password=self.password, host=self.host, port=self.port) as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(new_db_name)))
                    print(f"Database '{new_db_name}' created successfully.")
        except Exception as e:
            print(f"Error creating database: {e}")

    def create_table(self, table_name, columns):
        """Create a table in the database."""
        if self.connection is None:
            self.connect()
        
        try:
            with self.connection.cursor() as cursor:
                columns_with_types = ', '.join(f"{col} {dtype}" for col, dtype in columns.items())
                print("Executing SQL ")  # Debugging statement
                cursor.execute(f"CREATE TABLE {table_name} ({columns_with_types})")
                print(f"Table '{table_name}' created successfully.")
        except Exception as e:
            print(f"Error creating table: {e}")

    def get_data(self, query):
        """Retrieve data from the PostgreSQL database."""
        if self.connection is None:
            self.connect()
        
        try:
            df = pd.read_sql_query(query, self.connection)
            return df
        except Exception as e:
            print(f"Error retrieving data: {e}")
            return None

    def insert_data(self, data, tbl,schema_name='public', mode='append', postgis=False):
        """Insert a single row or load a DataFrame into PostgreSQL."""
        if self.connection is None:
            self.connect()
        
        try:
            # Convert dictionary to DataFrame if data is a dict
            if isinstance(data, dict):
                data = pd.DataFrame([data])  # Convert to DataFrame with one row

            if isinstance(data, pd.DataFrame):
                # Load DataFrame
                engine = create_engine(f'postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}')
                data.to_sql(tbl, engine, schema=schema_name, if_exists=mode, index=False, chunksize=100000)
                print(f"Data loaded successfully into table '{tbl}'.")
            else:
                print("Unsupported data type. Please provide a DataFrame or a dictionary.")
        except Exception as e:
            print(f"Error during insert or load: {e}")
    
    def delete_data(self, table_name, condition):
        """Delete data from the table based on a condition."""
        if self.connection is None:
            self.connect()
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql.SQL("DELETE FROM {} WHERE {}").format(sql.Identifier(table_name), sql.SQL(condition)))
                print("Data deleted successfully.")
        except Exception as e:
            print(f"Error deleting data: {e}")

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            print("Database connection closed.")
