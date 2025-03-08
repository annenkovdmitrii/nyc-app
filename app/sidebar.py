import streamlit as st
import os
from datetime import datetime

def create_sidebar():
    """Create and return the sidebar navigation."""
    
    with st.sidebar:
        # Header
        st.title("NYC Dashboard")
        try:
            image_path = "app/assets/nyc_icon.png"
            if os.path.exists(image_path):
                st.image(image_path, width=100)
            else:
                st.info("NYC icon not found")
        except Exception as e:
            st.info(f"Error loading image: {e}")
                
        # Current time
        now = datetime.now()
        st.write(f"**{now.strftime('%A, %B %d, %Y')}**")
        st.write(f"*{now.strftime('%I:%M %p')}*")
        
        st.divider()
        
        # Navigation
        st.subheader("Navigation")
        selected = st.radio(
            "Select a page:",
            ["Dashboard", "Weather", "Subway"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Settings section
        with st.expander("Settings"):
            # Weather settings
            st.subheader("Weather")
            zip_code = st.text_input(
                "ZIP Code", 
                value=os.getenv("WEATHER_ZIP", "10022"),
                help="NYC ZIP code for weather data"
            )
            
            # Subway settings
            st.subheader("Subway")
            station_id = st.text_input(
                "Station ID", 
                value=os.getenv("MTA_DEFAULT_STATION", "127"),
                help="MTA station ID (e.g., 127 for Times Square)"
            )
            
            subway_line = st.selectbox(
                "Subway Line",
                ["1", "2", "3", "4", "5", "6", "7", "A", "C", "E", "B", "D", "F", "M", "N", "Q", "R", "W", "G", "J", "Z", "L"],
                index=0,
                help="Subway line to display"
            )
            
            direction = st.radio(
                "Direction",
                ["Northbound", "Southbound"],
                index=0,
                help="Train direction"
            )
            
            # Store settings in session state
            if st.button("Save Settings"):
                st.session_state.zip_code = zip_code
                st.session_state.station_id = station_id
                st.session_state.subway_line = subway_line
                st.session_state.direction = "N" if direction == "Northbound" else "S"
                st.success("Settings saved!")
        
        # Initialize session state if not already set
        if "zip_code" not in st.session_state:
            st.session_state.zip_code = os.getenv("WEATHER_ZIP", "10022")
        if "station_id" not in st.session_state:
            st.session_state.station_id = os.getenv("MTA_DEFAULT_STATION", "127")
        if "subway_line" not in st.session_state:
            st.session_state.subway_line = os.getenv("MTA_DEFAULT_LINE", "1")
        if "direction" not in st.session_state:
            st.session_state.direction = os.getenv("MTA_DEFAULT_DIRECTION", "N")
            
        # Footer
        st.divider()
        st.caption("© 2025 NYC Local Dashboard")
        
    return selected