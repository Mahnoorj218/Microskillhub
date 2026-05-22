import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    """
    Establishes and returns a connection to the MySQL database.
    Autocommit is set to False to explicitly control transactions.
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "microskillhub"),
            autocommit=False
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        raise e

def get_db_cursor():
    """
    Establishes a connection and returns both the connection and a dictionary cursor.
    The dictionary=True argument ensures that query results are returned as Python dictionaries.
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        return connection, cursor
    except Error as e:
        print(f"Error creating database cursor: {e}")
        raise e

def close_db(connection=None, cursor=None):
    """
    Safely closes the provided database cursor and connection.
    """
    try:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
    except Error as e:
        print(f"Error while closing database resources: {e}")