
import streamlit as st
import pandas as pd
import os

# File paths
tasks_file = 'tasks.csv'
free_time_file = 'free_time.csv'

st.title("Dynamic Task Scheduler")

# Load or initialize data
def load_data(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=columns)

# Load data
tasks_df = load_data(tasks_file, ['Task', 'Estimated Time', 'Due Date', 'Importance', 'Complexity'])
free_time_df = load_data(free_time_file, ['Date', 'Available Hours'])

# Sidebar options
st.sidebar.header("Manage Data")

if st.sidebar.button("Reset Tasks"):
    tasks_df = tasks_df.iloc[0:0]
    tasks_df.to_csv(tasks_file, index=False)

if st.sidebar.button("Reset Free Time"):
    free_time_df = free_time_df.iloc[0:0]
    free_time_df.to_csv(free_time_file, index=False)

uploaded_tasks = st.sidebar.file_uploader("Upload Tasks CSV", type=["csv"])
if uploaded_tasks:
    tasks_df = pd.read_csv(uploaded_tasks)
    tasks_df.to_csv(tasks_file, index=False)

uploaded_free_time = st.sidebar.file_uploader("Upload Free Time CSV", type=["csv"])
if uploaded_free_time:
    free_time_df = pd.read_csv(uploaded_free_time)
    free_time_df.to_csv(free_time_file, index=False)

st.sidebar.download_button("Download Tasks CSV", tasks_df.to_csv(index=False), "tasks.csv")
st.sidebar.download_button("Download Free Time CSV", free_time_df.to_csv(index=False), "free_time.csv")

# Editable data tables
st.subheader("Edit Tasks")
tasks_df = st.data_editor(tasks_df, num_rows="dynamic")
tasks_df.to_csv(tasks_file, index=False)

st.subheader("Edit Free Time Windows")
free_time_df = st.data_editor(free_time_df, num_rows="dynamic")
free_time_df.to_csv(free_time_file, index=False)

# Scheduling logic
st.subheader("Scheduled Tasks")
scheduled_tasks = []

for _, task in tasks_df.iterrows():
    task_time_remaining = task['Estimated Time']
    task_name = task['Task']

    for idx, window in free_time_df.iterrows():
        if task_time_remaining <= 0:
            break

        available_hours = window['Available Hours']

        if available_hours > 0:
            allocated_time = min(task_time_remaining, available_hours)
            scheduled_tasks.append({
                'Task': task_name,
                'Date': window['Date'],
                'Allocated Hours': allocated_time
            })

            free_time_df.at[idx, 'Available Hours'] -= allocated_time
            task_time_remaining -= allocated_time

scheduled_df = pd.DataFrame(scheduled_tasks)

if not scheduled_df.empty:
    st.dataframe(scheduled_df.pivot(index='Task', columns='Date', values='Allocated Hours').fillna(''))
else:
    st.write("No scheduled tasks yet. Add tasks and free time to begin.")
