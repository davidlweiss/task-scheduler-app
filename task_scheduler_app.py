import streamlit as st
import pandas as pd
import os
from datetime import datetime

# File paths
tasks_file = 'tasks.csv'
free_time_file = 'free_time.csv'

st.title("Dynamic Task Scheduler V6")

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

if st.checkbox("Enable Sorting Mode (View Only)"):
    st.dataframe(tasks_df, use_container_width=True)
else:
    st.data_editor(tasks_df, num_rows="dynamic", use_container_width=True, column_config={"Task": st.column_config.Column(width='large')}, disabled=False)

st.subheader("Edit Free Time Windows")
st.data_editor(free_time_df, num_rows="dynamic", use_container_width=True, disabled=False)

# Save edited data
tasks_df.to_csv(tasks_file, index=False)
free_time_df.to_csv(free_time_file, index=False)

# Decision Results Storage
if 'action_results' not in st.session_state:
    st.session_state['action_results'] = []

# Run Scheduler Button
if st.button("Run Scheduler") or 'rerun_scheduler' in st.session_state:

    st.subheader("Scheduled Tasks")

    total_free_time = free_time_df['Available Hours'].sum()
    total_estimated_time = tasks_df['Estimated Time'].sum()

    st.markdown(f"### Capacity vs Demand")
    st.markdown(f"Total Free Time: **{total_free_time} hours**")
    st.markdown(f"Total Task Demand: **{total_estimated_time} hours**")

    if total_estimated_time > total_free_time:
        st.warning(f"You are over capacity by {total_estimated_time - total_free_time} hours. Consider reducing tasks, adding free time, or moving due dates.")
    else:
        st.success(f"You have {total_free_time - total_estimated_time} hours of free capacity remaining.")

    st.markdown("### Daily Capacity vs Demand")
    daily_summary = free_time_df.groupby('Date')['Available Hours'].sum().reset_index().rename(columns={'Available Hours': 'Total Available'})

    if not tasks_df.empty:
        scheduled_tasks = []
        warnings = []

        today = pd.to_datetime(datetime.today().date())
        tasks_df['Due Date'] = pd.to_datetime(tasks_df['Due Date'], errors='coerce')
        free_time_df['Date'] = pd.to_datetime(free_time_df['Date'])
        free_time_df = free_time_df.sort_values(by='Date')

        def calc_priority(row):
            days_until_due = (row['Due Date'] - today).days if pd.notnull(row['Due Date']) else 9999
            return days_until_due * 1 - row['Importance'] * 5

        tasks_df['Priority Score'] = tasks_df.apply(calc_priority, axis=1)
        tasks_df = tasks_df.sort_values(by=['Priority Score', 'Complexity'])

        for idx, task in tasks_df.iterrows():
            task_time_remaining = task['Estimated Time']
            task_name = task['Task']
            due_date = task['Due Date']

            if task_time_remaining > 6:
                warnings.append(f"Task '{task_name}' exceeds 6 hours and should probably be split unless it's a Work Block.")

            for f_idx, window in free_time_df.iterrows():
                if task_time_remaining <= 0:
                    break

                if pd.notnull(due_date) and window['Date'] > due_date:
                    break

                available_hours = window['Available Hours']
                if available_hours > 0:
                    allocated_time = min(task_time_remaining, available_hours)
                    scheduled_tasks.append({'Task': task_name, 'Date': window['Date'], 'Allocated Hours': allocated_time})
                    free_time_df.at[f_idx, 'Available Hours'] -= allocated_time
                    task_time_remaining -= allocated_time

            if pd.notnull(due_date) and task_time_remaining > 0:
                warnings.append(f"HANDLE: {task_name} (Due: {due_date.date()}) needs {task['Estimated Time']}h, but only {task['Estimated Time']-task_time_remaining}h scheduled before due date.")

        scheduled_df = pd.DataFrame(scheduled_tasks)

        # Filter scheduled_df to only include dates in free_time_df
        scheduled_df = scheduled_df[scheduled_df['Date'].isin(free_time_df['Date'])]

        daily_scheduled = scheduled_df.groupby('Date')['Allocated Hours'].sum().reset_index().rename(columns={'Allocated Hours': 'Total Scheduled'})
        
        # Ensure both Date columns are datetime
        daily_summary['Date'] = pd.to_datetime(daily_summary['Date'])
        daily_scheduled['Date'] = pd.to_datetime(daily_scheduled['Date'])
        daily_summary = daily_summary.merge(daily_scheduled, on='Date', how='left').fillna(0)

        st.dataframe(daily_summary)

        if not scheduled_df.empty:
            pivot_df = scheduled_df.pivot(index='Task', columns='Date', values='Allocated Hours').fillna('')
            non_empty_cols = pivot_df.columns[pivot_df.notna().any()].tolist()
            empty_cols = pivot_df.columns[~pivot_df.notna().any()].tolist()
            ordered_cols = non_empty_cols + empty_cols
            pivot_df = pivot_df[ordered_cols]

            st.dataframe(pivot_df)
        else:
            st.write("No scheduled tasks yet.")

        if warnings:
            st.subheader("Warnings & Handle Options")
            for warning in warnings:
                st.warning(warning)

    if 'rerun_scheduler' in st.session_state:
        del st.session_state['rerun_scheduler']
