import streamlit as st
import pandas as pd
from datetime import datetime
from models.task import load_tasks, save_tasks, calculate_task_priority, get_large_tasks
from models.free_time import load_free_time, get_total_free_time
from components.wizard import start_wizard

def run_scheduler():
    """
    Run the scheduling algorithm and display results.
    """
    st.header("Run Scheduler")
    
    # Initialize storage for action results if needed
    if 'action_results' not in st.session_state:
        st.session_state['action_results'] = []
    
    # Run scheduler button
    run_button = st.button("Run Scheduler")
    
    if run_button or 'rerun_scheduler' in st.session_state:
        st.subheader("Scheduled Tasks")
        
        # Load data
        tasks_df = load_tasks()
        free_time_df = load_free_time()
        
        # Calculate capacity vs demand
        total_free_time = get_total_free_time()
        total_estimated_time = tasks_df['Estimated Time'].sum() if not tasks_df.empty else 0
        
        # Display capacity summary
        display_capacity_summary(total_free_time, total_estimated_time)
        
        # Create a working copy of free time dataframe for scheduling
        working_free_time_df = free_time_df.copy()
        if 'Sort Order' in working_free_time_df.columns:
            working_free_time_df = working_free_time_df.drop('Sort Order', axis=1)
        
        working_free_time_df['Date'] = pd.to_datetime(working_free_time_df['Date'])
        working_free_time_df = working_free_time_df.sort_values(by='Date')
        
        # Create daily summary from current free time dataframe
        daily_summary = create_daily_summary(working_free_time_df)
        
        # Run the scheduling algorithm if we have tasks
        if not tasks_df.empty:
            scheduled_tasks, warnings, unallocated_tasks = schedule_tasks(tasks_df, working_free_time_df)
            
            # Display the scheduling results
            display_scheduling_results(scheduled_tasks, daily_summary)
            
            # Handle unallocated tasks
            if unallocated_tasks:
                handle_unallocated_tasks(unallocated_tasks, tasks_df)
            
            # Display large tasks that need breakdown
            display_large_tasks()
            
            # Display scheduling warnings
            if warnings:
                st.subheader("Scheduling Warnings")
                for warning in warnings:
                    if warning.startswith("HANDLE:"):
                        st.warning(warning)
        
        # Clear rerun flag if it exists
        if 'rerun_scheduler' in st.session_state:
            del st.session_state['rerun_scheduler']

def display_capacity_summary(total_free_time, total_estimated_time):
    """
    Display summary of total capacity vs demand.
    """
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

def create_daily_summary(free_time_df):
    """
    Create a summary of available hours by date.
    """
    if free_time_df.empty:
        return pd.DataFrame(columns=['Date', 'Total Available'])
        
    return (
        free_time_df.groupby('Date')['Available Hours']
        .sum()
        .reset_index()
        .rename(columns={'Available Hours': 'Total Available'})
    )

def schedule_tasks(tasks, available_hours, start_date, end_date):
    """
    Automatically creates an optimal schedule for tasks given available time.
    
    Parameters:
    - tasks: DataFrame containing task data (name, estimated_time, due_date, importance, complexity, etc.)
    - available_hours: Total hours available in the scheduling period
    - start_date: First day of scheduling period
    - end_date: Last day of scheduling period
    
    Returns:
    - schedule: DataFrame with daily task allocations
    - unallocated: DataFrame with tasks that couldn't be fully scheduled
    """
    # Calculate total task hours
    total_task_hours = tasks['Estimated Time'].sum()
    
    # Create day containers from start_date to end_date
    days = create_day_containers(start_date, end_date, available_hours)
    
    # Sort tasks by urgency and importance
    prioritized_tasks = prioritize_tasks(tasks)
    
    # Initialize tracking variables
    scheduled_tasks = []
    unallocated_tasks = []
    remaining_hours = available_hours
    
    # First pass: Schedule tasks with hard deadlines
    deadline_tasks = prioritized_tasks[prioritized_tasks['Due Date'].notnull()]
    for _, task in deadline_tasks.iterrows():
        scheduled_hours = schedule_task(task, days, remaining_hours)
        remaining_hours -= scheduled_hours
        
        if scheduled_hours < task['Estimated Time']:
            # Track partially scheduled tasks
            unallocated_tasks.append({
                'Task': task['Task'],
                'Unallocated Hours': task['Estimated Time'] - scheduled_hours,
                'Reason': 'Insufficient time before deadline'
            })
    
    # Second pass: Handle focus session tasks
    focus_tasks = prioritized_tasks[prioritized_tasks['Focus Sessions'].notnull()]
    for _, task in focus_tasks.iterrows():
        if task['Task'] not in [t['Task'] for t in unallocated_tasks]:
            schedule_focus_sessions(task, days, remaining_hours)
    
    # Third pass: Similar task batching
    task_groups = group_similar_tasks(prioritized_tasks)
    for group in task_groups:
        schedule_task_group(group, days, remaining_hours)
    
    # Final pass: Remaining tasks by priority
    for _, task in prioritized_tasks.iterrows():
        if task['Task'] not in [t['Task'] for t in scheduled_tasks + unallocated_tasks]:
            scheduled_hours = schedule_task(task, days, remaining_hours)
            remaining_hours -= scheduled_hours
            
            if scheduled_hours < task['Estimated Time']:
                unallocated_tasks.append({
                    'Task': task['Task'],
                    'Unallocated Hours': task['Estimated Time'] - scheduled_hours,
                    'Reason': 'Insufficient total capacity'
                })
    
    # Generate final schedule representation
    schedule = create_schedule_representation(days)
    
    return schedule, unallocated_tasks

def prioritize_tasks(tasks):
    """
    Create a priority score combining deadline urgency and importance.
    """
    today = pd.to_datetime(datetime.today().date())
    
    def calculate_priority(row):
        # If task is due today or past due, give highest priority
        if pd.notnull(row['Due Date']):
            days_until_due = (row['Due Date'] - today).days
            if days_until_due <= 0:
                return -9999  # Highest priority for overdue
            
            # Priority formula: balances days until due with importance
            deadline_factor = 10 / (days_until_due + 1)  # Higher weight for closer deadlines
            return -(deadline_factor * row['Importance'] * 10)
        else:
            # For tasks without deadlines, use importance as base priority
            return -row['Importance']
    
    tasks['Priority'] = tasks.apply(calculate_priority, axis=1)
    return tasks.sort_values('Priority')

def group_similar_tasks(tasks):
    """
    Group tasks that are similar in nature for batching.
    """
    groups = []
    
    # Example: Group by project
    project_groups = tasks.groupby('Project')
    for project, group_tasks in project_groups:
        groups.append(group_tasks)
    
    # Additional grouping: Find tasks with similar names
    # (e.g., all "Document" tasks)
    keyword_patterns = ['Document', 'Review', 'Refactor']
    for pattern in keyword_patterns:
        matching_tasks = tasks[tasks['Task'].str.contains(pattern)]
        if not matching_tasks.empty:
            groups.append(matching_tasks)
    
    return groups

def schedule_task(task, days, remaining_hours):
    """
    Schedule a single task across available days.
    """
    task_hours = task['Estimated Time']
    scheduled_hours = 0
    
    # If task has a due date, only consider days before due date
    due_date = task['Due Date'] if pd.notnull(task['Due Date']) else days[-1]['date']
    
    for day in days:
        if day['date'] > due_date:
            break
            
        if day['available_hours'] > 0 and scheduled_hours < task_hours:
            # Determine hours to allocate to this day
            allocate = min(day['available_hours'], task_hours - scheduled_hours)
            
            # Add to day's schedule
            day['schedule'].append({
                'Task': task['Task'],
                'Hours': allocate,
                'Start Time': calculate_start_time(day)
            })
            
            # Update tracking
            day['available_hours'] -= allocate
            scheduled_hours += allocate
            
            # If fully scheduled, break
            if scheduled_hours >= task_hours:
                break
    
    return scheduled_hours

def schedule_focus_sessions(task, days, remaining_hours):
    """
    Schedule a task with focus sessions, respecting session length.
    """
    sessions = int(task['Focus Sessions'])
    session_length = float(task['Session Length'])
    
    # Try to schedule each session as a continuous block
    for i in range(sessions):
        for day in days:
            if day['available_hours'] >= session_length:
                # Add session to day's schedule
                day['schedule'].append({
                    'Task': f"{task['Task']} (Session {i+1})",
                    'Hours': session_length,
                    'Start Time': calculate_start_time(day)
                })
                
                # Update tracking
                day['available_hours'] -= session_length
                break
    
    return sessions * session_length

def create_schedule_representation(days):
    """
    Convert the internal days structure to a user-friendly schedule.
    """
    schedule = []
    
    for day in days:
        date_str = day['date'].strftime('%A, %B %d')
        
        # Group by morning/afternoon
        morning = []
        afternoon = []
        
        for task in day['schedule']:
            if task['Start Time'] < 12:
                morning.append(task)
            else:
                afternoon.append(task)
        
        # Add to schedule
        schedule.append({
            'Date': date_str,
            'Morning': morning,
            'Afternoon': afternoon,
            'Total Hours': sum(task['Hours'] for task in day['schedule'])
        })
    
    return schedule

def display_scheduling_results(scheduled_tasks, daily_summary):
    """
    Display the results of the scheduling algorithm.
    """
    if not scheduled_tasks:
        st.info("No tasks could be scheduled with the current free time availability.")
        return
        
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
        
        # Check if daily_summary is empty
        if daily_summary.empty:
            st.dataframe(daily_scheduled)
        else:
            daily_summary = daily_summary.merge(daily_scheduled, on='Date', how='left').fillna(0)
            st.dataframe(daily_summary)
        
        # Create task-by-date pivot table
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

def handle_unallocated_tasks(unallocated_tasks, tasks_df):
    """
    Display and provide resolution options for tasks with insufficient allocated time.
    """
    if not unallocated_tasks:
        return
        
    st.subheader("Tasks with Insufficient Hours")
    
    # Create a dataframe of unallocated tasks
    unallocated_df = pd.DataFrame(unallocated_tasks)
    st.dataframe(unallocated_df[['Task', 'Due Date', 'Total Hours', 'Allocated Hours', 'Unallocated Hours']])
    
    # Let user select a task to resolve
    task_options = [task['Task'] for task in unallocated_tasks]
    selected_task_name = st.selectbox("Select a task to resolve:", task_options)
    
    # Find the selected task details
    selected_task = next((task for task in unallocated_tasks if task['Task'] == selected_task_name), None)
    
    if selected_task:
        st.markdown(f"### Resolve scheduling for: {selected_task['Task']}")
        st.markdown(f"**Due date:** {selected_task['Due Date'].date()}")
        st.markdown(f"**Current allocation:** {selected_task['Allocated Hours']} of {selected_task['Total Hours']} hours")
        st.markdown(f"**Unallocated hours:** {selected_task['Unallocated Hours']} hours")
        
        # Use a form for the resolution options
        with st.form(key="resolution_form"):
            st.subheader("Resolution Options")
            
            # Show resolution options
            resolution_options = [
                "Reduce task hours estimate",
                "Add more free time",
                "Break down into subtasks",
                "Extend the due date",
                "Mark as partially completed"
            ]
            
            resolution_choice = st.radio("How would you like to resolve this?", resolution_options)
            
            # Show input fields based on the selected option
            if resolution_choice == "Reduce task hours estimate":
                new_estimate = st.number_input(
                    "New total hour estimate:", 
                    min_value=float(selected_task['Allocated Hours']), 
                    max_value=float(selected_task['Total Hours']), 
                    value=float(selected_task['Allocated Hours']),
                    step=0.5
                )
                
            elif resolution_choice == "Add more free time":
                # Calculate days until due
                today = pd.Timestamp(datetime.today().date())
                days_until_due = max(1, (selected_task['Due Date'] - today).days)
                
                col1, col2 = st.columns(2)
                with col1:
                    days_to_add = st.slider("Days to add free time:", 1, days_until_due, 1)
                with col2:
                    hours_per_day = st.number_input(
                        "Hours per day:", 
                        min_value=0.5, 
                        value=float(selected_task['Unallocated Hours']/min(days_to_add, days_until_due)),
                        step=0.5
                    )
            
            elif resolution_choice == "Break down into subtasks":
                st.write("Task will be sent to the Task Breakdown Wizard.")
                
            elif resolution_choice == "Extend the due date":
                new_due_date = st.date_input(
                    "New due date:", 
                    value=selected_task['Due Date'], 
                    min_value=selected_task['Due Date'].date()
                )
            
            elif resolution_choice == "Mark as partially completed":
                progress_percentage = st.slider(
                    "What percentage of this task is already completed?", 
                    min_value=0, 
                    max_value=100, 
                    value=int((selected_task['Allocated Hours'] / selected_task['Total Hours']) * 100)
                )
                
                remaining_hours = selected_task['Total Hours'] * (1 - progress_percentage / 100)
                st.write(f"This will update the task to {remaining_hours:.1f} hours remaining.")
            
            # Form submission button
            submit_button = st.form_submit_button("Apply This Resolution")
        
        # Handle form submission - this only runs after the form is submitted
        if submit_button:
            # Process the selected resolution
            if resolution_choice == "Reduce task hours estimate":
                task_idx = selected_task['Task Index']
                tasks_df.at[task_idx, 'Estimated Time'] = new_estimate
                save_tasks(tasks_df)
                st.success(f"Updated estimate for '{selected_task['Task']}' to {new_estimate} hours.")
                st.session_state.rerun_scheduler = True
                st.rerun()
            
            elif resolution_choice == "Add more free time":
                from models.free_time import add_free_time
                
                # Calculate dates to add free time
                today = pd.Timestamp(datetime.today().date())
                dates_to_add = []
                for i in range(days_to_add):
                    date = today + pd.Timedelta(days=i)
                    if date <= selected_task['Due Date']:
                        dates_to_add.append(date)
                
                # Add free time to each date
                for date in dates_to_add:
                    add_free_time(date, hours_per_day)
                
                st.success(f"Added {hours_per_day * len(dates_to_add)} hours of free time across {len(dates_to_add)} days.")
                st.session_state.rerun_scheduler = True
                st.rerun()
            
            elif resolution_choice == "Break down into subtasks":
                # Store the task index to break down in the wizard
                st.session_state.wizard_task_idx = selected_task['Task Index']
                st.session_state.wizard_task = tasks_df.loc[selected_task['Task Index']].to_dict()
                start_wizard()
                st.rerun()
            
            elif resolution_choice == "Extend the due date":
                task_idx = selected_task['Task Index']
                tasks_df.at[task_idx, 'Due Date'] = pd.to_datetime(new_due_date)
                save_tasks(tasks_df)
                st.success(f"Updated due date for '{selected_task['Task']}' to {new_due_date}.")
                st.session_state.rerun_scheduler = True
                st.rerun()
            
            elif resolution_choice == "Mark as partially completed":
                task_idx = selected_task['Task Index']
                remaining_hours = selected_task['Total Hours'] * (1 - progress_percentage / 100)
                tasks_df.at[task_idx, 'Estimated Time'] = remaining_hours
                
                # Optionally add "[IN PROGRESS]" tag to task name
                current_task_name = tasks_df.at[task_idx, 'Task']
                if not "[IN PROGRESS]" in current_task_name:
                    tasks_df.at[task_idx, 'Task'] = f"{current_task_name} [IN PROGRESS {progress_percentage}%]"
                
                save_tasks(tasks_df)
                st.success(f"Updated progress for '{selected_task['Task']}' to {progress_percentage}% complete.")
                st.session_state.rerun_scheduler = True
                st.rerun()

def display_large_tasks():
    """
    Display large tasks and offer to break them down.
    """
    large_tasks = get_large_tasks()
    
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
