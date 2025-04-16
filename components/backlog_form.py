import streamlit as st
import pandas as pd
from models.backlog import load_backlog, save_backlog, add_backlog_item, delete_backlog_item
from models.task import add_task

def show_backlog_manager():
    """
    Display and manage idea backlog in the Backlog tab.
    """
    st.header("Idea Backlog")
    
    # Load backlog data
    backlog_df = load_backlog()
    
    # Initialize session state for backlog conversion
    if 'converting_item' not in st.session_state:
        st.session_state.converting_item = None
    if 'converting_idx' not in st.session_state:
        st.session_state.converting_idx = None
    
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
        
    # Handle adding new backlog item
    if submit_button and idea_name:
        # Create new backlog item
        new_item = {
            'Idea': idea_name,
            'Category': category,
            'Description': description,
            'Creation Date': pd.Timestamp.now(),
            'Status': status
        }
        
        # Add to backlog
        add_backlog_item(new_item)
        st.success(f"Added '{idea_name}' to backlog!")
        st.rerun()
    
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
                new_task = {
                    'Project': project,
                    'Task': task_name,
                    'Estimated Time': estimated_time,
                    'Due Date': pd.to_datetime(due_date),
                    'Importance': importance,
                    'Complexity': complexity
                }
                
                # Add to tasks
                add_task(new_task)
                
                # Remove from backlog
                delete_backlog_item(idx)
                
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
                        delete_backlog_item(idx)
                        st.success(f"Removed '{item['Idea']}' from backlog.")
                        st.rerun()
    else:
        st.info("Your backlog is empty. Add ideas using the form above.")
