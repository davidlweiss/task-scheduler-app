import streamlit as st
from datetime import datetime

def initialize_session_state():
    """
    Initialize all session state variables used throughout the application.
    Centralizing these initializations makes state management more predictable.
    """
    # Initialize wizard session state
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
    
    # Initialize backlog conversion state
    if 'converting_item' not in st.session_state:
        st.session_state.converting_item = None
    if 'converting_idx' not in st.session_state:
        st.session_state.converting_idx = None
    
    # Initialize task resolution state
    if 'resolving_task' not in st.session_state:
        st.session_state.resolving_task = None
    if 'resolving_option' not in st.session_state:
        st.session_state.resolving_option = None
    
    # Initialize free time management state
    if 'free_time_date' not in st.session_state:
        st.session_state.free_time_date = datetime.today()
    if 'free_time_hours' not in st.session_state:
        st.session_state.free_time_hours = 1.0
    
    # Scheduler state
    if 'rerun_scheduler' not in st.session_state:
        st.session_state.rerun_scheduler = False
    if 'action_results' not in st.session_state:
        st.session_state.action_results = []

def clear_wizard_state():
    """
    Clear all state related to the wizard.
    """
    st.session_state.wizard_mode = False
    st.session_state.wizard_step = 1
    st.session_state.wizard_task_idx = None
    st.session_state.wizard_task = None
    st.session_state.wizard_approach = None

def clear_conversion_state():
    """
    Clear state related to backlog item conversion.
    """
    st.session_state.converting_item = None
    st.session_state.converting_idx = None

def clear_resolution_state():
    """
    Clear state related to task resolution.
    """
    st.session_state.resolving_task = None
    st.session_state.resolving_option = None

def set_wizard_mode(mode=True):
    """
    Set the wizard mode state.
    """
    st.session_state.wizard_mode = mode
    if not mode:
        clear_wizard_state()
