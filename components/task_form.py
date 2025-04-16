import streamlit as st
from models.task import load_tasks, save_tasks
import pandas as pd

def show_task_manager():
    """
    Display and manage tasks in the Task Manager tab.
    """
    st.header("Edit Tasks")
    
    # Load current tasks
    tasks_df = load_tasks()
    
    # Convert 'Due Date' to date only (without time) if it exists
    if 'Due Date' in tasks_df.columns and not tasks_df.empty:
        tasks_df['Due Date'] = pd.to_datetime(tasks_df['Due Date']).dt.date
    
    # Provide view-only mode for sorting
    if st.checkbox("Enable Sorting Mode (View Only)"):
        st.dataframe(tasks_df, use_container_width=True, hide_index=True)
    else:
        # Use data editor for full editing capabilities
        edited_tasks_df = st.data_editor(
            tasks_df,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Task": st.column_config.Column(width='large'),
                "Due Date": st.column_config.DateColumn(
                    "Due Date",
                    format="YYYY-MM-DD",
                    step=1,
                ),
            },
            disabled=False,
            key="task_editor"
        )
        
        # Convert dates back to datetime for storage
        if 'Due Date' in edited_tasks_df.columns and not edited_tasks_df.empty:
            edited_tasks_df['Due Date'] = pd.to_datetime(edited_tasks_df['Due Date'])
        
        # Save changes when button is pressed
        if st.button("Save Tasks"):
            save_tasks(edited_tasks_df)
            st.success("Tasks saved successfully!")
            
            # Return the updated dataframe for any subsequent operations
            return edited_tasks_df
    
    return tasks_df
