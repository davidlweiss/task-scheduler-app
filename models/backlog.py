import pandas as pd
import os
from datetime import datetime

# File path
BACKLOG_FILE = 'backlog.csv'

def load_backlog():
    """
    Load backlog data from CSV or create a new DataFrame if file doesn't exist.
    """
    if os.path.exists(BACKLOG_FILE):
        df = pd.read_csv(BACKLOG_FILE)
        # Ensure dates are properly formatted
        if 'Creation Date' in df.columns:
            df['Creation Date'] = pd.to_datetime(df['Creation Date'])
        return df
    else:
        return pd.DataFrame(columns=['Idea', 'Category', 'Description', 'Creation Date', 'Status'])

def save_backlog(backlog_df):
    """
    Save backlog data to CSV file.
    """
    backlog_df.to_csv(BACKLOG_FILE, index=False)
    return True

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
