import streamlit as st
import pandas as pd
import math
from datetime import datetime
from models.task import load_tasks, save_tasks, get_large_tasks

def start_wizard():
    """
    Initialize wizard mode with default values.
    """
    st.session_state.wizard_mode = True
    st.session_state.wizard_step = 1
    st.session_state.wizard_task_idx = None
    st.session_state.wizard_task = None
    st.session_state.wizard_approach = None

def exit_wizard():
    """
    Exit wizard mode and reset all wizard-related state.
    """
    st.session_state.wizard_mode = False
    st.session_state.wizard_step = 1
    st.session_state.wizard_task_idx = None
    st.session_state.wizard_task = None
    st.session_state.wizard_approach = None

def next_wizard_step():
    """
    Advance to the next wizard step.
    """
    st.session_state.wizard_step += 1

def prev_wizard_step():
    """
    Go back to the previous wizard step.
    """
    st.session_state.wizard_step = max(1, st.session_state.wizard_step - 1)

def run_wizard():
    """
    Run the task breakdown wizard interface.
    """
    st.title("Dynamic Task Scheduler V8")
    st.markdown("## Task Breakdown Wizard")
    
    # Create a progress bar
    progress_percentage = (st.session_state.wizard_step - 1) / 3  # 3 steps total
    st.progress(progress_percentage)
    
    # Show step indicator
    st.write(f"Step {st.session_state.wizard_step} of 3")
    
    # Run the appropriate step
    if st.session_state.wizard_step == 1:
        wizard_step_one()
    elif st.session_state.wizard_step == 2:
        wizard_step_two()
    elif st.session_state.wizard_step == 3:
        wizard_step_three()

def wizard_step_one():
    """
    Step 1: Select a task to break down.
    """
    st.subheader("Step 1: Select a Task to Break Down")
    
    # Load tasks
    tasks_df = load_tasks()
    
    # Identify large tasks
    large_tasks = get_large_tasks()
    
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

def wizard_step_two():
    """
    Step 2: Choose a breakdown approach.
    """
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

def wizard_step_three():
    """
    Step 3: Complete form for selected approach.
    """
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
        handle_planning_session(idx, task, task_name, hours)
    elif "Break into Subtasks" in approach:
        handle_break_into_subtasks(idx, task, task_name, hours)
    elif "Focus Sessions" in approach:
        handle_focus_sessions(idx, task, task_name, hours)
    elif "Iterative Project" in approach:
        handle_iterative_project(idx, task, task_name, hours)
    elif "Fixed Duration Event" in approach:
        handle_fixed_event(idx, task, task_name, hours)

def handle_planning_session(idx, task, task_name, hours):
    """
    Handle the 'Schedule a Planning Session' approach.
    """
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
            # Load tasks to ensure we're working with the latest data
            tasks_df = load_tasks()
            
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
            save_tasks(tasks_df)
            
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

def handle_break_into_subtasks(idx, task, task_name, hours):
    """
    Handle the 'Break into Subtasks' approach.
    """
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
                    min_value=float(0.5), 
                    max_value=float(hours), 
                    value=float(hours_value),
                    step=float(0.5),
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
            # Load tasks to ensure we're working with the latest data
            tasks_df = load_tasks()
            
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
            save_tasks(tasks_df)
            
            # Show success message
            st.success(f"Created {num_subtasks} subtasks. Original task has been removed.")
            
            # Auto-exit
            exit_wizard()
            st.rerun()

def handle_focus_sessions(idx, task, task_name, hours):
    """
    Handle the 'Focus Sessions' approach.
    """
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
            # Load tasks to ensure we're working with the latest data
            tasks_df = load_tasks()
            
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
            save_tasks(tasks_df)
            
            # Show success message
            st.success(f"Updated task to use {num_sessions} focus sessions of {session_length}h each.")
            
            # Auto-exit
            exit_wizard()
            st.rerun()

def handle_iterative_project(idx, task, task_name, hours):
    """
    Handle the 'Iterative Project' approach.
    """
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
            # Load tasks to ensure we're working with the latest data
            tasks_df = load_tasks()
            
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
            save_tasks(tasks_df)
            
            # Show success message
            st.success("Created iterative project structure with initial exploration session and placeholder for remaining work.")
            
            # Auto-exit
            exit_wizard()
            st.rerun()

def handle_fixed_event(idx, task, task_name, hours):
    """
    Handle the 'Fixed Duration Event' approach.
    """
    with st.form(key="fixed_event_form"):
        st.write("Mark this task as a fixed-duration event that doesn't need to be broken down.")
        
        # Option to update the task name
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
            mark_fixed = st.form_submit_button("Mark as Fixed Event")
        
        if previous_step:
            prev_wizard_step()
            st.rerun()
        
        if cancel:
            exit_wizard()
            st.rerun()
        
        if mark_fixed:
            # Load tasks to ensure we're working with the latest data
            tasks_df = load_tasks()
            
            # Update the task name if requested
            if update_name:
                tasks_df.at[idx, 'Task'] = new_name
            
            # Add metadata about fixed event - make sure column exists
            if 'Fixed Event' not in tasks_df.columns:
                tasks_df['Fixed Event'] = False
            
            tasks_df.at[idx, 'Fixed Event'] = True
            
            # Save changes
            save_tasks(tasks_df)
            
            # Show success message
            st.success(f"Marked '{task_name}' as a fixed event.")
            
            # Auto-exit
            exit_wizard()
            st.rerun()
