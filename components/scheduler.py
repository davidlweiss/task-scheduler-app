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

def schedule_tasks(tasks_df, working_free_time_df):
    """
    Schedule tasks based on priority and available time.
    Modified to better handle date comparisons and ensure fair allocation.
    """
    scheduled_tasks = []
    warnings = []
    unallocated_tasks = []
    
    # Prioritize tasks - make a copy to avoid modifying the original
    tasks_df = calculate_task_priority(tasks_df.copy())
    
    # Important fix: Ensure all dates are properly normalized to date-only (no time component)
    # This prevents inequality due to time components
    today = pd.to_datetime(datetime.today().date())
    
    # Normalize due dates to remove time components for comparison
    tasks_df['Due Date'] = tasks_df['Due Date'].apply(lambda x: x.normalize() if pd.notnull(x) else x)
    working_free_time_df['Date'] = working_free_time_df['Date'].apply(lambda x: x.normalize() if pd.notnull(x) else x)
    
    # Group tasks by due date first to ensure fair allocation
    # This ensures all tasks due on the same day get a fair chance at the available time
    if not working_free_time_df.empty:
        # Get unique due dates from tasks, sorted
        due_dates = tasks_df['Due Date'].dropna().unique()
        due_dates = sorted(due_dates)
        
        # First pass - allocate time for each due date's tasks
        for due_date in due_dates:
            # Get tasks for this due date
            day_tasks = tasks_df[tasks_df['Due Date'] == due_date]
            
            # Skip if no tasks for this day
            if day_tasks.empty:
                continue
                
            # Get available time windows up to this due date
            available_windows = working_free_time_df[working_free_time_df['Date'] <= due_date]
            
            # Skip if no available windows
            if available_windows.empty:
                # All tasks for this due date are unallocated
                for idx, task in day_tasks.iterrows():
                    unallocated_tasks.append({
                        'Task': task['Task'],
                        'Task Index': idx,
                        'Due Date': task['Due Date'],
                        'Total Hours': task['Estimated Time'],
                        'Allocated Hours': 0,
                        'Unallocated Hours': task['Estimated Time']
                    })
                continue
            
            # Calculate total available hours up to due date
            total_available = available_windows['Available Hours'].sum()
            
            # Calculate total needed hours for this due date
            total_needed = day_tasks['Estimated Time'].sum()
            
            # If not enough time, allocate proportionally based on priority
            if total_needed > total_available and total_available > 0:
                # Calculate priority-weighted allocation
                day_tasks['Priority Score'] = day_tasks.apply(
                    lambda row: row['Importance'] * 2 + (5 - row['Complexity']), 
                    axis=1
                )
                total_priority = day_tasks['Priority Score'].sum()
                
                if total_priority > 0:
                    # Allocate hours proportionally based on priority weight
                    day_tasks['Allocated'] = day_tasks.apply(
                        lambda row: min(row['Estimated Time'], (row['Priority Score'] / total_priority) * total_available),
                        axis=1
                    )
                else:
                    # Equal distribution if priorities sum to zero
                    day_tasks['Allocated'] = day_tasks.apply(
                        lambda row: min(row['Estimated Time'], total_available / len(day_tasks)),
                        axis=1
                    )
            else:
                # Enough time available, allocate full hours
                day_tasks['Allocated'] = day_tasks['Estimated Time']
            
            # Allocate the hours for each task in this due date group
            for idx, task in day_tasks.iterrows():
                allocated_hours = task['Allocated']
                remaining_to_allocate = allocated_hours
                
                # Try to allocate across available windows
                for f_idx, window in available_windows.iterrows():
                    if remaining_to_allocate <= 0:
                        break
                    
                    available_in_window = working_free_time_df.at[f_idx, 'Available Hours']
                    if available_in_window <= 0:
                        continue
                    
                    # Calculate how much to allocate in this window
                    allocate_now = min(remaining_to_allocate, available_in_window)
                    
                    if allocate_now > 0:
                        # Add to scheduled tasks
                        scheduled_tasks.append({
                            'Task': task['Task'],
                            'Date': window['Date'],
                            'Allocated Hours': allocate_now
                        })
                        
                        # Update remaining available in window
                        working_free_time_df.at[f_idx, 'Available Hours'] -= allocate_now
                        remaining_to_allocate -= allocate_now
                
                # Check if we have unallocated hours for this task
                actual_allocated = allocated_hours - remaining_to_allocate
                if actual_allocated < task['Estimated Time']:
                    unallocated_hours = task['Estimated Time'] - actual_allocated
                    
                    # Add to unallocated task list
                    if unallocated_hours > 0:
                        warnings.append(
                            f"HANDLE: {task['Task']} (Due: {task['Due Date'].date()}) "
                            f"needs {task['Estimated Time']}h, but only {actual_allocated}h scheduled before due date."
                        )
                        
                        unallocated_tasks.append({
                            'Task': task['Task'],
                            'Task Index': idx,
                            'Due Date': task['Due Date'],
                            'Total Hours': task['Estimated Time'],
                            'Allocated Hours': actual_allocated,
                            'Unallocated Hours': unallocated_hours
                        })
    
    # Identify large tasks separately from allocation issues
    for idx, task in tasks_df.iterrows():
        task_time = task['Estimated Time']
        task_name = task['Task']
        
        # Check for large tasks
        if task_time > 6 and not any(tag in str(task_name) for tag in ['[MULTI-SESSION]', '[FIXED EVENT]', '[PENDING PLANNING]']):
            warnings.append(
                f"Task '{task_name}' exceeds 6 hours and should probably be split unless it's a Work Block."
            )
    
    return scheduled_tasks, warnings, unallocated_tasks

def display_scheduling_results(scheduled_tasks, daily_summary):
    """
    Display the results of the scheduling algorithm.
    """
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
