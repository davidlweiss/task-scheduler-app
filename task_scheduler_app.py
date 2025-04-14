import streamlit as st
import pandas as pd
import os
import math
from datetime import datetime

# File paths
tasks_file = 'tasks.csv'
free_time_file = 'free_time.csv'
backlog_file = 'backlog.csv'  # New file for backlog items

# Initialize session state for wizard at the very beginning
if 'wizard_mode' not in st.session_state:
    st.session_state.wizard_mode = False
if 'wizard_step' not in st.session_state:
    st.session_state.wizard_step = 1
if 'wizard_task_idx' not in st.session_state:
    st.session_state.wizard_task_idx = None
if 'wizard_task' not in st.session_state:
    st.session_state.wizard_task = None
if 'wizard_approach' not in st.session_state:
    st.session_state.wizard_approach = None
    
# Initialize session state for backlog conversion
if 'converting_item' not in st.session_state:
    st.session_state.converting_item = None
if 'converting_idx' not in st.session_state:
    st.session_state.converting_idx = None
    
# Initialize session state for task resolution
if 'resolving_task' not in st.session_state:
    st.session_state.resolving_task = None
if 'resolving_option' not in st.session_state:
    st.session_state.resolving_option = None

# For debugging
# st.write(f"DEBUG: Wizard mode = {st.session_state.wizard_mode}")

# Function to start wizard mode
def start_wizard():
    st.session_state.wizard_mode = True
    st.session_state.wizard_step = 1
    st.session_state.wizard_task_idx = None
    st.session_state.wizard_task = None
    st.session_state.wizard_approach = None

# Function to exit wizard mode
def exit_wizard():
    st.session_state.wizard_mode = False
    st.session_state.wizard_step = 1
    st.session_state.wizard_task_idx = None
    st.session_state.wizard_task = None
    st.session_state.wizard_approach = None

# Function to go to next wizard step
def next_wizard_step():
    st.session_state.wizard_step += 1

# Function to go to previous wizard step
def prev_wizard_step():
    st.session_state.wizard_step = max(1, st.session_state.wizard_step - 1)

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
backlog_df = load_data(backlog_file, ['Idea', 'Category', 'Description', 'Creation Date', 'Status'])

# TOP LEVEL UI DECISION - Check if we're in wizard mode first, before rendering any UI
if st.session_state.wizard_mode:
    # WIZARD MODE
    st.title("Dynamic Task Scheduler V8")
    st.markdown("## Task Breakdown Wizard")
    
    # Create a progress bar
    progress_percentage = (st.session_state.wizard_step - 1) / 3  # 3 steps total
    st.progress(progress_percentage)
    
    # Show step indicator
    st.write(f"Step {st.session_state.wizard_step} of 3")
    
    # WIZARD STEP 1: Select a task
    if st.session_state.wizard_step == 1:
        st.subheader("Step 1: Select a Task to Break Down")
        
        # Identify large tasks
        large_tasks = []
        for idx, task in tasks_df.iterrows():
            if task['Estimated Time'] > 6 and not any(tag in str(task['Task']) for tag in ['[MULTI-SESSION]', '[FIXED EVENT]', '[PENDING PLANNING]']):
                large_tasks.append((idx, task))
        
        if not large_tasks:
            st.info("No large tasks found that need to be broken down.")
            if st.button("Return to Main App"):
                exit_wizard()
        else:
            # Create task options
            task_options = []
            for idx, task in large_tasks:
                hours = task['Estimated Time']
                task_options.append((idx, f"{task['Task']} ({hours}h)"))
            
            # Create radio buttons for task selection
            selected_task_index = 0
            for i, (idx, label) in enumerate(task_options):
                if st.radio(f"", [label], key=f"task_{i}", label_visibility="collapsed"):
                    selected_task_index = i
            
            # Store the selected task
            idx, _ = task_options[selected_task_index]
            st.session_state.wizard_task_idx = idx
            st.session_state.wizard_task = tasks_df.loc[idx].to_dict()
            
            # Navigation buttons
            cols = st.columns([1, 1, 1])
            with cols[0]:
                if st.button("Cancel"):
                    exit_wizard()
            with cols[2]:
                if st.button("Next Step"):
                    next_wizard_step()
    
    # WIZARD STEP 2: Choose approach
    elif st.session_state.wizard_step == 2:
        st.subheader("Step 2: Choose a Breakdown Approach")
        
        # Get task details
        task = st.session_state.wizard_task
        task_name = task['Task']
        hours = task['Estimated Time']
        is_very_large = hours >= 15
        
        # Display task info
        st.markdown(f"**Task:** {task_name}")
        st.markdown(f"**Estimated hours:** {hours}")
        
        # Create approach options based on task size
        if is_very_large:
            st.write("This task is very large and may require significant planning.")
            approach_options = [
                "Schedule a Planning Session - Create time to plan this work",
                "Break into Subtasks - Split into multiple smaller tasks",
                "Focus Sessions - Keep as one task but divide into timed sessions",
                "Iterative Project - Create a flexible, evolving project structure"
            ]
        else:
            approach_options = [
                "Break into Subtasks - Split into multiple smaller tasks",
                "Schedule a Planning Session - Create time to plan this work",
                "Focus Sessions - Keep as one task but divide into timed sessions",
                "Fixed Duration Event - Mark as event that shouldn't be broken down"
            ]
        
        # Use radio buttons for approach selection
        approach_index = 0
        for i, approach in enumerate(approach_options):
            if st.radio("", [approach], key=f"approach_{i}", label_visibility="collapsed"):
                approach_index = i
        
        # Store the selected approach
        st.session_state.wizard_approach = approach_options[approach_index]
        
        # Navigation buttons
        cols = st.columns([1, 1, 1])
        with cols[0]:
            if st.button("Previous Step"):
                prev_wizard_step()
        with cols[1]:
            if st.button("Cancel"):
                exit_wizard()
        with cols[2]:
            if st.button("Next Step"):
                next_wizard_step()
    
    # WIZARD STEP 3: Complete form for selected approach
    elif st.session_state.wizard_step == 3:
        st.subheader("Step 3: Complete Task Breakdown")
        
        # Get task details
        idx = st.session_state.wizard_task_idx
        task = st.session_state.wizard_task
        task_name = task['Task']
        hours = task['Estimated Time']
        approach = st.session_state.wizard_approach
        
        # Display task and approach
        st.markdown(f"**Task:** {task_name}")
        st.markdown(f"**Approach:** {approach.split(' - ')[0]}")
        
        # Show form based on selected approach
        if "Planning Session" in approach:
            with st.form(key="planning_form"):
                st.write("Create a planning task to help you break down this work later.")
                
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
                
                # Form buttons
                cols = st.columns([1, 1, 1])
                with cols[0]:
                    previous_step = st.form_submit_button("Previous")
                with cols[1]:
                    cancel = st.form_submit_button("Cancel")
                with cols[2]:
                    create_planning = st.form_submit_button("Create Planning Task")
                
                if previous_step:
                    prev_wizard_step()
                    st.rerun()
                
                if cancel:
                    exit_wizard()
                    st.rerun()
                
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
                    
                    # Show success message
                    st.success("Created planning task. The original task has been marked as pending planning.")
                    
                    # Return to main app
                    if st.button("Return to App"):
                        exit_wizard()
                        st.rerun()
                    else:
                        # Auto-exit
                        exit_wizard()
                        st.rerun()
        
        elif "Break into Subtasks" in approach:
            with st.form(key="breakdown_form"):
                st.write("Split this into multiple related subtasks that can be scheduled separately.")
                
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
                        hours_value = round(hours / num_subtasks, 1) if i == 0 else 0
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
                
                # Form buttons
                cols = st.columns([1, 1, 1])
                with cols[0]:
                    previous_step = st.form_submit_button("Previous")
                with cols[1]:
                    cancel = st.form_submit_button("Cancel")
                with cols[2]:
                    create_subtasks = st.form_submit_button("Create Subtasks")
                
                if previous_step:
                    prev_wizard_step()
                    st.rerun()
                
                if cancel:
                    exit_wizard()
                    st.rerun()
                
                if create_subtasks:
                    # Create new subtask rows
                    new_tasks = []
                    for i in range(num_subtasks):
                        task_dict = task.copy()
                        task_dict['Task'] = subtask_names[i]
                        task_dict['Estimated Time'] = subtask_hours[i]
                        new_tasks.append(task_dict)
                    
                    # Remove the original task
                    tasks_df = tasks_df.drop(idx)
                    
                    # Add new subtasks
                    new_tasks_df = pd.DataFrame(new_tasks)
                    tasks_df = pd.concat([tasks_df, new_tasks_df], ignore_index=True)
                    
                    # Save changes
                    tasks_df.to_csv(tasks_file, index=False)
                    
                    # Show success message
                    st.success(f"Created {num_subtasks} subtasks. Original task has been removed.")
                    
                    # Auto-exit
                    exit_wizard()
                    st.rerun()
        
        elif "Focus Sessions" in approach:
            with st.form(key="focus_form"):
                st.write("Keep this as one task but divide it into multiple timed work sessions.")
                
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
                
                # Form buttons
                cols = st.columns([1, 1, 1])
                with cols[0]:
                    previous_step = st.form_submit_button("Previous")
                with cols[1]:
                    cancel = st.form_submit_button("Cancel")
                with cols[2]:
                    create_sessions = st.form_submit_button("Create Focus Sessions")
                
                if previous_step:
                    prev_wizard_step()
                    st.rerun()
                
                if cancel:
                    exit_wizard()
                    st.rerun()
                
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
                    
                    # Show success message
                    st.success(f"Updated task to use {num_sessions} focus sessions of {session_length}h each.")
                    
                    # Auto-exit
                    exit_wizard()
                    st.rerun()
        
        elif "Iterative Project" in approach:
            with st.form(key="iterative_form"):
                st.write("Create a structure for a project that will evolve as work progresses.")
                
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
                
                # Form buttons
                cols = st.columns([1, 1, 1])
                with cols[0]:
                    previous_step = st.form_submit_button("Previous")
                with cols[1]:
                    cancel = st.form_submit_button("Cancel")
                with cols[2]:
                    create_project = st.form_submit_button("Create Iterative Project")
                
                if previous_step:
                    prev_wizard_step()
                    st.rerun()
                
                if cancel:
                    exit_wizard()
                    st.rerun()
                
                if create_project:
                    # Copy most attributes from original task
                    task_dict = task.copy()
                    
                    exploration_task = task_dict.copy()
                    exploration_task['Project'] = f"Iterative: {task_name}"
                    exploration_task['Task'] = f"Initial exploration: {task_name}"
                    exploration_task['Estimated Time'] = exploration_hours
                    
                    remaining_task = task_dict.copy()
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
                    
                    # Show success message
                    st.success("Created iterative project structure with initial exploration session and placeholder for remaining work.")
                    
                    # Auto-exit
                    exit_wizard()
                    st.rerun()
        
        elif "Fixed Duration Event" in approach:
            with st.form(key="event_form"):
                st.write("Mark this as a fixed-duration event that shouldn't be broken down.")
                
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
                
                # Form buttons
                cols = st.columns([1, 1, 1])
                with cols[0]:
                    previous_step = st.form_submit_button("Previous")
                with cols[1]:
                    cancel = st.form_submit_button("Cancel")
                with cols[2]:
                    mark_as_event = st.form_submit_button("Mark as Fixed Event")
                
                if previous_step:
                    prev_wizard_step()
                    st.rerun()
                
                if cancel:
                    exit_wizard()
                    st.rerun()
                
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
                    
                    # Show success message
                    st.success("Marked as a fixed duration event. It won't be flagged for breakdown again.")
                    
                    # Auto-exit
                    exit_wizard()
                    st.rerun()

else:
    # MAIN APP INTERFACE
    st.title("Dynamic Task Scheduler V8")
    
    # Create a tab structure for the main app
    tab1, tab2, tab3, tab4 = st.tabs(["Manage Tasks", "Manage Free Time", "Run Scheduler", "Idea Backlog"])
    
    # Tab 1: Manage Tasks
    with tab1:
        st.header("Edit Tasks")
        
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
            if st.button("Save Tasks"):
                edited_tasks_df.to_csv(tasks_file, index=False)
                tasks_df = edited_tasks_df
                st.success("Tasks saved successfully!")
    
    # Tab 2: Manage Free Time
    with tab2:
        st.header("Manage Free Time Windows")
    
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
    
    # Tab 3: Run Scheduler
    with tab3:
        st.header("Run Scheduler")
        
        # Decision Results Storage
        if 'action_results' not in st.session_state:
            st.session_state['action_results'] = []
        
        # Run Scheduler Button
        run_button = st.button("Run Scheduler")
        
        if run_button or 'rerun_scheduler' in st.session_state:
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
                unallocated_tasks = []  # List to track tasks with insufficient allocation
                
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
                    
                    # Track unallocated tasks
                    if pd.notnull(due_date) and task_time_remaining > 0:
                        warnings.append(
                            f"HANDLE: {task_name} (Due: {due_date.date()}) "
                            f"needs {task['Estimated Time']}h, but only {task['Estimated Time'] - task_time_remaining}h scheduled before due date."
                        )
                        
                        # Track the unallocated task with details
                        unallocated_tasks.append({
                            'Task': task_name,
                            'Task Index': idx,  # Store the index for later reference
                            'Due Date': due_date,
                            'Total Hours': task['Estimated Time'],
                            'Allocated Hours': task['Estimated Time'] - task_time_remaining,
                            'Unallocated Hours': task_time_remaining
                        })
                
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
                
                # NEW SECTION: Handle tasks with insufficient hours
                if unallocated_tasks:
                    st.subheader("Tasks with Insufficient Hours")
                    
                    # Create a dataframe of unallocated tasks
                    unallocated_df = pd.DataFrame(unallocated_tasks)
                    st.dataframe(unallocated_df[['Task', 'Due Date', 'Total Hours', 'Allocated Hours', 'Unallocated Hours']])
                    
                    # Use session state to maintain resolution state
                    if st.session_state.resolving_task is None:
                        # Let user select a task to resolve
                        task_options = [task['Task'] for task in unallocated_tasks]
                        selected_task_name = st.selectbox("Select a task to resolve:", task_options)
                        
                        # Find the selected task details
                        selected_task = next((task for task in unallocated_tasks if task['Task'] == selected_task_name), None)
                        
                        if selected_task and st.button("Resolve This Task"):
                            st.session_state.resolving_task = selected_task
                            st.rerun()
                    else:
                        # We already have a task selected to resolve
                        selected_task = st.session_state.resolving_task
                        
                        # Show task details and "back" button
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.markdown(f"### Resolve scheduling for: {selected_task['Task']}")
                        with col2:
                            if st.button("× Cancel", key="cancel_resolution"):
                                st.session_state.resolving_task = None
                                st.session_state.resolving_option = None
                                st.rerun()
                                
                        st.markdown(f"**Due date:** {selected_task['Due Date'].date()}")
                        st.markdown(f"**Current allocation:** {selected_task['Allocated Hours']} of {selected_task['Total Hours']} hours")
                        st.markdown(f"**Unallocated hours:** {selected_task['Unallocated Hours']} hours")
                        
                        # Show resolution options
                        resolution_options = [
                            "Reduce task hours estimate",
                            "Add more free time",
                            "Break down into subtasks",
                            "Extend the due date",
                            "Mark as partially completed"
                        ]
                        
                        # If we don't have a resolution option selected yet, show the options
                        if st.session_state.resolving_option is None:
                            resolution_choice = st.radio("How would you like to resolve this?", resolution_options)
                            
                            if st.button("Continue"):
                                st.session_state.resolving_option = resolution_choice
                                st.rerun()
                        else:
                            # We have a resolution option selected
                            resolution_choice = st.session_state.resolving_option
                            
                            # Option to go back to option selection
                            if st.button("← Back to Options", key="back_to_options"):
                                st.session_state.resolving_option = None
                                st.rerun()
                                
                            st.markdown(f"**Resolution method:** {resolution_choice}")
                            
                            # Handle each resolution option
                            if resolution_choice == "Reduce task hours estimate":
                                new_estimate = st.number_input(
                                    "New total hour estimate:", 
                                    min_value=selected_task['Allocated Hours'], 
                                    max_value=selected_task['Total Hours'], 
                                    value=selected_task['Allocated Hours'],
                                    step=0.5
                                )
                                
                                if st.button("Update Task Estimate"):
                                    # Update the task's estimated time
                                    task_idx = selected_task['Task Index']
                                    tasks_df.at[task_idx, 'Estimated Time'] = new_estimate
                                    tasks_df.to_csv(tasks_file, index=False)
                                    st.success(f"Updated estimate for '{selected_task['Task']}' to {new_estimate} hours.")
                                    # Reset the resolution state
                                    st.session_state.resolving_task = None
                                    st.session_state.resolving_option = None
                                    st.session_state.rerun_scheduler = True
                                    st.rerun()
                            
                            elif resolution_choice == "Add more free time":
                                # Calculate days until due
                                today = pd.Timestamp(datetime.today().date())
                                days_until_due = (selected_task['Due Date'] - today).days
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    days_to_add = st.slider("Days to add free time:", 1, max(1, days_until_due), 1)
                                with col2:
                                    hours_per_day = st.number_input("Hours per day:", min_value=0.5, value=selected_task['Unallocated Hours']/days_to_add, step=0.5)
                                
                                dates_to_add = []
                                for i in range(days_to_add):
                                    date = today + pd.Timedelta(days=i)
                                    if date <= selected_task['Due Date']:
                                        dates_to_add.append(date)
                                
                                st.write(f"Will add {hours_per_day} hours to the following dates:")
                                for date in dates_to_add:
                                    st.write(f"- {date.strftime('%A, %B %d, %Y')}")
                                
                                if st.button("Add Free Time"):
                                    for date in dates_to_add:
                                        # Check if date already exists in free_time_df
                                        if date in free_time_df['Date'].values:
                                            idx = free_time_df[free_time_df['Date'] == date].index[0]
                                            free_time_df.at[idx, 'Available Hours'] += hours_per_day
                                        else:
                                            new_row = pd.DataFrame({'Date': [date], 'Available Hours': [hours_per_day]})
                                            free_time_df = pd.concat([free_time_df, new_row], ignore_index=True)
                                    
                                    free_time_df.to_csv(free_time_file, index=False)
                                    st.success(f"Added {hours_per_day * len(dates_to_add)} hours of free time across {len(dates_to_add)} days.")
                                    # Reset the resolution state
                                    st.session_state.resolving_task = None
                                    st.session_state.resolving_option = None
                                    st.session_state.rerun_scheduler = True
                                    st.rerun()
                            
                            elif resolution_choice == "Break down into subtasks":
                                if st.button("Start Task Breakdown Wizard"):
                                    # Store the task index to break down in the wizard
                                    st.session_state.wizard_task_idx = selected_task['Task Index']
                                    st.session_state.wizard_task = tasks_df.loc[selected_task['Task Index']].to_dict()
                                    # Reset the resolution state
                                    st.session_state.resolving_task = None
                                    st.session_state.resolving_option = None
                                    start_wizard()
                                    st.rerun()
                            
                            elif resolution_choice == "Extend the due date":
                                new_due_date = st.date_input(
                                    "New due date:", 
                                    value=selected_task['Due Date'], 
                                    min_value=selected_task['Due Date'].date()
                                )
                                
                                if st.button("Update Due Date"):
                                    task_idx = selected_task['Task Index']
                                    tasks_df.at[task_idx, 'Due Date'] = pd.to_datetime(new_due_date)
                                    tasks_df.to_csv(tasks_file, index=False)
                                    st.success(f"Updated due date for '{selected_task['Task']}' to {new_due_date}.")
                                    # Reset the resolution state
                                    st.session_state.resolving_task = None
                                    st.session_state.resolving_option = None
                                    st.session_state.rerun_scheduler = True
                                    st.rerun()
                            
                            elif resolution_choice == "Mark as partially completed":
                                progress_percentage = st.slider(
                                    "What percentage of this task is already completed?", 
                                    min_value=0, 
                                    max_value=100, 
                                    value=int((selected_task['Allocated Hours'] / selected_task['Total Hours']) * 100)
                                )
                                
                                remaining_hours = selected_task['Total Hours'] * (1 - progress_percentage / 100)
                                
                                st.write(f"This will update the task to {remaining_hours:.1f} hours remaining.")
                                
                                if st.button("Update Task Progress"):
                                    task_idx = selected_task['Task Index']
                                    tasks_df.at[task_idx, 'Estimated Time'] = remaining_hours
                                    
                                    # Optionally add "[IN PROGRESS]" tag to task name
                                    current_task_name = tasks_df.at[task_idx, 'Task']
                                    if not "[IN PROGRESS]" in current_task_name:
                                        tasks_df.at[task_idx, 'Task'] = f"{current_task_name} [IN PROGRESS {progress_percentage}%]"
                                    
                                    tasks_df.to_csv(tasks_file, index=False)
                                    st.success(f"Updated progress for '{selected_task['Task']}' to {progress_percentage}% complete.")
                                    # Reset the resolution state
                                    st.session_state.resolving_task = None
                                    st.session_state.resolving_option = None
                                    st.session_state.rerun_scheduler = True
                                    st.rerun()
                
                # Display large tasks section if there are any
                if large_tasks:
                    st.subheader("Large Tasks")
                    
                    large_task_df = pd.DataFrame([
                        {
                            "Task": task['Task'],
                            "Hours": task['Estimated Time'],
                            "Due Date": task['Due Date'] if pd.notnull(task['Due Date']) else "None"
                        }
                        for _, task in large_tasks
                    ])
                    
                    st.dataframe(large_task_df)
                    
                    # Add a button to start the breakdown wizard
                    st.info("Use the Task Breakdown Wizard to break down large tasks into manageable pieces.")
                    if st.button("Start Task Breakdown Wizard"):
                        start_wizard()
                        st.rerun()
                
                # Display scheduling warnings
                if warnings:
                    st.subheader("Scheduling Warnings")
                    
                    for warning in warnings:
                        if warning.startswith("HANDLE:"):
                            st.warning(warning)
            
            if 'rerun_scheduler' in st.session_state:
                del st.session_state['rerun_scheduler']
                
            # Clear resolution state if we're not actively resolving a task
            if 'resolving_task' in st.session_state and st.session_state.resolving_task is not None:
                # Keep the resolution state
                pass
            else:
                # Reset the resolution state when scheduler is run normally
                st.session_state.resolving_task = None
                st.session_state.resolving_option = None
    
    # Tab 4: Idea Backlog - NEW TAB
    with tab4:
        st.header("Idea Backlog")
        
        # Add form for new backlog items
        with st.form("add_backlog_item"):
            st.subheader("Add New Idea")
            idea_name = st.text_input("Idea Name")
            
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox(
                    "Category", 
                    options=["Work", "Personal", "Learning", "Project", "Other"]
                )
            with col2:
                status = st.selectbox(
                    "Status",
                    options=["New", "Evaluating", "Someday/Maybe"]
                )
                
            description = st.text_area("Description")
            submit_button = st.form_submit_button("Add to Backlog")
            
        if submit_button and idea_name:
            # Add new item to backlog
            new_item = pd.DataFrame({
                'Idea': [idea_name],
                'Category': [category],
                'Description': [description],
                'Creation Date': [pd.Timestamp.now()],
                'Status': [status]
            })
            
            backlog_df = pd.concat([backlog_df, new_item], ignore_index=True)
            backlog_df.to_csv(backlog_file, index=False)
            st.success(f"Added '{idea_name}' to backlog!")
        
        # Handle conversion of backlog items to tasks
        if st.session_state.converting_item is not None:
            item = st.session_state.converting_item
            idx = st.session_state.converting_idx
            
            st.subheader(f"Convert '{item['Idea']}' to Task")
            
            with st.form("convert_to_task"):
                task_name = st.text_input("Task Name", value=item['Idea'])
                
                col1, col2 = st.columns(2)
                with col1:
                    project = st.text_input("Project", value=item['Category'])
                with col2:
                    estimated_time = st.number_input("Estimated Time (hours)", min_value=0.5, step=0.5, value=1.0)
                
                col3, col4 = st.columns(2)
                with col3:
                    due_date = st.date_input("Due Date", value=pd.Timestamp.now() + pd.Timedelta(days=7))
                with col4:
                    importance = st.slider("Importance", min_value=1, max_value=5, value=3)
                
                complexity = st.slider("Complexity", min_value=1, max_value=5, value=3)
                
                col5, col6 = st.columns([1, 1])
                with col5:
                    cancel = st.form_submit_button("Cancel")
                with col6:
                    submit = st.form_submit_button("Create Task")
                
                if cancel:
                    st.session_state.converting_item = None
                    st.session_state.converting_idx = None
                    st.rerun()
                
                if submit:
                    # Create the new task
                    new_task = pd.DataFrame({
                        'Project': [project],
                        'Task': [task_name],
                        'Estimated Time': [estimated_time],
                        'Due Date': [pd.to_datetime(due_date)],
                        'Importance': [importance],
                        'Complexity': [complexity]
                    })
                    
                    # Add to tasks and remove from backlog
                    tasks_df = pd.concat([tasks_df, new_task], ignore_index=True)
                    tasks_df.to_csv(tasks_file, index=False)
                    
                    # Remove from backlog
                    backlog_df = backlog_df.drop(idx)
                    backlog_df.to_csv(backlog_file, index=False)
                    
                    st.success(f"Successfully converted '{task_name}' to a task!")
                    st.session_state.converting_item = None
                    st.session_state.converting_idx = None
                    st.rerun()
        
        # Display and manage existing backlog items
        if not backlog_df.empty:
            st.subheader("Current Backlog")
            
            # Add filtering options
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                filter_category = st.multiselect(
                    "Filter by Category",
                    options=backlog_df['Category'].unique()
                )
            with filter_col2:
                filter_status = st.multiselect(
                    "Filter by Status",
                    options=backlog_df['Status'].unique()
                )
            
            # Apply filters
            filtered_df = backlog_df
            if filter_category:
                filtered_df = filtered_df[filtered_df['Category'].isin(filter_category)]
            if filter_status:
                filtered_df = filtered_df[filtered_df['Status'].isin(filter_status)]
            
            # Display the backlog items with actions
            for idx, item in filtered_df.iterrows():
                with st.expander(f"{item['Idea']} ({item['Category']})"):
                    cols = st.columns([3, 1, 1])
                    
                    with cols[0]:
                        st.markdown(f"**Description:** {item['Description']}")
                        st.markdown(f"**Created:** {pd.to_datetime(item['Creation Date']).strftime('%Y-%m-%d')}")
                        st.markdown(f"**Status:** {item['Status']}")
                    
                    with cols[1]:
                        if st.button("Convert to Task", key=f"convert_{idx}"):
                            # Store the item for conversion
                            st.session_state.converting_item = item
                            st.session_state.converting_idx = idx
                            st.rerun()
                    
                    with cols[2]:
                        if st.button("Remove", key=f"remove_{idx}"):
                            backlog_df = backlog_df.drop(idx)
                            backlog_df.to_csv(backlog_file, index=False)
                            st.success(f"Removed '{item['Idea']}' from backlog.")
                            st.rerun()
        else:
            st.info("Your backlog is empty. Add ideas using the form above.")
