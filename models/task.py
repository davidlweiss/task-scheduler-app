import pandas as pd
from datetime import datetime
import math
from utils.db_utils import table_to_df, df_to_table, execute_query

def load_tasks():
    """
    Load tasks from the SQLite database.
    """
    return table_to_df('tasks')

def save_tasks(tasks_df):
    """
    Save tasks to the SQLite database.
    """
    return df_to_table(tasks_df, 'tasks')

def add_task(task_data):
    """
    Add a new task to the database.
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
        estimated_time = float(task['Estimated Time']) if pd.notnull(task['Estimated Time']) else 0
        if estimated_time > 6 and not any(tag in str(task['Task']) for tag in ['[MULTI-SESSION]', '[FIXED EVENT]', '[PENDING PLANNING]']):
            large_tasks.append((idx, task))
    
    return large_tasks

def calculate_task_priority(tasks_df):
    """
    Calculate priority score for each task.
    """
    today = pd.to_datetime(datetime.today().date())
    
    def calc_priority(row):
        # Ensure Importance is a number
        importance = float(row['Importance']) if pd.notnull(row['Importance']) else 0
        
        # Calculate days until due, handling null values
        if pd.isnull(row['Due Date']):
            days_until_due = 9999  # Large number for tasks with no due date
        else:
            days_until_due = (row['Due Date'] - today).days
            
        # Calculate the priority score
        return days_until_due * 1 - importance * 5
    
    tasks_df['Priority Score'] = tasks_df.apply(calc_priority, axis=1)
    return tasks_df.sort_values(by=['Priority Score', 'Complexity'])
