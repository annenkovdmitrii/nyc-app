import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

def display_trains_card(train_data, line, station_name, direction, limit=5):
    """
    Display subway train arrivals in a card format.
    
    Args:
        train_data: DataFrame with train arrival data
        line: Subway line (e.g., '1', 'A')
        station_name: Name of the station
        direction: Direction ('N' for northbound, 'S' for southbound)
        limit: Maximum number of trains to display
    """
    # Create container
    with st.container():
        # Header with subway line and station
        st.subheader(f"Subway: Line {line} at {station_name}")
        st.caption(f"{'Northbound' if direction == 'N' else 'Southbound'} trains")
        
        if train_data is None or train_data.empty:
            st.warning(f"No upcoming trains found")
            st.info("Try changing the line or direction")
            return
        
        # Current time for calculating minutes to arrival
        now = datetime.now(pytz.timezone('America/New_York'))
        
        # Display upcoming trains
        for i, (_, train) in enumerate(train_data.iterrows()):
            if i >= limit:
                break
            
            # Calculate minutes to arrival
            minutes = int((train['arrival_time'] - now).total_seconds() / 60)
            
            # Create a horizontal layout for each train
            cols = st.columns([1, 2, 1])
            
            with cols[0]:
                # Line indicator - Circle with line number/letter
                line_style = get_line_style(line)
                st.markdown(
                    f"""
                    <div style="
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background-color: {line_style['bg_color']};
                        color: {line_style['text_color']};
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        font-size: 20px;
                        margin: auto;
                    ">
                        {line}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            
            with cols[1]:
                # Time information
                if minutes <= 0:
                    st.markdown("**Arriving now**")
                else:
                    st.markdown(f"**Arrives in {minutes} min**")
                
                # Trip ID (shortened for readability)
                trip_id = train['trip_id']
                short_id = trip_id.split('_')[0] if '_' in trip_id else trip_id[:8]
                st.caption(f"Train: {short_id}")
            
            with cols[2]:
                # Arrival time
                st.markdown(f"**{train['arrival_time'].strftime('%I:%M %p')}**")
            
            # Add a subtle divider between trains
            if i < min(limit, len(train_data) - 1):
                st.markdown("<hr style='margin:0; padding:0; opacity:0.2'>", unsafe_allow_html=True)
        
        # Show last updated time
        st.caption(f"Last updated: {now.strftime('%I:%M:%S %p')}")

def display_station_info(station_data):
    """
    Display station information in a card format.
    
    Args:
        station_data: DataFrame with station information
    """
    if station_data is None or station_data.empty:
        st.warning("No station information available")
        return
    
    # Extract first row for display
    station = station_data.iloc[0]
    
    with st.container():
        st.subheader(f"Station: {station['clean_name'] if 'clean_name' in station else 'Unknown'}")
        
        # Station details
        details = []
        
        if 'stop_id' in station:
            details.append(f"ID: {station['stop_id']}")
        
        if 'direction' in station:
            details.append(f"Platform: {station['direction']}")
        
        if 'stop_lat' in station and 'stop_lon' in station:
            details.append(f"Location: {station['stop_lat']:.4f}, {station['stop_lon']:.4f}")
        
        # Display details
        if details:
            for detail in details:
                st.caption(detail)

def display_lines_available(station_id, mta_client):
    """
    Display available subway lines at a station.
    
    Args:
        station_id: MTA station ID
        mta_client: MTA client instance
    """
    try:
        # This is a simplified approach - in a real app, you'd want to 
        # implement a function that gets all lines serving a station
        common_lines = {
            '127': ['1', '2', '3', 'N', 'Q', 'R', 'W', '7'],  # Times Square
            '631': ['4', '5', '6', '7'],  # Grand Central
            '635': ['4', '5', '6', 'N', 'Q', 'R', 'W', 'L'],  # Union Square
            '101': ['1'],  # 103 St
            # Add more stations as needed
        }
        
        station_key = str(station_id)
        
        if station_key in common_lines:
            lines = common_lines[station_key]
            
            st.caption("Available lines at this station:")
            
            # Display line indicators in a row
            cols = st.columns(len(lines))
            
            for i, line in enumerate(lines):
                with cols[i]:
                    line_style = get_line_style(line)
                    st.markdown(
                        f"""
                        <div style="
                            width: 30px;
                            height: 30px;
                            border-radius: 50%;
                            background-color: {line_style['bg_color']};
                            color: {line_style['text_color']};
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-weight: bold;
                            font-size: 16px;
                            margin: auto;
                        ">
                            {line}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
        else:
            # If we don't have hardcoded data, don't show anything
            pass
    except Exception as e:
        # Silently fail if can't get line info - not critical
        pass

def get_line_style(line):
    """
    Get color styling for subway line.
    
    Args:
        line: Subway line (e.g., '1', 'A')
        
    Returns:
        Dictionary with background and text colors
    """
    # Simple color mapping for NYC subway lines
    line_colors = {
        '1': {'bg_color': '#EE352E', 'text_color': 'white'},  # Red
        '2': {'bg_color': '#EE352E', 'text_color': 'white'},  # Red
        '3': {'bg_color': '#EE352E', 'text_color': 'white'},  # Red
        '4': {'bg_color': '#00933C', 'text_color': 'white'},  # Green
        '5': {'bg_color': '#00933C', 'text_color': 'white'},  # Green
        '6': {'bg_color': '#00933C', 'text_color': 'white'},  # Green
        '7': {'bg_color': '#B933AD', 'text_color': 'white'},  # Purple
        'A': {'bg_color': '#0039A6', 'text_color': 'white'},  # Blue
        'C': {'bg_color': '#0039A6', 'text_color': 'white'},  # Blue
        'E': {'bg_color': '#0039A6', 'text_color': 'white'},  # Blue
        'B': {'bg_color': '#FF6319', 'text_color': 'white'},  # Orange
        'D': {'bg_color': '#FF6319', 'text_color': 'white'},  # Orange
        'F': {'bg_color': '#FF6319', 'text_color': 'white'},  # Orange
        'M': {'bg_color': '#FF6319', 'text_color': 'white'},  # Orange
        'N': {'bg_color': '#FCCC0A', 'text_color': 'black'},  # Yellow
        'Q': {'bg_color': '#FCCC0A', 'text_color': 'black'},  # Yellow
        'R': {'bg_color': '#FCCC0A', 'text_color': 'black'},  # Yellow
        'W': {'bg_color': '#FCCC0A', 'text_color': 'black'},  # Yellow
        'G': {'bg_color': '#6CBE45', 'text_color': 'white'},  # Light Green
        'J': {'bg_color': '#996633', 'text_color': 'white'},  # Brown
        'Z': {'bg_color': '#996633', 'text_color': 'white'},  # Brown
        'L': {'bg_color': '#A7A9AC', 'text_color': 'white'},  # Grey
        'S': {'bg_color': '#808183', 'text_color': 'white'},  # Dark Grey
    }
    
    return line_colors.get(line, {'bg_color': '#333333', 'text_color': 'white'})