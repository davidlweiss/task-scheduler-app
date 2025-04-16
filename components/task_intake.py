import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from models.task import load_tasks, save_tasks, add_task
from models.backlog import load_backlog, save_backlog, add_backlog_item

def show_task_intake_wizard():
    """
    Display a wizard-style task intake form showing one question at a time.
    """
    st.header("New Task Intake")
    
    # Initialize session state for the wizard if needed
    if 'intake_step' not in st.session_state:
        st.session_state.intake_step = 1
    if 'task_data' not in st.session_state:
        st.session_state.task_data = {}
    
    # Display progress indicator
    st.progress(st.session_state.intake_step / 6)
    st.write(f"Step {st.session_state.intake_step} of 6")
    
    # Step 1: Task name
    if st.session_state.intake_step == 1:
        st.subheader("What is the task?")
        task_name = st.text_input("Task Name", value=st.session_state.task_data.get('task_name', ''))
        
        if st.button("Next"):
            if task_name.strip():  # Validate that task name is not empty
                st.session_state.task_data['task_name'] = task_name
                st.session_state.intake_step += 1
                st.rerun()
            else:
                st.error("Please enter a task name")
    
    # Step 2: Certainty
    elif st.session_state.intake_step == 2:
        st.subheader("How much certainty do you have about execution?")
        certainty = st.radio(
            "Select level of certainty:",
            options=["None at all (needs planning)", "Some certainty", "Quite certain"],
            index=1  # Default to "Some certainty"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back"):
                st.session_state.intake_step -= 1
                st.rerun()
        with col2:
            if st.button("Next"):
                st.session_state.task_data['certainty'] = certainty
                st.session_state.intake_step += 1
                st.rerun()
    
    # Step 3: Complexity
    elif st.session_state.intake_step == 3:
        st.subheader("How complex is this task?")
        complexity_options = [
            "No idea yet", 
            "Not at all complex (1)", 
            "Somewhat complex (3)", 
            "Very complex (5)"
        ]
        complexity = st.radio(
            "Select complexity level:",
            options=complexity_options,
            index=1  # Default to "Not at all complex"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back"):
                st.session_state.intake_step -= 1
                st.rerun()
        with col2:
            if st.button("Next"):
                st.session_state.task_data['complexity'] = complexity
                # Extract numeric value if present
                if "(1)" in complexity:
                    st.session_state.task_data['complexity_value'] = 1
                elif "(3)" in complexity:
                    st.session_state.task_data['complexity_value'] = 3
                elif "(5)" in complexity:
                    st.session_state.task_data['complexity_value'] = 5
                else:
                    st.session_state.task_data['complexity_value'] = None
                st.session_state.intake_step += 1
                st.rerun()
    
    # Step 4: Time Estimate
    elif st.session_state.intake_step == 4:
        st.subheader("How long do you think this will take?")
        time_options = [
            "No idea",
            "Less than an hour",
            "More than an hour",
            "Many hours"
        ]
        time_estimate = st.radio(
            "Select time estimate:",
            options=time_options,
            index=0  # Default to "No idea"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back"):
                st.session_state.intake_step -= 1
                st.rerun()
        with col2:
            if st.button("Next"):
                st.session_state.task_data['time_estimate'] = time_estimate
                st.session_state.intake_step += 1
                st.rerun()
    
    # Step 5: Importance
    elif st.session_state.intake_step == 5:
        st.subheader("Is this task very important?")
        importance_col1, importance_col2 = st.columns(2)
        
        with importance_col1:
            if st.button("Yes", use_container_width=True):
                st.session_state.task_data['importance'] = True
                st.session_state.intake_step += 1
                st.rerun()
        
        with importance_col2:
            if st.button("No", use_container_width=True):
                st.session_state.task_data['importance'] = False
                st.session_state.intake_step += 1
                st.rerun()
        
        if st.button("Back"):
            st.session_state.intake_step -= 1
            st.rerun()
    
    # Step 6: Due Date
    elif st.session_state.intake_step == 6:
        st.subheader("When does this need to be completed?")
        due_date_type = st.radio(
            "Select due date type:",
            options=["No specific due date", "Specific due date", "Broad timeframe"]
        )
        
        if due_date_type == "Specific due date":
            due_date = st.date_input("Select date:", value=datetime.today() + timedelta(days=7))
            st.session_state.task_data['due_date'] = due_date
            st.session_state.task_data['due_date_type'] = due_date_type
        elif due_date_type == "Broad timeframe":
            timeframe = st.selectbox("Select timeframe:", options=["This week", "Next week"])
            
            # Calculate actual date based on timeframe
            today = datetime.today()
            # Find the Friday of current or next week
            days_until_friday = (4 - today.weekday()) % 7  # 4 = Friday (0-based, Monday=0)
            
            if timeframe == "This week":
                friday_date = today + timedelta(days=days_until_friday)
            else:  # Next week
                friday_date = today + timedelta(days=days_until_friday + 7)
            
            st.session_state.task_data['due_date'] = friday_date
            st.session_state.task_data['due_date_type'] = due_date_type
            st.session_state.task_data['timeframe'] = timeframe
        else:  # No specific due date
            st.session_state.task_data['due_date'] = None
            st.session_state.task_data['due_date_type'] = due_date_type
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Back"):
                st.session_state.intake_step -= 1
                st.rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state.intake_step = 1
                st.session_state.task_data = {}
                st.rerun()
        with col3:
            if st.button("Submit"):
                # Process form submission
                destination, item_data = process_task_submission(st.session_state.task_data)
                
                # Show appropriate success message
                if destination == "tasks":
                    if "[PLANNING]" in item_data['Task']:
                        st.success("Added a 30-minute planning session to your tasks!")
                    else:
                        st.success("Task added successfully to your task list!")
                else:  # backlog
                    st.success("Item added to your backlog for future consideration!")
                
                # Reset form
                st.session_state.intake_step = 1
                st.session_state.task_data = {}
                
                # Provide option to go back to main app
                if st.button("Return to Main App"):
                    st.rerun()
    
    # Display a summary of selections so far
    if st.session_state.intake_step > 1:
        with st.expander("Your selections so far"):
            for key, value in st.session_state.task_data.items():
                if key not in ['complexity_value'] and not key.endswith('_value'):
                    # Format the key for display
                    display_key = key.replace('_', ' ').title()
                    
                    # Format the value for display
                    if key == 'importance':
                        display_value = "Yes" if value else "No"
                    elif key == 'due_date' and value is not None:
                        if isinstance(value, datetime):
                            display_value = value.strftime('%Y-%m-%d')
                        else:
                            display_value = str(value)
                    else:
                        display_value = str(value)
                    
                    st.write(f"**{display_key}:** {display_value}")

def process_task_submission(task_data):
    """
    Process the completed task form and determine whether to add to backlog or tasks.
    
    Returns a tuple of (destination, item_data) where:
    - destination is either "tasks" or "backlog"
    - item_data is the dictionary of data added to that destination
    """
    # Check for key decision factors
    has_due_date = task_data.get('due_date_type', 'No specific due date') != 'No specific due date'
    is_important = task_data.get('importance', False)
    
    # Check for ambiguity (no certainty, unknown complexity, unknown time)
    is_ambiguous = (
        task_data.get('certainty') == 'None at all (needs planning)' or
        task_data.get('complexity') == 'No idea yet' or
        task_data.get('time_estimate') == 'No idea'
    )
    
    # Extract the due date
    due_date = None
    if has_due_date:
        due_date = task_data.get('due_date')
    
    # DECISION TREE
    if has_due_date:
        if is_ambiguous:
            # Has due date but ambiguous -> 30min planning session
            planning_task = create_planning_session(task_data, due_date)
            # Use the task_data dictionary directly instead of using add_task
            tasks_df = load_tasks()
            new_task = pd.DataFrame([planning_task])
            tasks_df = pd.concat([tasks_df, new_task], ignore_index=True)
            save_tasks(tasks_df)
            return "tasks", planning_task
        else:
            # Has due date and not ambiguous -> regular task
            regular_task = create_regular_task(task_data, due_date)
            # Use the task_data dictionary directly instead of using add_task
            tasks_df = load_tasks()
            new_task = pd.DataFrame([regular_task])
            tasks_df = pd.concat([tasks_df, new_task], ignore_index=True)
            save_tasks(tasks_df)
            return "tasks", regular_task
    else:  # No due date
        if is_important:
            # Important but no due date -> 30min planning session (due tomorrow)
            tomorrow = datetime.today() + timedelta(days=1)
            planning_task = create_planning_session(task_data, tomorrow)
            # Use the task_data dictionary directly instead of using add_task
            tasks_df = load_tasks()
            new_task = pd.DataFrame([planning_task])
            tasks_df = pd.concat([tasks_df, new_task], ignore_index=True)
            save_tasks(tasks_df)
            return "tasks", planning_task
        else:
            # Not important and no due date -> backlog
            backlog_item = create_backlog_item(task_data)
            # Use the dictionary directly instead of using add_backlog_item
            backlog_df = load_backlog()
            new_item = pd.DataFrame([backlog_item])
            backlog_df = pd.concat([backlog_df, new_item], ignore_index=True)
            save_backlog(backlog_df)
            return "backlog", backlog_item

def create_planning_session(task_data, due_date):
    """Create a 30-minute planning session task."""
    task_name = task_data.get('task_name', 'New Task')
    
    return {
        'Project': 'Planning',
        'Task': f"[PLANNING] {task_name}",
        'Estimated Time': 0.5,  # 30 minutes
        'Due Date': due_date,
        'Importance': 5 if task_data.get('importance', False) else 3,
        'Complexity': 2  # Planning sessions are moderate complexity
    }

def create_regular_task(task_data, due_date):
    """Create a regular task with appropriate estimated time based on complexity and time estimate."""
    # Map time estimate to hours
    time_mapping = {
        'Less than an hour': 0.5,
        'More than an hour': 2.0,
        'Many hours': 4.0,
        'No idea': 1.0  # Fallback, though this shouldn't happen in this path
    }
    
    # Get complexity value
    complexity_value = task_data.get('complexity_value', 3)
    
    # Determine estimated time
    estimated_time = time_mapping.get(task_data.get('time_estimate', 'More than an hour'))
    
    # Flag for wizard if needed
    needs_wizard = (
        task_data.get('time_estimate') == 'Many hours' or
        complexity_value == 5
    )
    
    task_name = task_data.get('task_name', 'New Task')
    if needs_wizard:
        task_name += " [NEEDS BREAKDOWN]"
    
    return {
        'Project': 'General',  # This could be improved by adding a project field
        'Task': task_name,
        'Estimated Time': estimated_time,
        'Due Date': due_date,
        'Importance': 5 if task_data.get('importance', False) else 3,
        'Complexity': complexity_value if complexity_value is not None else 3
    }

def create_backlog_item(task_data):
    """Create a backlog item for future consideration."""
    return {
        'Idea': task_data.get('task_name', 'New Idea'),
        'Category': 'General',  # This could be improved by adding a category field
        'Description': f"Complexity: {task_data.get('complexity')}, Time: {task_data.get('time_estimate')}, Important: {'Yes' if task_data.get('importance', False) else 'No'}",
        'Creation Date': datetime.now(),
        'Status': 'New'
    }
