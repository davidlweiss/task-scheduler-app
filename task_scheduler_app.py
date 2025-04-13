import streamlit as st
import pandas as pd
import os
import math
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
    
    # Create working copy of the free time dataframe for scheduling
    working_free_time_df = free_time_df.copy()
    if 'Sort Order' in working_free_time_df.columns:
        working_free_time_df = working_free_time_df.drop('Sort Order', axis=1)
    
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

        # Check for large tasks before scheduling
        large_tasks = []
        for idx, task in tasks_df.iterrows():
            if task['Estimated Time'] > 6 and not any(tag in str(task['Task']) for tag in ['[MULTI-SESSION]', '[FIXED EVENT]', '[PENDING PLANNING]']):
                large_tasks.append((idx, task))
        
        # MAIN SCHEDULING LOGIC
        for idx, task in tasks_df.iterrows():
            task_time_remaining = task['Estimated Time']
            task_name = task['Task']
            due_date = task['Due Date']

            if task_time_remaining > 6 and not any(tag in str(task_name) for tag in ['[MULTI-SESSION]', '[FIXED EVENT]', '[PENDING PLANNING]']):
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

                        # Process large tasks first
        if large_tasks:
            st.subheader("Tasks That Need Breakdown")
            
            # Create a selection interface first - no collapsible elements
            st.markdown("Select a task to break down:")
            
            # Create a list of task options with IDs for selection
            task_options = []
            for i, (idx, task) in enumerate(large_tasks):
                task_name = task['Task']
                hours = task['Estimated Time']
                task_options.append(f"{i+1}. '{task_name}' ({hours}h)")
            
            # Only show breakdown UI if user selects a task
            if "selected_task_index" not in st.session_state:
                st.session_state.selected_task_index = 0
                
            # Add option for no task selected
            task_options = ["-- Select a task to break down --"] + task_options
            
            # Select a task to break down
            selected_option = st.selectbox(
                "Choose a task:",
                options=task_options,
                index=st.session_state.selected_task_index,
                key="task_selector"
            )
            
            # Get the selected task index (0 means no selection)
            selected_index = task_options.index(selected_option) - 1
            st.session_state.selected_task_index = selected_index + 1
            
            # Only show breakdown UI if user selects a task
            if selected_index >= 0:
                idx, task = large_tasks[selected_index]
                task_name = task['Task']
                hours = task['Estimated Time']
                is_very_large = hours >= 15
                
                st.markdown("---")
                st.warning(f"Task '{task_name}' exceeds 6 hours and should probably be split unless it's a Work Block.")
                
                if is_very_large:
                    st.markdown(f"**This task is estimated at {hours} hours**, which suggests it may need planning and breakdown. Select an approach:")
                else:
                    st.markdown(f"**This task is estimated at {hours} hours**. Select an approach:")
                
                # Create unique options based on task size
                if is_very_large:
                    approach_options = [
                        "-- Select an approach --",
                        "📋 Schedule a Planning Session",
                        "✂️ Break it Down Now",
                        "🔄 Split into Focus Sessions",
                        "🌱 Iterative Project"
                    ]
                else:
                    approach_options = [
                        "-- Select an approach --",
                        "🔍 Project Breakdown",
                        "📋 Schedule Planning",
                        "🔄 Focus Sessions",
                        "📅 Fixed Duration Event"
                    ]
                
                # Select approach
                if "selected_approach" not in st.session_state:
                    st.session_state.selected_approach = 0
                    
                selected_approach = st.selectbox(
                    "Approach:",
                    options=approach_options,
                    index=st.session_state.selected_approach,
                    key=f"approach_selector_{selected_index}"
                )
                
                approach_index = approach_options.index(selected_approach)
                st.session_state.selected_approach = approach_index
                
                # Handle the selected approach
                if approach_index == 1:  # Planning Session
                    st.info("This will create a 1-hour planning task to help you break down this work later.")
                    
                    with st.form(key=f"planning_form_{selected_index}"):
                        planning_task_name = st.text_input(
                            "Planning task name:", 
                            value=f"Plan breakdown of: {task_name}"
                        )
                        
                        planning_date = st.date_input(
                            "When do you want to plan this?", 
                            value=datetime.today()
                        )
                        
                        planning_hours = st.slider(
                            "Planning time needed (hours):", 
                            min_value=0.5, 
                            max_value=2.0, 
                            value=1.0, 
                            step=0.5
                        )
                        
                        create_planning = st.form_submit_button("Create Planning Task")
                        
                        if create_planning:
                            # Add the planning task
                            new_task = pd.DataFrame({
                                'Project': task['Project'] if 'Project' in task else "Planning",
                                'Task': planning_task_name,
                                'Estimated Time': planning_hours,
                                'Due Date': pd.to_datetime(planning_date),
                                'Importance': 4,  # High importance
                                'Complexity': 2   # Moderate complexity
                            })
                            
                            # Update original task description to show it's pending planning
                            tasks_df.at[idx, 'Task'] = f"{task_name} [PENDING PLANNING]"
                            
                            # Add planning task and save
                            tasks_df = pd.concat([tasks_df, new_task], ignore_index=True)
                            tasks_df.to_csv(tasks_file, index=False)
                            
                            # Reset selection for next task
                            st.session_state.selected_task_index = 0
                            st.session_state.selected_approach = 0
                            
                            st.success(f"Created planning task: {planning_task_name}")
                            st.session_state['rerun_scheduler'] = True
                            st.rerun()
                
                elif approach_index == 2:  # Break down / Project
                    st.info("Let's break this down into smaller, related subtasks")
                    
                    with st.form(key=f"breakdown_form_{selected_index}"):
                        num_subtasks = st.slider(
                            "How many subtasks do you want to create?", 
                            min_value=2, 
                            max_value=10, 
                            value=3
                        )
                        
                        # Create input fields for each subtask
                        subtask_names = []
                        subtask_hours = []
                        total_hours = 0
                        
                        for i in range(num_subtasks):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                name = st.text_input(
                                    f"Subtask {i+1} name:", 
                                    value=f"{task_name} - Part {i+1}",
                                    key=f"subtask_name_{i}"
                                )
                                subtask_names.append(name)
                            
                            with col2:
                                hours_value = hours / num_subtasks if i == 0 else 0
                                hour = st.number_input(
                                    "Hours:", 
                                    min_value=0.5, 
                                    max_value=float(hours), 
                                    value=hours_value,
                                    step=0.5,
                                    key=f"subtask_hours_{i}"
                                )
                                subtask_hours.append(hour)
                                total_hours += hour
                        
                        # Show the total hours allocated
                        remaining = hours - total_hours
                        st.write(f"Total allocated: **{total_hours}h** | Original estimate: **{hours}h** | Remaining: **{remaining}h**")
                        
                        create_subtasks = st.form_submit_button("Create Subtasks")
                        
                        if create_subtasks:
                            # Create new subtask rows
                            new_tasks = []
                            for i in range(num_subtasks):
                                new_task_row = task.copy()
                                new_task_row['Task'] = subtask_names[i]
                                new_task_row['Estimated Time'] = subtask_hours[i]
                                new_tasks.append(new_task_row)
                            
                            # Remove the original task
                            tasks_df = tasks_df.drop(idx)
                            
                            # Add new subtasks
                            new_tasks_df = pd.DataFrame(new_tasks)
                            tasks_df = pd.concat([tasks_df, new_tasks_df], ignore_index=True)
                            
                            # Save changes
                            tasks_df.to_csv(tasks_file, index=False)
                            
                            # Reset selection for next task
                            st.session_state.selected_task_index = 0
                            st.session_state.selected_approach = 0
                            
                            st.success(f"Created {num_subtasks} subtasks. Original task has been removed.")
                            st.session_state['rerun_scheduler'] = True
                            st.rerun()
                
                elif approach_index == 3:  # Focus Sessions
                    st.info("Let's split this into multiple focus sessions while keeping it as a single task")
                    
                    with st.form(key=f"focus_form_{selected_index}"):
                        # Determine suggested session length
                        suggested_length = min(4.0, hours / 2)
                        
                        session_length = st.slider(
                            "How long should each focus session be?", 
                            min_value=1.0, 
                            max_value=6.0, 
                            value=suggested_length,
                            step=0.5
                        )
                        
                        num_sessions = math.ceil(hours / session_length)
                        st.write(f"This will create **{num_sessions} sessions** of **{session_length}h** each.")
                        
                        # Option to update the task name
                        update_name = st.checkbox(
                            "Update the task name to indicate it's a multi-session task?", 
                            value=True
                        )
                        
                        new_name = task_name
                        if update_name:
                            new_name = st.text_input(
                                "New task name:", 
                                value=f"{task_name} [MULTI-SESSION]"
                            )
                        
                        create_sessions = st.form_submit_button("Create Focus Sessions")
                        
                        if create_sessions:
                            # Update the task
                            # Update name if requested
                            if update_name:
                                tasks_df.at[idx, 'Task'] = new_name
                            
                            # Add metadata about sessions - make sure columns exist
                            if 'Focus Sessions' not in tasks_df.columns:
                                tasks_df['Focus Sessions'] = None
                            if 'Session Length' not in tasks_df.columns:
                                tasks_df['Session Length'] = None
                            
                            tasks_df.at[idx, 'Focus Sessions'] = num_sessions
                            tasks_df.at[idx, 'Session Length'] = session_length
                            
                            # Save changes
                            tasks_df.to_csv(tasks_file, index=False)
                            
                            # Reset selection for next task
                            st.session_state.selected_task_index = 0
                            st.session_state.selected_approach = 0
                            
                            st.success(f"Updated task to use {num_sessions} focus sessions of {session_length}h each.")
                            st.session_state['rerun_scheduler'] = True
                            st.rerun()
                
                elif approach_index == 4:  # Iterative Project or Fixed Event
                    if is_very_large:  # Iterative Project
                        st.info("Let's set up an iterative project structure that will evolve as work progresses")
                        
                        with st.form(key=f"iterative_form_{selected_index}"):
                            # Initial exploration session
                            exploration_hours = st.slider(
                                "How long should the initial exploration session be?", 
                                min_value=1.0, 
                                max_value=4.0, 
                                value=2.0,
                                step=0.5
                            )
                            
                            # Expected sessions
                            expected_sessions = math.ceil((hours - exploration_hours) / 4) + 1
                            st.write(f"Based on the total estimate of {hours}h, you'll likely need about {expected_sessions} sessions.")
                            
                            # Create a project container
                            create_project = st.form_submit_button("Create Iterative Project")
                            
                            if create_project:
                                # Copy most attributes from original task
                                exploration_task = task.copy()
                                exploration_task['Project'] = f"Iterative: {task_name}"
                                exploration_task['Task'] = f"Initial exploration: {task_name}"
                                exploration_task['Estimated Time'] = exploration_hours
                                
                                remaining_task = task.copy()
                                remaining_task['Project'] = f"Iterative: {task_name}"
                                remaining_task['Task'] = f"{task_name} [REMAINING WORK]"
                                remaining_task['Estimated Time'] = hours - exploration_hours
                                
                                # Convert to DataFrames
                                exploration_df = pd.DataFrame([exploration_task])
                                remaining_df = pd.DataFrame([remaining_task])
                                
                                # Remove the original task
                                tasks_df = tasks_df.drop(idx)
                                
                                # Add new tasks
                                tasks_df = pd.concat([tasks_df, exploration_df, remaining_df], ignore_index=True)
                                
                                # Save changes
                                tasks_df.to_csv(tasks_file, index=False)
                                
                                # Reset selection for next task
                                st.session_state.selected_task_index = 0
                                st.session_state.selected_approach = 0
                                
                                st.success(f"Created iterative project structure with initial exploration session and placeholder for remaining work.")
                                st.session_state['rerun_scheduler'] = True
                                st.rerun()
                    else:  # Fixed Event
                        st.info("This will mark the task as a fixed-duration event that shouldn't be broken down")
                        
                        with st.form(key=f"event_form_{selected_index}"):
                            update_name = st.checkbox(
                                "Update the task name to indicate it's a fixed event?", 
                                value=True
                            )
                            
                            new_name = task_name
                            if update_name:
                                new_name = st.text_input(
                                    "New task name:", 
                                    value=f"{task_name} [FIXED EVENT]"
                                )
                            
                            mark_as_event = st.form_submit_button("Mark as Fixed Event")
                            
                            if mark_as_event:
                                # Update the task
                                # Update name if requested
                                if update_name:
                                    tasks_df.at[idx, 'Task'] = new_name
                                
                                # Add metadata about event type
                                if 'Event Type' not in tasks_df.columns:
                                    tasks_df['Event Type'] = None
                                    
                                tasks_df.at[idx, 'Event Type'] = "Fixed Duration"
                                
                                # Save changes
                                tasks_df.to_csv(tasks_file, index=False)
                                
                                # Reset selection for next task
                                st.session_state.selected_task_index = 0
                                st.session_state.selected_approach = 0
                                
                                st.success("Marked as a fixed duration event. It won't be flagged for breakdown again.")
                                st.session_state['rerun_scheduler'] = True
                                st.rerun() again.")
                                st.session_state['rerun_scheduler'] = True
                                st.rerun() again.")
                                st.session_state['rerun_scheduler'] = True
                                st.rerun()
        
        # Handle other warnings (scheduling issues, etc.)
        if warnings:
            st.subheader("Warnings & Handle Options")
            
            # Process scheduling warnings (HANDLE warnings)
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
                    
                    # Create tabs for different resolution options
                    with resolution_container:
                        st.write("### Resolution Options")
                        
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
                
                # Skip displaying large task warnings here, as we've already handled them
                elif "exceeds 6 hours" not in warning:
                    st.warning(warning)

    if 'rerun_scheduler' in st.session_state:
        del st.session_state['rerun_scheduler']
