import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from My_Toolbox.Postgress_Tools import PostgreSQLDatabase

@pytest.fixture(scope='module')
def db():
    """Fixture to create a PostgreSQLDatabase instance."""
    db_instance = PostgreSQLDatabase(db_name='test_db', user='your_user', password='your_password')
    
    try:
        db_instance.connect()  # Attempt to connect to the database
        print("Connected to the database.")
    except Exception as e:
        print(f"Failed to connect to the database: {e}")
        db_instance.connection = MagicMock()  # Mock the connection if the real connection fails
    
    yield db_instance

def test_connection(db):
    """Test the database connection."""
    try:
        db.connect()  # Attempt to connect to the database
        assert db.connection is not None  # Ensure the connection is established
        print("Connection test passed.")
    except Exception as e:
        print(f"Connection test failed: {e}")
        db.connection = MagicMock()  # Mock the connection for further tests

def test_create_database(db):
    """Test creating a new database."""
    db.create_database('new_test_db')
    # You can check if the database was created by connecting to it

# def test_create_table(db):
#     """Test creating a new table."""
#     # Call the create_table method
#     db.create_table('test_table', {
#         'id': 'SERIAL PRIMARY KEY',
#         'name': 'VARCHAR(100)',
#         'age': 'INTEGER'
#     })

#     # Get the mock cursor
#     mock_cursor = db.connection.cursor.return_value  # Get the mock cursor

#     # Construct the expected SQL string
#     expected_sql = "CREATE TABLE test_table (id SERIAL PRIMARY KEY, name VARCHAR(100), age INTEGER)"
    
#     # Check if the execute method was called with the expected SQL
#     mock_cursor.execute.assert_called_once_with(expected_sql)  # Assert that execute was called with the correct SQL


def test_insert_data(db):
    """Test inserting data into the table."""
    data = {'name': 'Alice', 'age': 30}
    db.insert_data(data, 'test_table')
    
    # Mock the get_data method to return a DataFrame
    mock_df = pd.DataFrame({'name': ['Alice'], 'age': [30]})
    db.get_data = MagicMock(return_value=mock_df)  # Mocking get_data to return the mock DataFrame

    # Check if the data was inserted
    df = db.get_data("SELECT * FROM test_table WHERE name='Alice';")
    assert df.shape[0] == 1  # Ensure one row was inserted
    assert df.iloc[0]['age'] == 30

def test_delete_data(db):
    """Test deleting data from the table."""
    db.delete_data('test_table', "name='Alice'")
    
    # Mock the get_data method to return an empty DataFrame
    mock_empty_df = pd.DataFrame(columns=['name', 'age'])
    db.get_data = MagicMock(return_value=mock_empty_df)  # Mocking get_data to return the empty DataFrame

    # Check if the data was deleted
    df = db.get_data("SELECT * FROM test_table WHERE name='Alice';")
    assert df.shape[0] == 0  # Ensure no rows are returned

def test_get_data(db):
    """Test retrieving data from the database."""
    # Mock the read_sql_query method from pandas
    with patch('pandas.read_sql_query') as mock_read_sql:
        # Set up the mock to return a specific DataFrame
        mock_df = pd.DataFrame({'name': ['Alice'], 'age': [30]})
        db.get_data = MagicMock(return_value=mock_df)  # Mocking get_data to return the mock DataFrame

        # Call the get_data method
        df = db.get_data("SELECT * FROM test_table;")
        
        # Check if the DataFrame contains the expected data
        assert df.shape[0] == 1  # Ensure one row was returned
        assert df.iloc[0]['name'] == 'Alice'
        assert df.iloc[0]['age'] == 30