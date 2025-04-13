import streamlit as st
import pandas as pd
import os
from datetime import datetime

# File paths
tasks_file = 'tasks.csv'
free_time_file = 'free_time.csv'

st.title("Dynamic Task Scheduler V7")

# Load or initialize data
def load_data(file_path, columns):
    """
    Loads a CSV if present, else returns an empty DataFrame with specified columns.
    """
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
    edited_tasks_df = st.data_editor(
        tasks_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={"Task": st.column_config.Column(width='large')},
        disabled=False,
        key="task_editor"
    )
    # Save any changes to the tasks
    edited_tasks_df.to_csv(tasks_file, index=False)
    tasks_df = edited_tasks_df  # Update the main dataframe with edits

st.subheader("Manage Free Time Windows")

# Initialize free_time_df with correct types
if 'Date' in free_time_df.columns:
    free_time_df['Date'] = pd.to_datetime(free_time_df['Date'])
    
# Create sessions states for the free time management
if 'free_time_date' not in st.session_state:
    st.session_state.free_time_date = datetime.today()
if 'free_time_hours' not in st.session_state:
    st.session_state.free_time_hours = 1.0

# Remove Sort Order column if it exists
if 'Sort Order' in free_time_df.columns:
    free_time_df = free_time_df.drop('Sort Order', axis=1)

# Add new free time window with a form
with st.form("add_free_time"):
    cols = st.columns([2, 1, 1, 1])
    with cols[0]:
        selected_date = st.date_input("Select Date", value=st.session_state.free_time_date, key="new_date")
    with cols[1]:
        hours = st.number_input("Hours", min_value=0.5, max_value=24.0, value=st.session_state.free_time_hours, step=0.5, key="new_hours")
    with cols[2]:
        operation = st.radio("Operation", ["Add", "Subtract"], horizontal=True)
    with cols[3]:
        submit_button = st.form_submit_button("Update Free Time")
        
if submit_button:
    # Convert date to pandas datetime
    pd_date = pd.to_datetime(selected_date)
    
    # Check if date already exists
    if not free_time_df.empty and pd_date in free_time_df['Date'].values:
        # Add or subtract from existing date
        idx = free_time_df[free_time_df['Date'] == pd_date].index[0]
        if operation == "Add":
            free_time_df.at[idx, 'Available Hours'] += hours
        else:  # Subtract
            current_hours = free_time_df.at[idx, 'Available Hours']
            new_hours = max(0, current_hours - hours)  # Prevent negative hours
            
            if new_hours == 0:
                # Remove the date if hours reduced to 0
                free_time_df = free_time_df.drop(idx)
            else:
                free_time_df.at[idx, 'Available Hours'] = new_hours
    else:
        # Only add new date if adding hours (can't subtract from non-existent date)
        if operation == "Add":
            new_row = pd.DataFrame({'Date': [pd_date], 'Available Hours': [hours]})
            free_time_df = pd.concat([free_time_df, new_row], ignore_index=True)
        else:
            st.warning(f"Cannot subtract hours from {selected_date.strftime('%A, %B %d')} - date doesn't exist yet.")
    
    # Save changes
    free_time_df.to_csv(free_time_file, index=False)
    st.session_state.free_time_date = selected_date
    st.session_state.free_time_hours = hours

# Display free time windows with move up/down buttons
if not free_time_df.empty:
    # Sort by date for display
    free_time_df = free_time_df.sort_values('Date')
    
    for i, (idx, row) in enumerate(free_time_df.iterrows()):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            formatted_date = row['Date'].strftime('%A, %B %d, %Y') if pd.notnull(row['Date']) else "Invalid Date"
            st.write(f"{formatted_date}")
        
        with col2:
            st.write(f"{row['Available Hours']} hours")
            
        with col3:
            # Move Up button (disabled for first row)
            if i > 0 and st.button("⬆️ Move Up", key=f"up_{idx}"):
                # Swap with previous row by date
                free_time_df = free_time_df.sort_values('Date')
                dates = free_time_df['Date'].tolist()
                current_date = dates[i]
                prev_date = dates[i-1]
                
                # Store current values
                current_hours = free_time_df.loc[free_time_df['Date'] == current_date, 'Available Hours'].values[0]
                prev_hours = free_time_df.loc[free_time_df['Date'] == prev_date, 'Available Hours'].values[0]
                
                # Swap dates (keep hours the same)
                free_time_df.loc[free_time_df['Date'] == current_date, 'Date'] = prev_date
                free_time_df.loc[free_time_df['Date'] == prev_date, 'Date'] = current_date
                
                # Save changes
                free_time_df.to_csv(free_time_file, index=False)
                st.rerun()
                
        with col4:
            # Delete button
            if st.button("🗑️ Delete", key=f"del_{idx}"):
                free_time_df = free_time_df.drop(idx)
                free_time_df.to_csv(free_time_file, index=False)
                st.rerun()
    
    # Show a summary
    st.info(f"Total free time available: {free_time_df['Available Hours'].sum()} hours")
else:
    st.info("No free time windows added yet. Use the form above to add free time.")

# Update the main dataframe with edits for use in scheduling
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
        st.warning(
            f"You are over capacity by {total_estimated_time - total_free_time} hours. "
            f"Consider reducing tasks, adding free time, or moving due dates."
        )
    else:
        st.success(
            f"You have {total_free_time - total_estimated_time} hours of free capacity remaining."
        )

    st.markdown("### Daily Capacity vs Demand")
    
    # Create a working copy of the free time dataframe for scheduling
    working_free_time_df = free_time_df.copy()
    working_free_time_df['Date'] = pd.to_datetime(working_free_time_df['Date'])
    working_free_time_df = working_free_time_df.sort_values(by='Date')
    
    # Create daily summary from current free time dataframe
    daily_summary = (
        working_free_time_df.groupby('Date')['Available Hours']
        .sum()
        .reset_index()
        .rename(columns={'Available Hours': 'Total Available'})
    )

    if not tasks_df.empty:
        scheduled_tasks = []  # Start with an empty list - clear previous scheduling
        warnings = []

        today = pd.to_datetime(datetime.today().date())
        tasks_df['Due Date'] = pd.to_datetime(tasks_df['Due Date'], errors='coerce')
        
        def calc_priority(row):
            days_until_due = (row['Due Date'] - today).days if pd.notnull(row['Due Date']) else 9999
            return days_until_due * 1 - row['Importance'] * 5

        tasks_df['Priority Score'] = tasks_df.apply(calc_priority, axis=1)
        tasks_df = tasks_df.sort_values(by=['Priority Score', 'Complexity'])

        # MAIN SCHEDULING LOGIC
        for idx, task in tasks_df.iterrows():
            task_time_remaining = task['Estimated Time']
            task_name = task['Task']
            due_date = task['Due Date']

            if task_time_remaining > 6:
                warnings.append(
                    f"Task '{task_name}' exceeds 6 hours and should probably be split unless it's a Work Block."
                )

            for f_idx, window in working_free_time_df.iterrows():
                if task_time_remaining <= 0:
                    break

                if pd.notnull(due_date) and window['Date'] > due_date:
                    break

                available_hours = window['Available Hours']
                if available_hours > 0:
                    allocated_time = min(task_time_remaining, available_hours)
                    scheduled_tasks.append({
                        'Task': task_name,
                        'Date': window['Date'],
                        'Allocated Hours': allocated_time
                    })
                    working_free_time_df.at[f_idx, 'Available Hours'] -= allocated_time
                    task_time_remaining -= allocated_time

            # If leftover => user might want "Needs Attention" or partial?
            if pd.notnull(due_date) and task_time_remaining > 0:
                warnings.append(
                    f"HANDLE: {task_name} (Due: {due_date.date()}) "
                    f"needs {task['Estimated Time']}h, but only {task['Estimated Time'] - task_time_remaining}h scheduled before due date."
                )

        scheduled_df = pd.DataFrame(scheduled_tasks)

        if not scheduled_df.empty:
            # Convert scheduled_df to datetime
            scheduled_df['Date'] = pd.to_datetime(scheduled_df['Date'])
            
            # Build daily_scheduled
            daily_scheduled = (
                scheduled_df.groupby('Date')['Allocated Hours']
                .sum()
                .reset_index()
                .rename(columns={'Allocated Hours': 'Total Scheduled'})
            )

            # Ensure both Date columns are datetime
            daily_summary['Date'] = pd.to_datetime(daily_summary['Date'])
            daily_scheduled['Date'] = pd.to_datetime(daily_scheduled['Date'])
            daily_summary = daily_summary.merge(daily_scheduled, on='Date', how='left').fillna(0)

            st.dataframe(daily_summary)

            pivot_df = scheduled_df.pivot(index='Task', columns='Date', values='Allocated Hours').fillna('')
            
            # Only display non-empty columns first
            if not pivot_df.empty:
                non_empty_cols = [col for col in pivot_df.columns if (pivot_df[col] != '').any()]
                empty_cols = [col for col in pivot_df.columns if col not in non_empty_cols]
                ordered_cols = non_empty_cols + empty_cols
                if ordered_cols:  # Check if any columns exist
                    pivot_df = pivot_df[ordered_cols]
                
                st.dataframe(pivot_df)
            else:
                st.write("No scheduled tasks yet.")
        else:
            st.write("No tasks could be scheduled with the current free time availability.")

        if warnings:
            st.subheader("Warnings & Handle Options")
            
            for i, warning in enumerate(warnings):
                if warning.startswith("HANDLE:"):
                    # Extract task details from the warning
                    task_info = warning.replace("HANDLE:", "").strip()
                    task_name = task_info.split("(Due:")[0].strip()
                    
                    # Display the warning in a yellow box
                    st.warning(warning)
                    
                    # Create a container for resolution options
                    resolution_container = st.container()
                    
                    # Create unique keys for this warning
                    warning_key = f"warning_{i}_{task_name.replace(' ', '_')}"
                    
                    # Radio button for resolution options
                    with resolution_container:
                        st.write("### Resolution Options")
                        
                        # Create tabs for different resolution options
                        tab1, tab2, tab3, tab4, tab5 = st.tabs([
                            "Add Time", 
                            "Reduce Estimate", 
                            "Move Tasks", 
                            "Adjust Due Date",
                            "Acknowledge"
                        ])
                        
                        with tab1:
                            # Add more free time before the due date
                            task_row = tasks_df[tasks_df['Task'] == task_name]
                            if not task_row.empty:
                                due_date = task_row['Due Date'].iloc[0]
                                if pd.notnull(due_date):
                                    # Format for display
                                    due_date_str = pd.to_datetime(due_date).strftime('%Y-%m-%d')
                                    
                                    st.write(f"Add free time before {due_date_str}:")
                                    
                                    # Find how much more time is needed
                                    time_needed = 0
                                    if "needs" in task_info and "scheduled" in task_info:
                                        try:
                                            total_needed = float(task_info.split("needs ")[1].split("h")[0])
                                            scheduled = float(task_info.split("only ")[1].split("h")[0])
                                            time_needed = total_needed - scheduled
                                        except:
                                            time_needed = 1.0  # Default if parsing fails
                                    
                                    # Create quick add options
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        add_date = st.date_input("Date to add time", 
                                                              value=pd.to_datetime(due_date) - pd.Timedelta(days=1),
                                                              max_value=pd.to_datetime(due_date),
                                                              key=f"add_date_{warning_key}")
                                    with col2:
                                        add_hours = st.number_input("Hours to add", 
                                                                min_value=0.5, 
                                                                value=time_needed if time_needed > 0 else 1.0,
                                                                step=0.5,
                                                                key=f"add_hours_{warning_key}")
                                    
                                    if st.button("Add This Time", key=f"add_time_{warning_key}"):
                                        pd_date = pd.to_datetime(add_date)
                                        
                                        # Check if date already exists in free_time_df
                                        if not free_time_df.empty and pd_date in free_time_df['Date'].values:
                                            # Add to existing date
                                            idx = free_time_df[free_time_df['Date'] == pd_date].index[0]
                                            free_time_df.at[idx, 'Available Hours'] += add_hours
                                        else:
                                            # Add new date
                                            new_row = pd.DataFrame({'Date': [pd_date], 'Available Hours': [add_hours]})
                                            free_time_df = pd.concat([free_time_df, new_row], ignore_index=True)
                                        
                                        # Save changes
                                        free_time_df.to_csv(free_time_file, index=False)
                                        st.session_state['rerun_scheduler'] = True
                                        st.success(f"Added {add_hours} hours on {add_date}. Rescheduling...")
                                        st.rerun()
                        
                        with tab2:
                            # Reduce the estimated time for this task
                            task_row = tasks_df[tasks_df['Task'] == task_name]
                            if not task_row.empty:
                                current_estimate = task_row['Estimated Time'].iloc[0]
                                
                                # Find how much is currently scheduled
                                scheduled_time = 0
                                if "only" in task_info and "scheduled" in task_info:
                                    try:
                                        scheduled_time = float(task_info.split("only ")[1].split("h")[0])
                                    except:
                                        scheduled_time = 0
                                
                                # Show current estimate and get new estimate
                                st.write(f"Current estimate: **{current_estimate}h**")
                                st.write(f"Currently scheduled: **{scheduled_time}h**")
                                
                                new_estimate = st.number_input(
                                    "New estimate (hours):",
                                    min_value=scheduled_time,
                                    max_value=float(current_estimate),
                                    value=scheduled_time,
                                    step=0.5,
                                    key=f"new_estimate_{warning_key}"
                                )
                                
                                # Always show the update button
                                if st.button("Update Estimate", key=f"update_estimate_{warning_key}"):
                                    # Update the task's estimated time
                                    idx = task_row.index[0]
                                    tasks_df.at[idx, 'Estimated Time'] = new_estimate
                                    
                                    # Save changes
                                    tasks_df.to_csv(tasks_file, index=False)
                                    st.session_state['rerun_scheduler'] = True
                                    st.success(f"Updated estimate to {new_estimate}h. Rescheduling...")
                                    st.rerun()
                        
                        with tab3:
                            # Move other tasks to make room for this one
                            st.info("This feature is coming soon. For now, please use the task editor to manually adjust task priorities.")
                        
                        with tab4:
                            # Adjust the due date for this task
                            task_row = tasks_df[tasks_df['Task'] == task_name]
                            if not task_row.empty:
                                current_due_date = task_row['Due Date'].iloc[0]
                                if pd.notnull(current_due_date):
                                    current_due_date = pd.to_datetime(current_due_date)
                                    
                                    # Show current due date
                                    st.write(f"Current due date: **{current_due_date.strftime('%Y-%m-%d')}**")
                                    
                                    # Get new due date
                                    new_due_date = st.date_input(
                                        "New due date:",
                                        value=current_due_date + pd.Timedelta(days=1),
                                        min_value=pd.to_datetime(datetime.today()),
                                        key=f"new_due_date_{warning_key}"
                                    )
                                    
                                    if st.button("Update Due Date", key=f"update_due_date_{warning_key}"):
                                        # Update the task's due date
                                        idx = task_row.index[0]
                                        tasks_df.at[idx, 'Due Date'] = pd.to_datetime(new_due_date)
                                        
                                        # Save changes
                                        tasks_df.to_csv(tasks_file, index=False)
                                        st.session_state['rerun_scheduler'] = True
                                        st.success(f"Updated due date to {new_due_date}. Rescheduling...")
                                        st.rerun()
                        
                        with tab5:
                            # Mark as acknowledged
                            st.write("Mark this warning as acknowledged if you'll handle it manually.")
                            if st.button("Acknowledge Warning", key=f"acknowledge_{warning_key}"):
                                st.success("Warning acknowledged. You'll need to handle this manually.")
                    
                    # Add a separator between warnings
                    st.markdown("---")
                else:
                    # Display other warnings (not HANDLE: warnings)
                    st.warning(warning)

    if 'rerun_scheduler' in st.session_state:
        del st.session_state['rerun_scheduler']
