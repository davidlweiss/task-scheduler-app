import sqlite3
import os
import pandas as pd

# Database file path
DB_FILE = 'task_scheduler.db'

def initialize_database():
    """
    Initialize the SQLite database with necessary tables if they don't exist.
    """
    # Create the database file if it doesn't exist
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Create tasks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Project TEXT,
            Task TEXT,
            "Estimated Time" REAL,
            "Due Date" TEXT,
            Importance INTEGER,
            Complexity INTEGER,
            "Focus Sessions" INTEGER,
            "Session Length" REAL
        )
        ''')
        
        # Create free_time table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS free_time (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Date TEXT,
            "Available Hours" REAL
        )
        ''')
        
        # Create backlog table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS backlog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Idea TEXT,
            Category TEXT,
            Description TEXT,
            "Creation Date" TEXT,
            Status TEXT
        )
        ''')
        
        conn.commit()

def execute_query(query, params=None, fetch=False):
    """
    Execute a SQL query and optionally fetch results.
    
    Args:
        query (str): SQL query to execute
        params (tuple, optional): Parameters for the query
        fetch (bool, optional): Whether to fetch results
        
    Returns:
        List of results if fetch=True, otherwise None
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        if fetch:
            return cursor.fetchall()
        
        conn.commit()
    return None

def table_to_df(table_name):
    """
    Convert a table to a pandas DataFrame.
    
    Args:
        table_name (str): Name of the table
        
    Returns:
        pandas.DataFrame: DataFrame containing the table data
    """
    with sqlite3.connect(DB_FILE) as conn:
        try:
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            
            # Convert date strings to datetime objects where appropriate
            date_columns = ["Due Date", "Date", "Creation Date"]
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            return df
        except pd.errors.DatabaseError:
            # Table doesn't exist or is empty
            if table_name == 'tasks':
                return pd.DataFrame(columns=['Project', 'Task', 'Estimated Time', 'Due Date', 'Importance', 'Complexity'])
            elif table_name == 'free_time':
                return pd.DataFrame(columns=['Date', 'Available Hours'])
            elif table_name == 'backlog':
                return pd.DataFrame(columns=['Idea', 'Category', 'Description', 'Creation Date', 'Status'])

def df_to_table(df, table_name, if_exists='replace'):
    """
    Save a DataFrame to a table.
    
    Args:
        df (pandas.DataFrame): DataFrame to save
        table_name (str): Name of the table
        if_exists (str, optional): What to do if the table exists
        
    Returns:
        bool: True if successful
    """
    with sqlite3.connect(DB_FILE) as conn:
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
    return True

# Initialize the database when the module is imported
initialize_database()
