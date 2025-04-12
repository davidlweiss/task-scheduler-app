
import streamlit as st
import pandas as pd

st.title("Dynamic Task Scheduler")

st.sidebar.header("Upload your data")

# Upload tasks file
tasks_file = st.sidebar.file_uploader("Upload Tasks CSV", type=["csv"])

# Upload free time file
free_time_file = st.sidebar.file_uploader("Upload Free Time CSV", type=["csv"])

if tasks_file and free_time_file:
    tasks_df = pd.read_csv(tasks_file)
    free_time_df = pd.read_csv(free_time_file)

    st.subheader("Your Tasks")
    st.dataframe(tasks_df)

    st.subheader("Your Free Time Windows")
    st.dataframe(free_time_df)

    st.subheader("Scheduled Tasks")

    # Basic scheduling logic
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
    st.dataframe(scheduled_df.pivot(index='Task', columns='Date', values='Allocated Hours').fillna(''))
else:
    st.write("Please upload both CSV files to see the schedule.")
