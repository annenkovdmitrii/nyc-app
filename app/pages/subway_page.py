import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import time

# Import MTA client
from lib.mta.mta_client import MTAClient

def show():
    """Display detailed subway information page."""
    
    st.title("NYC Subway Information")
    
    # Get user settings from session state
    station_id = st.session_state.station_id
    subway_line = st.session_state.subway_line
    direction = st.session_state.direction
    
    # Initialize MTA client
    mta_client = MTAClient()
    
    # Station search section
    st.header("Find a Station")
    
    search_cols = st.columns([3, 1])
    
    with search_cols[0]:
        search_term = st.text_input("Search by station name", placeholder="e.g. Times Square, Grand Central")
    
    with search_cols[1]:
        search_button = st.button("Search", use_container_width=True)
    
    # Station search results
    if search_term and search_button:
        with st.spinner("Searching for stations..."):
            stations = mta_client.find_stations_by_name(search_term)
        
        if not stations.empty:
            st.success(f"Found {len(stations)} stations matching '{search_term}'")
            
            # Format the dataframe for display
            display_df = stations.copy()
            
            # Rename columns for better readability
            display_df = display_df.rename(columns={
                'core_id': 'Station ID',
                'clean_name': 'Station Name',
                'direction': 'Platform Direction'
            })
            
            # Select columns to display
            if 'stop_lat' in display_df.columns and 'stop_lon' in display_df.columns:
                display_df = display_df[['Station ID', 'Station Name', 'Platform Direction', 'stop_lat', 'stop_lon']]
            else:
                display_df = display_df[['Station ID', 'Station Name', 'Platform Direction']]
            
            # Display the station results
            st.dataframe(display_df, use_container_width=True)
            
            # Option to select a station from results
            selected_ids = display_df['Station ID'].unique().tolist()
            if selected_ids:
                select_cols = st.columns([2, 1, 1])
                
                with select_cols[0]:
                    selected_station = st.selectbox(
                        "Select a station",
                        selected_ids,
                        format_func=lambda x: f"{x} - {display_df[display_df['Station ID'] == x]['Station Name'].iloc[0]}"
                    )
                
                with select_cols[1]:
                    selected_direction = st.radio(
                        "Direction",
                        ["Northbound", "Southbound"],
                        index=0 if direction == "N" else 1
                    )
                
                with select_cols[2]:
                    if st.button("Set Station", use_container_width=True):
                        # Update session state
                        st.session_state.station_id = selected_station
                        st.session_state.direction = "N" if selected_direction == "Northbound" else "S"
                        
                        # Refresh the page
                        st.success(f"Station set to {selected_station}")
                        time.sleep(1)
                        st.experimental_rerun()
        else:
            st.warning(f"No stations found matching '{search_term}'")
            st.info("Try a different search term or check spelling")
    
    # Divider
    st.divider()
    
    # Current station section
    st.header("Current Station Information")
    
    # Get station info
    try:
        stations = mta_client.find_stations_by_id(station_id)
        
        if not stations.empty:
            station_name = stations.iloc[0]["clean_name"]
            
            # Display station info card
            st.subheader(f"{station_name} ({station_id})")
            
            # If coordinates are available, add a map
            if 'stop_lat' in stations.columns and 'stop_lon' in stations.columns:
                lat = stations.iloc[0]["stop_lat"]
                lon = stations.iloc[0]["stop_lon"]
                
                if lat and lon:
                    st.map(pd.DataFrame({
                        'lat': [lat],
                        'lon': [lon]
                    }))
        else:
            station_name = f"Station {station_id}"
            st.warning(f"No additional information found for station ID {station_id}")
    except Exception as e:
        station_name = f"Station {station_id}"
        st.error(f"Error retrieving station information: {e}")
    
    # Train arrival section
    st.subheader(f"Upcoming {subway_line} Trains")
    st.caption(f"{'Northbound' if direction == 'N' else 'Southbound'} at {station_name}")
    
    # Get train arrivals
    try:
        with st.spinner("Fetching train arrivals..."):
            train_arrivals = mta_client.get_upcoming_trains(
                subway_line,
                station_id,
                direction,
                limit=10
            )
        
        if train_arrivals is not None and not train_arrivals.empty:
            # Add minutes to arrival and format time
            now = datetime.now(pytz.timezone('America/New_York'))
            
            # Create a list for the formatted arrivals
            formatted_arrivals = []
            
            for _, train in train_arrivals.iterrows():
                minutes = int((train['arrival_time'] - now).total_seconds() / 60)
                
                formatted_arrivals.append({
                    'Trip ID': train['trip_id'],
                    'Arrival Time': train['arrival_time'].strftime('%I:%M %p'),
                    'Minutes Away': max(0, minutes),
                    'Status': 'Arriving' if minutes <= 0 else f'{minutes} min'
                })
            
            # Convert to DataFrame for display
            arrivals_df = pd.DataFrame(formatted_arrivals)
            
            # Display as table
            st.table(arrivals_df)
            
            # Time of last update
            st.caption(f"Last updated: {now.strftime('%I:%M:%S %p')}")
        else:
            st.warning(f"No upcoming {subway_line} trains found at this station")
            st.info("Try changing the subway line or direction")
    except Exception as e:
        st.error(f"Error fetching train arrivals: {e}")
        st.info("Check your connection and try again")
    
    # Line information
    st.divider()
    st.subheader("Available Subway Lines")
    
    try:
        lines = mta_client.list_all_lines()
        
        if not lines.empty:
            # Display subway line information
            display_lines = lines.copy()
            
            # Rename columns for better readability
            display_lines = display_lines.rename(columns={
                'route_id': 'Line',
                'route_long_name': 'Description',
                'route_color': 'Color'
            })
            
            # Display as table
            st.dataframe(display_lines, use_container_width=True)
        else:
            st.warning("No subway line information available")
    except Exception as e:
        st.error(f"Error fetching subway line information: {e}")
    
    # Refresh option
    st.divider()
    
    refresh_cols = st.columns([3, 1])
    
    with refresh_cols[1]:
        if st.button("Refresh Data", use_container_width=True):
            st.experimental_rerun()
    
    with refresh_cols[0]:
        auto_refresh = st.checkbox("Auto-refresh every 30 seconds", value=False)
    
    if auto_refresh:
        # Add a countdown timer
        countdown_placeholder = st.empty()
        
        for i in range(30, 0, -1):
            countdown_placeholder.caption(f"Refreshing in {i} seconds...")
            time.sleep(1)
        
        countdown_placeholder.caption("Refreshing now...")
        st.experimental_rerun()