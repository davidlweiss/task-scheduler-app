import pandas as pd
import os

# File path
FREE_TIME_FILE = 'free_time.csv'

def load_free_time():
    """
    Load free time data from CSV or create a new DataFrame if file doesn't exist.
    """
    if os.path.exists(FREE_TIME_FILE):
        df = pd.read_csv(FREE_TIME_FILE)
        # Ensure date is properly formatted
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        return df
    else:
        return pd.DataFrame(columns=['Date', 'Available Hours'])

def save_free_time(free_time_df):
    """
    Save free time data to CSV file.
    """
    free_time_df.to_csv(FREE_TIME_FILE, index=False)
    return True

def add_free_time(date, hours):
    """
    Add hours to a specific date.
    """
    free_time_df = load_free_time()
    date = pd.to_datetime(date)
    
    # Check if date already exists
    if not free_time_df.empty and date in free_time_df['Date'].values:
        idx = free_time_df[free_time_df['Date'] == date].index[0]
        free_time_df.at[idx, 'Available Hours'] += hours
    else:
        new_row = pd.DataFrame({'Date': [date], 'Available Hours': [hours]})
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
        current_hours = free_time_df.at[idx, 'Available Hours']
        new_hours = max(0, current_hours - hours)  # Prevent negative hours
        
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
    return free_time_df['Available Hours'].sum() if not free_time_df.empty else 0

def delete_free_time(idx):
    """
    Delete a free time entry by index.
    """
    free_time_df = load_free_time()
    free_time_df = free_time_df.drop(idx)
    return save_free_time(free_time_df)
