import pandas as pd
from utils.db_utils import table_to_df, df_to_table, execute_query

def load_free_time():
    """
    Load free time data from SQLite database.
    """
    return table_to_df('free_time')

def save_free_time(free_time_df):
    """
    Save free time data to SQLite database.
    """
    return df_to_table(free_time_df, 'free_time')

def add_free_time(date, hours):
    """
    Add hours to a specific date.
    """
    free_time_df = load_free_time()
    date = pd.to_datetime(date)
    
    # Check if date already exists
    if not free_time_df.empty and date in free_time_df['Date'].values:
        idx = free_time_df[free_time_df['Date'] == date].index[0]
        free_time_df.at[idx, 'Available Hours'] += float(hours)
    else:
        new_row = pd.DataFrame({'Date': [date], 'Available Hours': [float(hours)]})
        free_time_df = pd.concat([free_time_df, new_row], ignore_index=True)
    
    return save_free_time(free_time_df)

def subtract_free_time(date, hours):
    """
    Subtract hours from a specific date.
    """
    free_time_df = load_free_time()
    date = pd.to_datetime(date)
    
    # Check if date exists
    if not free_time_df.empty and date in free_time_df['Date'].values:
        idx = free_time_df[free_time_df['Date'] == date].index[0]
        current_hours = float(free_time_df.at[idx, 'Available Hours'])
        new_hours = max(0, current_hours - float(hours))  # Prevent negative hours
        
        if new_hours == 0:
            # Remove the date if hours reduced to 0
            free_time_df = free_time_df.drop(idx)
        else:
            free_time_df.at[idx, 'Available Hours'] = new_hours
            
        return save_free_time(free_time_df)
    else:
        return False  # Cannot subtract from non-existent date

def get_total_free_time():
    """
    Calculate total available free time across all dates.
    """
    free_time_df = load_free_time()
    
    if free_time_df.empty:
        return 0
    
    # Ensure we're summing numeric values
    free_time_df['Available Hours'] = pd.to_numeric(free_time_df['Available Hours'], errors='coerce').fillna(0)
    
    # Sum the values
    total = free_time_df['Available Hours'].sum()
    
    return float(total)

def delete_free_time(idx):
    """
    Delete a free time entry by index.
    """
    free_time_df = load_free_time()
    free_time_df = free_time_df.drop(idx)
    return save_free_time(free_time_df)
