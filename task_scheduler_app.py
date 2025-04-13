import streamlit as st
import pandas as pd
import os

# File paths
tasks_file = 'tasks.csv'
free_time_file = 'free_time.csv'

st.title("Dynamic Task Scheduler V4")

# Load or initialize data
def load_data(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=columns)

# Load data
tasks_df = load_data(tasks_file, ['Project', 'Task', 'Estimated Time', 'Due Date', 'Importance', 'Complexity'])
free_time_df = load_data(free_time_file, ['Date', 'Available Hours'])

# Sidebar controls
st.sidebar.header("Manage Data")

uploaded_tasks = st.sidebar.file_uploader("Upload Tasks CSV", type=["csv"])
if uploaded_tasks:
    tasks_df = pd.read_csv(uploaded_tasks)
    tasks_df.to_csv(tasks_file, index=False)

uploaded_free_time = st.sidebar.file_uploader("Upload Free Time CSV", type=["csv"])
if uploaded_free_time:
    free_time_df = pd.read_csv(uploaded_free_time)
    free_time_df.to_csv(free_time_file, index=False)

# Editable data tables
st.subheader("Edit Tasks")
tasks_df = st.data_editor(tasks_df, num_rows="dynamic")
tasks_df.to_csv(tasks_file, index=False)

st.subheader("Edit Free Time Windows")
free_time_df = st.data_editor(free_time_df, num_rows="dynamic")
free_time_df.to_csv(free_time_file, index=False)

# Run Scheduler Button
if st.button("Run Scheduler"):
    st.subheader("Scheduled Tasks")

    # Split tasks
    tasks_due = tasks_df.dropna(subset=['Due Date']).copy()
    tasks_due['Due Date'] = pd.to_datetime(tasks_due['Due Date'])
    tasks_due = tasks_due.sort_values(by=['Due Date', 'Importance', 'Complexity'])

    tasks_no_due = tasks_df[tasks_df['Due Date'].isna()].copy()
    tasks_no_due = tasks_no_due.sort_values(by=['Importance', 'Complexity'])

    free_time_df['Date'] = pd.to_datetime(free_time_df['Date'])
    free_time_df = free_time_df.sort_values(by='Date')

    scheduled_tasks = []
    warnings = []

    # Function to check if task is a Work Block
    def is_work_block(task_name):
        return 'Work Block' in task_name or 'Session' in task_name

    # Schedule due date tasks
    for _, task in tasks_due.iterrows():
        task_time_remaining = task['Estimated Time']
        task_name = task['Task']
        due_date = task['Due Date']

        if task_time_remaining > 6 and not is_work_block(task_name):
            warnings.append(f"Task '{task_name}' exceeds 6 hours and should probably be split unless it's a Work Block.")

        for idx, window in free_time_df.iterrows():
            if task_time_remaining <= 0:
                break
            if window['Date'] > due_date:
                break

            available_hours = window['Available Hours']
            if available_hours > 0:
                allocated_time = min(task_time_remaining, available_hours)
                scheduled_tasks.append({'Task': task_name, 'Date': window['Date'], 'Allocated Hours': allocated_time})
                free_time_df.at[idx, 'Available Hours'] -= allocated_time
                task_time_remaining -= allocated_time

        if task_time_remaining > 0:
            warnings.append(f"WARNING: {task_name} (Due: {due_date.date()}) needs {task['Estimated Time']}h, but only {task['Estimated Time']-task_time_remaining}h scheduled before due date.")

    # Schedule tasks with no due date
    for _, task in tasks_no_due.iterrows():
        task_time_remaining = task['Estimated Time']
        task_name = task['Task']

        if task_time_remaining > 6 and not is_work_block(task_name):
            warnings.append(f"Task '{task_name}' exceeds 6 hours and should probably be split unless it's a Work Block.")

        for idx, window in free_time_df.iterrows():
            if task_time_remaining <= 0:
                break

            available_hours = window['Available Hours']
            if available_hours > 0:
                allocated_time = min(task_time_remaining, available_hours)
                scheduled_tasks.append({'Task': task_name, 'Date': window['Date'], 'Allocated Hours': allocated_time})
                free_time_df.at[idx, 'Available Hours'] -= allocated_time
                task_time_remaining -= allocated_time

    scheduled_df = pd.DataFrame(scheduled_tasks)

    if not scheduled_df.empty:
        # Pivot and reorder columns to show non-empty first
        pivot_df = scheduled_df.pivot(index='Task', columns='Date', values='Allocated Hours').fillna('')
        non_empty_cols = pivot_df.columns[pivot_df.notna().any()].tolist()
        empty_cols = pivot_df.columns[~pivot_df.notna().any()].tolist()
        ordered_cols = non_empty_cols + empty_cols
        pivot_df = pivot_df[ordered_cols]

        st.dataframe(pivot_df)
    else:
        st.write("No scheduled tasks yet.")

    if warnings:
        st.subheader("Warnings")
        for warning in warnings:
            st.warning(warning)
