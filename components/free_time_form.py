import streamlit as st
import pandas as pd
from datetime import datetime
from models.free_time import (
    load_free_time, save_free_time, 
    add_free_time, subtract_free_time, 
    delete_free_time, get_total_free_time
)

def show_free_time_manager():
    """
    Display and manage free time windows in the Free Time tab.
    """
    st.header("Manage Free Time Windows")
    
    # Initialize session state for the form
    if 'free_time_date' not in st.session_state:
        st.session_state.free_time_date = datetime.today()
    if 'free_time_hours' not in st.session_state:
        st.session_state.free_time_hours = 1.0
    
    # Load free time data
    free_time_df = load_free_time()
    
    # Ensure free_time_df has the right data types
    if 'Date' in free_time_df.columns:
        free_time_df['Date'] = pd.to_datetime(free_time_df['Date'])
    
    # Remove Sort Order column if it exists (legacy cleanup)
    if 'Sort Order' in free_time_df.columns:
        free_time_df = free_time_df.drop('Sort Order', axis=1)
    
    # Form for adding/subtracting free time
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
    
    # Handle form submission
    if submit_button:
        # Convert date to pandas datetime
        pd_date = pd.to_datetime(selected_date)
        
        if operation == "Add":
            success = add_free_time(pd_date, hours)
            if success:
                st.success(f"Added {hours} hours to {selected_date.strftime('%A, %B %d')}")
        else:  # Subtract
            success = subtract_free_time(pd_date, hours)
            if success:
                st.success(f"Subtracted {hours} hours from {selected_date.strftime('%A, %B %d')}")
            else:
                st.warning(f"Cannot subtract hours from {selected_date.strftime('%A, %B %d')} - date doesn't exist yet.")
                
        # Update session state
        st.session_state.free_time_date = selected_date
        st.session_state.free_time_hours = hours
        
        # Reload data after update
        free_time_df = load_free_time()
        
    # Display existing free time windows
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
                    # Get sorted dates
                    sorted_df = free_time_df.sort_values('Date')
                    dates = sorted_df['Date'].tolist()
                    
                    current_date = dates[i]
                    prev_date = dates[i-1]
                    
                    # Store current values
                    current_hours = sorted_df.loc[sorted_df['Date'] == current_date, 'Available Hours'].values[0]
                    prev_hours = sorted_df.loc[sorted_df['Date'] == prev_date, 'Available Hours'].values[0]
                    
                    # Swap dates
                    free_time_df.loc[free_time_df['Date'] == current_date, 'Date'] = prev_date
                    free_time_df.loc[free_time_df['Date'] == prev_date, 'Date'] = current_date
                    
                    # Save changes
                    save_free_time(free_time_df)
                    st.rerun()
                    
            with col4:
                # Delete button
                if st.button("🗑️ Delete", key=f"del_{idx}"):
                    delete_free_time(idx)
                    st.rerun()
        
        # Show a summary
        total_hours = get_total_free_time()
        st.info(f"Total free time available: {total_hours} hours")
    else:
        st.info("No free time windows added yet. Use the form above to add free time.")
