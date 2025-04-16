import pandas as pd
import os
from datetime import datetime
from utils.db_utils import table_to_df, df_to_table, execute_query

def load_backlog():
    """
    Load backlog data from SQLite database.
    """
    return table_to_df('backlog')

def save_backlog(backlog_df):
    """
    Save backlog data to SQLite database.
    """
    return df_to_table(backlog_df, 'backlog')

def add_backlog_item(idea_data):
    """
    Add a new item to the backlog.
    """
    backlog_df = load_backlog()
    
    # Ensure creation date is set if not provided
    if 'Creation Date' not in idea_data or pd.isna(idea_data['Creation Date']):
        idea_data['Creation Date'] = pd.Timestamp.now()
        
    new_item = pd.DataFrame([idea_data])
    backlog_df = pd.concat([backlog_df, new_item], ignore_index=True)
    return save_backlog(backlog_df)

def delete_backlog_item(idx):
    """
    Delete a backlog item by index.
    """
    backlog_df = load_backlog()
    backlog_df = backlog_df.drop(idx)
    return save_backlog(backlog_df)

def update_backlog_item(idx, item_data):
    """
    Update an existing backlog item.
    """
    backlog_df = load_backlog()
    for key, value in item_data.items():
        backlog_df.at[idx, key] = value
    return save_backlog(backlog_df)

def filter_backlog(categories=None, statuses=None):
    """
    Filter backlog by categories and/or statuses.
    """
    backlog_df = load_backlog()
    
    if not backlog_df.empty:
        if categories:
            backlog_df = backlog_df[backlog_df['Category'].isin(categories)]
        if statuses:
            backlog_df = backlog_df[backlog_df['Status'].isin(statuses)]
            
    return backlog_df
