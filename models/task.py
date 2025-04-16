import pandas as pd
import os
from datetime import datetime
import math

# File path
TASKS_FILE = 'tasks.csv'

def load_tasks():
    """
    Load tasks from CSV file or create a new DataFrame if file doesn't exist.
    """
    if os.path.exists(TASKS_FILE):
        df = pd.read_csv(TASKS_FILE)
        # Ensure due date is properly formatted
        if 'Due Date' in df.columns:
            df['Due Date'] = pd.to_datetime(df['Due Date'], errors='coerce')
        return df
    else:
        return pd.DataFrame(columns=['Project', 'Task', 'Estimated Time', 'Due Date', 'Importance', 'Complexity'])

def save_tasks(tasks_df):
    """
    Save tasks to CSV file.
    """
    tasks_df.to_csv(TASKS_FILE, index=False)
    return True

def add_task(task_data):
    """
    Add a new task to the tasks file.
    """
    tasks_df = load_tasks()
    new_task = pd.DataFrame([task_data])
    tasks_df = pd.concat([tasks_df, new_task], ignore_index=True)
    return save_tasks(tasks_df)

def delete_task(task_idx):
    """
    Delete a task by index.
    """
    tasks_df = load_tasks()
    tasks_df = tasks_df.drop(task_idx)
    return save_tasks(tasks_df)

def update_task(task_idx, task_data):
    """
    Update an existing task.
    """
    tasks_df = load_tasks()
    for key, value in task_data.items():
        tasks_df.at[task_idx, key] = value
    return save_tasks(tasks_df)

def get_large_tasks():
    """
    Identify large tasks that might need to be broken down.
    """
    tasks_df = load_tasks()
    large_tasks = []
    
    for idx, task in tasks_df.iterrows():
        if task['Estimated Time'] > 6 and not any(tag in str(task['Task']) for tag in ['[MULTI-SESSION]', '[FIXED EVENT]', '[PENDING PLANNING]']):
            large_tasks.append((idx, task))
    
    return large_tasks

def calculate_task_priority(tasks_df):
    """
    Calculate priority score for each task.
    """
    today = pd.to_datetime(datetime.today().date())
    
    def calc_priority(row):
        days_until_due = (row['Due Date'] - today).days if pd.notnull(row['Due Date']) else 9999
        return days_until_due * 1 - row['Importance'] * 5
    
    tasks_df['Priority Score'] = tasks_df.apply(calc_priority, axis=1)
    return tasks_df.sort_values(by=['Priority Score', 'Complexity'])
