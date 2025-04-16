import streamlit as st
from models.task import load_tasks, save_tasks

def show_task_manager():
    """
    Display and manage tasks in the Task Manager tab.
    """
    st.header("Edit Tasks")
    
    # Load current tasks
    tasks_df = load_tasks()
    
    # Provide view-only mode for sorting
    if st.checkbox("Enable Sorting Mode (View Only)"):
        st.dataframe(tasks_df, use_container_width=True)
    else:
        # Use data editor for full editing capabilities
        edited_tasks_df = st.data_editor(
            tasks_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={"Task": st.column_config.Column(width='large')},
            disabled=False,
            key="task_editor"
        )
        
        # Save changes when button is pressed
        if st.button("Save Tasks"):
            save_tasks(edited_tasks_df)
            st.success("Tasks saved successfully!")
            
            # Return the updated dataframe for any subsequent operations
            return edited_tasks_df
            
    return tasks_df
