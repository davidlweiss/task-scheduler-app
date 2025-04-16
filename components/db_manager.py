import streamlit as st
import pandas as pd
import sqlite3
import io
import os
import zipfile
import base64
from datetime import datetime
from utils.db_utils import DB_FILE, table_to_df, df_to_table

def show_db_manager():
    """
    Show database management options for backing up and restoring data.
    """
    st.header("Database Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Backup Database")
        if st.button("📤 Download Database Backup"):
            # Generate backup file name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"task_scheduler_backup_{timestamp}.zip"
            
            # Create the download link
            download_link = create_download_link(backup_name)
            st.markdown(download_link, unsafe_allow_html=True)
            st.success("Click the link above to download your backup.")
    
    with col2:
        st.subheader("Restore Database")
        uploaded_file = st.file_uploader("📥 Upload Backup File", type=["zip"])
        
        if uploaded_file is not None:
            if st.button("Restore from Backup"):
                success = restore_from_backup(uploaded_file)
                if success:
                    st.success("Database restored successfully! Restart the app to see your data.")
                else:
                    st.error("Error restoring database. Please check if the backup file is valid.")

def create_download_link(backup_name):
    """
    Create a database backup and generate a download link.
    
    Args:
        backup_name: Name of the backup file
        
    Returns:
        str: HTML link for downloading the backup
    """
    # Create a zip file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add the database file to the zip if it exists
        if os.path.exists(DB_FILE):
            zip_file.write(DB_FILE, arcname=os.path.basename(DB_FILE))
        
        # Also add CSV exports of each table for easier inspection
        for table in ['tasks', 'free_time', 'backlog']:
            df = table_to_df(table)
            if not df.empty:
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                zip_file.writestr(f"{table}.csv", csv_buffer.getvalue())
    
    # Set up the download link
    b64 = base64.b64encode(zip_buffer.getvalue()).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="{backup_name}">Download {backup_name}</a>'
    
    return href

def restore_from_backup(uploaded_file):
    """
    Restore database from an uploaded backup file.
    
    Args:
        uploaded_file: Uploaded zip file
        
    Returns:
        bool: True if restoration was successful
    """
    try:
        # Create a temporary file to extract the backup
        with zipfile.ZipFile(uploaded_file) as zip_ref:
            # First, check if it contains the database file
            db_filename = os.path.basename(DB_FILE)
            
            if db_filename in zip_ref.namelist():
                # If database file exists, close any open connections
                # This is important because SQLite will lock the file
                conn = sqlite3.connect(DB_FILE)
                conn.close()
                
                # Extract the database file, overwriting the existing one
                zip_ref.extract(db_filename, path=os.path.dirname(DB_FILE))
                return True
            
            # If no database file, try to restore from CSVs
            csv_files = [name for name in zip_ref.namelist() if name.endswith('.csv')]
            
            if csv_files:
                for csv_file in csv_files:
                    table_name = os.path.splitext(csv_file)[0]
                    
                    # Read the CSV into a DataFrame
                    with zip_ref.open(csv_file) as f:
                        df = pd.read_csv(io.BytesIO(f.read()))
                        
                        # Save to the database
                        df_to_table(df, table_name)
                
                return True
        
        return False
    except Exception as e:
        st.error(f"Error during restoration: {str(e)}")
        return False
