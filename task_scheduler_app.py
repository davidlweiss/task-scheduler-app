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
st.data_editor(tasks_df, num_rows="dynamic", use_container_width=True)
tasks_df.to_csv(tasks_file, index=False)

st.subheader("Edit Free Time Windows")
st.data_editor(free_time_df, num_rows="dynamic", use_container_width=True)
free_time_df.to_csv(free_time_file, index=False)

# Decision Results Storage
if 'action_results' not in st.session_state:
    st.session_state['action_results'] = []

# Focus View Toggle
focus_mode = st.checkbox("Enter Weekly Setup Mode (Focus View)")

# Run Scheduler Button
if st.button("Run Scheduler") or 'rerun_scheduler' in st.session_state:

    st.subheader("Scheduled Tasks")

    if 'rerun_scheduler' in st.session_state:
        del st.session_state['rerun_scheduler']

    today = pd.to_datetime(datetime.today().date())

    tasks_df['Due Date'] = pd.to_datetime(tasks_df['Due Date'], errors='coerce')
    free_time_df['Date'] = pd.to_datetime(free_time_df['Date'])
    free_time_df = free_time_df.sort_values(by='Date')

    def calc_priority(row):
        days_until_due = (row['Due Date'] - today).days if pd.notnull(row['Due Date']) else 9999
        return days_until_due * 1 - row['Importance'] * 5

    tasks_df['Priority Score'] = tasks_df.apply(calc_priority, axis=1)
    tasks_df = tasks_df.sort_values(by=['Priority Score', 'Complexity'])

    scheduled_tasks = []
    warnings = []

    def is_work_block(task_name):
        return 'Work Block' in task_name or 'Session' in task_name

    for idx, task in tasks_df.iterrows():
        task_time_remaining = task['Estimated Time']
        task_name = task['Task']
        due_date = task['Due Date']

        if task_time_remaining > 6 and not is_work_block(task_name):
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

    if focus_mode:
        st.subheader("Focus View: This Week")

        today = pd.to_datetime(datetime.today().date())
        end_of_week = today + pd.Timedelta(days=6 - today.weekday())

        due_soon = tasks_df[(tasks_df['Due Date'] <= end_of_week) & (tasks_df['Due Date'] >= today)]
        overdue = tasks_df[tasks_df['Due Date'] < today]

        st.write("### Overdue Tasks")
        st.dataframe(overdue if not overdue.empty else pd.DataFrame({'Message': ['None']}))

        st.write("### Tasks Due This Week")
        st.dataframe(due_soon if not due_soon.empty else pd.DataFrame({'Message': ['None']}))

        st.write("### Scheduled This Week")

        st.write("### Unscheduled Important Tasks")
        unscheduled = tasks_df[(tasks_df['Due Date'].isna()) & (tasks_df['Importance'] >= 4)]
        for idx, task in unscheduled.iterrows():
            st.write(f"- {task['Task']} ({task['Estimated Time']}h)")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"Create Work Block for {task['Task']}", key=f"workblock_{task['Task']}"):
                    tasks_df.loc[idx, 'Task'] = f"{task['Task']} (Work Block)"
                    tasks_df.to_csv(tasks_file, index=False)
                    st.experimental_rerun()
            with col2:
                if st.button(f"Combine Small Tasks", key=f"combine_{task['Task']}"):
                    pass  # Placeholder for future logic
            with col3:
                if st.button(f"Flag for Later", key=f"flag_{task['Task']}"):
                    if 'Status' not in tasks_df.columns:
                        tasks_df['Status'] = ''
                    tasks_df.loc[idx, 'Status'] = 'Revisit Later'
                    tasks_df.to_csv(tasks_file, index=False)
                    st.experimental_rerun()
        week_scheduled = scheduled_df[(scheduled_df['Date'] >= today) & (scheduled_df['Date'] <= end_of_week)]
        st.dataframe(week_scheduled if not week_scheduled.empty else pd.DataFrame({'Message': ['None']}))

    elif not scheduled_df.empty:
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

            if "HANDLE: " in warning:
                task_name = warning.split("HANDLE: ")[1].split(" (")[0]

                expand = st.session_state.get('open_task') == task_name

                with st.expander(f"Handle This Task for {task_name}", expanded=expand):
                    with st.form(key=f"form_{task_name}"):
                        action = st.radio(
                            "Choose an action:",
                            [
                                'Add More Free Time (manual)',
                                'Reduce Estimated Time',
                                'Move Due Date',
                                'Accept Partial Completion & Create Follow-up Task',
                                'Deprioritize Other Tasks',
                                'Skip for Now'
                            ],
                            key=f"action_{task_name}"
                        )

                        new_time = None
                        new_due_date = None

                        if action == 'Reduce Estimated Time':
                            new_time = st.number_input(
                                "Enter new estimated time (hours):",
                                min_value=0.5,
                                step=0.5,
                                value=task['Estimated Time'],
                                key=f"new_time_{task_name}"
                            )

                        if action == 'Move Due Date':
                            new_due_date = st.date_input(
                                "Pick new due date:",
                                key=f"new_due_date_{task_name}"
                            )

                        submitted = st.form_submit_button("Confirm and Apply Action")

                        if submitted:
                            st.session_state['open_task'] = task_name
                            if action == 'Reduce Estimated Time' and new_time:
                                tasks_df.loc[tasks_df['Task'] == task_name, 'Estimated Time'] = new_time
                                tasks_df.to_csv(tasks_file, index=False)
                                st.success(f"Updated Estimated Time to {new_time} hours")

                            elif action == 'Move Due Date' and new_due_date:
                                tasks_df.loc[tasks_df['Task'] == task_name, 'Due Date'] = pd.to_datetime(new_due_date)
                                tasks_df.to_csv(tasks_file, index=False)
                                st.success(f"Moved Due Date to {new_due_date}")

                            else:
                                st.info(f"Action '{action}' noted for {task_name}. Please adjust manually if needed.")

                            st.session_state['rerun_scheduler'] = True
                            st.button("Run Scheduler Again", key=f"rerun_{task_name}")
