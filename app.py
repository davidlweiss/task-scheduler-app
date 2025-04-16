import streamlit as st
from components.task_form import show_task_manager
from components.free_time_form import show_free_time_manager
from components.scheduler import run_scheduler
from components.backlog_form import show_backlog_manager
from components.wizard import run_wizard
from utils.session_state import initialize_session_state

def main():
    """Main entry point for the Task Scheduler application."""
    # Add custom CSS to make containers wider
    st.markdown("""
        <style>
        .main .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)
    
    st.title("Dynamic Task Scheduler V8")
    
    # Initialize session state
    initialize_session_state()
    
    # Check if wizard mode is active
    if st.session_state.wizard_mode:
        run_wizard()
    else:
        # Create tabs for the main app interface
        tab1, tab2, tab3, tab4 = st.tabs(["Manage Tasks", "Manage Free Time", "Run Scheduler", "Idea Backlog"])
        
        with tab1:
            show_task_manager()
        
        with tab2:
            show_free_time_manager()
        
        with tab3:
            run_scheduler()
        
        with tab4:
            show_backlog_manager()

if __name__ == "__main__":
    main()
