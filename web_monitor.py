#!/usr/bin/env python3
"""
Streamlit Web Interface for Video Compression Monitor
This provides a real-time dashboard showing the processing queue, current file progress,
completed files, and any errors or skipped files.
"""

import streamlit as st
import json
import time
from pathlib import Path
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Video Compression Monitor",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# State directory
STATE_DIR = Path(__file__).parent / 'state'

# State files
QUEUE_FILE = STATE_DIR / 'queue.json'
CURRENT_FILE = STATE_DIR / 'current.json'
COMPLETED_FILE = STATE_DIR / 'completed.json'
ERRORS_FILE = STATE_DIR / 'errors.json'


def load_json(file_path):
    """Load JSON file, return empty list/dict if not exists"""
    try:
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
    return [] if 'queue' in str(file_path) or 'completed' in str(file_path) or 'errors' in str(file_path) else {}


def format_timestamp(iso_timestamp):
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return iso_timestamp


def main():
    # Header
    st.title("🎬 Video Compression Monitor")
    st.markdown("Real-time monitoring of NVEnc H.265 video compression tasks")
    
    # Auto-refresh control in sidebar
    st.sidebar.title("Settings")
    auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
    refresh_rate = st.sidebar.slider("Refresh rate (seconds)", 1, 10, 3)
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.rerun()
    
    # Check if state directory exists
    if not STATE_DIR.exists():
        st.warning("⚠️ State directory not found. Make sure the main script (handbrakevidz.py) is running.")
        st.info(f"Expected state directory: {STATE_DIR}")
        time.sleep(refresh_rate)
        if auto_refresh:
            st.rerun()
        return
    
    # Load all state data
    queue = load_json(QUEUE_FILE)
    current = load_json(CURRENT_FILE)
    completed = load_json(COMPLETED_FILE)
    errors = load_json(ERRORS_FILE)
    
    # Display stats in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Queue", len(queue))
    
    with col2:
        is_processing = bool(current and 'path' in current)
        st.metric("Processing", "Yes" if is_processing else "No")
    
    with col3:
        st.metric("Completed", len(completed))
    
    with col4:
        st.metric("Errors/Skipped", len(errors))
    
    st.markdown("---")
    
    # Current Processing Section
    st.header("🎥 Current Processing")
    if current and 'path' in current:
        file_path = Path(current['path'])
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"📁 {file_path.name}")
            st.text(f"Path: {file_path.parent}")
            st.text(f"Started: {format_timestamp(current.get('started', 'Unknown'))}")
        
        with col2:
            progress = current.get('progress', 0)
            eta = current.get('eta', 'Unknown')
            st.metric("Progress", f"{progress}%")
            st.text(f"ETA: {eta}")
        
        # Progress bar
        st.progress(progress / 100)
    else:
        st.info("No file currently being processed")
    
    st.markdown("---")
    
    # Queue Section
    st.header("📋 Processing Queue")
    if queue:
        st.write(f"**{len(queue)} file(s) waiting to be processed**")
        for idx, item in enumerate(queue, 1):
            file_path = Path(item['path'])
            added_time = format_timestamp(item.get('added', 'Unknown'))
            
            with st.expander(f"{idx}. {file_path.name}"):
                st.text(f"Path: {file_path}")
                st.text(f"Added: {added_time}")
    else:
        st.success("Queue is empty")
    
    st.markdown("---")
    
    # Completed Section
    st.header("✅ Completed Files")
    if completed:
        st.write(f"**{len(completed)} file(s) successfully processed**")
        
        # Show last 10 completed files by default
        show_all_completed = st.checkbox("Show all completed files", value=False)
        display_completed = completed if show_all_completed else completed[-10:]
        
        for idx, item in enumerate(reversed(display_completed), 1):
            input_path = Path(item['input'])
            output_path = Path(item['output'])
            original_size = item.get('original_size_mb', 0)
            compressed_size = item.get('compressed_size_mb', 0)
            compression_ratio = ((original_size - compressed_size) / original_size * 100) if original_size > 0 else 0
            completed_time = format_timestamp(item.get('completed', 'Unknown'))
            
            with st.expander(f"{idx}. {input_path.name} → {output_path.name}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text(f"Input: {input_path}")
                    st.text(f"Original Size: {original_size:.2f} MB")
                
                with col2:
                    st.text(f"Output: {output_path}")
                    st.text(f"Compressed Size: {compressed_size:.2f} MB")
                
                st.text(f"Compression Ratio: {compression_ratio:.1f}% reduction")
                st.text(f"Completed: {completed_time}")
    else:
        st.info("No files completed yet")
    
    st.markdown("---")
    
    # Errors/Skipped Section
    st.header("⚠️ Errors & Skipped Files")
    if errors:
        st.write(f"**{len(errors)} error(s) or skipped file(s)**")
        
        # Show last 10 errors by default
        show_all_errors = st.checkbox("Show all errors", value=False)
        display_errors = errors if show_all_errors else errors[-10:]
        
        for idx, item in enumerate(reversed(display_errors), 1):
            file_path = item['path']
            reason = item.get('reason', 'Unknown')
            timestamp = format_timestamp(item.get('timestamp', 'Unknown'))
            
            with st.expander(f"{idx}. {Path(file_path).name}", expanded=False):
                st.error(f"**Reason:** {reason}")
                st.text(f"Path: {file_path}")
                st.text(f"Time: {timestamp}")
    else:
        st.success("No errors or skipped files")
    
    # Auto-refresh at the end
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()


if __name__ == "__main__":
    main()
