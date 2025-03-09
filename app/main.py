# Configure the page - MUST BE THE FIRST STREAMLIT COMMAND
import streamlit as st
st.set_page_config(
    page_title="NYC Local Dashboard",
    page_icon="🗽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import standard libraries
from streamlit_autorefresh import st_autorefresh
import os
from datetime import datetime
import pytz
import pandas as pd
import time
from utils import timed

# Import our custom classes
from nyc_weather import NYCWeather
from mta_client import MTAClient

# Global configurations
DEFAULT_STATIONS = [
    {"id": "630", "name": "51 St", "lines": ["6"]},
    {"id": "F12", "name": "5 Av/53 St", "lines": ["E"]},
    {"id": "F11", "name": "Lexington Av/53 St", "lines": ["M"]}
]

# Setup auto-refresh
def setup_auto_refresh():
    # If auto-refresh is enabled, set it up
    if st.session_state.get("autorefresh_enabled", False):
        # Set up auto-refresh - returns the refresh counter
        count = st_autorefresh(
            interval=60 * 1000,  # 60 seconds in milliseconds
            key="datarefresh",
            limit=None  # No limit on refreshes
        )
        return count
    return None

# Try to load CSS - AFTER page config
try:
    if os.path.exists("assets/styles.css"):
        with open("assets/styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception as e:
    st.warning(f"Could not load CSS: {e}")

# Lazy load clients to improve performance
def get_weather_client(zip_code):
    """Get or create a weather client instance."""
    if "weather_client" not in st.session_state:
        st.session_state.weather_client = {}
    
    if zip_code not in st.session_state.weather_client:
        st.session_state.weather_client[zip_code] = NYCWeather(zip_code=zip_code)
    
    return st.session_state.weather_client[zip_code]

def get_mta_client():
    """Get or create an MTA client instance."""
    if "mta_client" not in st.session_state:
        st.session_state.mta_client = MTAClient()
    
    return st.session_state.mta_client

# Initialize session state if not already set
def init_session_state():
    if "zip_code" not in st.session_state:
        st.session_state.zip_code = "10022"
    if "autorefresh_enabled" not in st.session_state:
        st.session_state.autorefresh_enabled = False
    if "default_stations" not in st.session_state:
        st.session_state.default_stations = DEFAULT_STATIONS

# --------------- SIDEBAR NAVIGATION ---------------
def create_sidebar():
    with st.sidebar:
        st.title("NYC Dashboard")
        
        st.divider()
        
        # Try to load image, but don't crash if missing
        try:
            if os.path.exists("assets/nyc_icon.png"):
                st.image("assets/nyc_icon.png", width=100)
            else:
                st.write("🗽 NYC")
        except:
            st.write("🗽 NYC")
        
        # Current time
        now = datetime.now(pytz.timezone('America/New_York'))
        st.write(f"**{now.strftime('%A, %B %d, %Y')}**")
        st.write(f"*{now.strftime('%I:%M %p')}*")
        
        st.divider()
        
        # Navigation
        page = st.radio(
            "Select Page:",
            ["Dashboard", "Weather Details", "Subway Lookup"]
        )
        
        st.divider()
        
        # Settings
        with st.expander("Settings"):
            zip_code = st.text_input(
                "ZIP Code",
                value=st.session_state.get("zip_code", "10022"),
                help="NYC ZIP code for weather data"
            )
            
            if st.button("Save Settings"):
                st.session_state.zip_code = zip_code
                st.success("Settings saved!")
                st.rerun()
        
        if st.button("Refresh Data"):
            st.rerun()
        
        st.divider()
        st.caption("© 2025 NYC Local Dashboard")
    
    return page

# --------------- TRAIN ARRIVALS DISPLAY ---------------
def display_train_arrivals(station_info, mta_client, num_trains=2):
    """Display train arrivals for a single station in both directions."""
    station_id = station_info["id"]
    station_name = station_info["name"]
    default_line = station_info["lines"][0]
    
    st.subheader(f"{station_name}")
    
    # Use a single level of columns for the directions
    cols = st.columns(2)
    
    # Display northbound trains
    with cols[0]:
        st.markdown("**🔼 Northbound**")
        display_direction_trains(station_id, default_line, "N", mta_client, num_trains)
    
    # Display southbound trains
    with cols[1]:
        st.markdown("**🔽 Southbound**")
        display_direction_trains(station_id, default_line, "S", mta_client, num_trains)

def display_direction_trains(station_id, line, direction, mta_client, limit=2):
    """Display trains for a specific direction."""
    with st.spinner("Loading..."):
        trains = mta_client.get_upcoming_trains(line, station_id, direction, limit=limit)
        
        if not trains.empty:
            now = datetime.now(pytz.timezone('America/New_York'))
            
            for _, train in trains.iterrows():
                mins = int((train['arrival_time'] - now).total_seconds() / 60)
                
                # Get the right color for the line
                if train['route_id'] in "123":
                    line_color = "#EE352E"  # Red
                elif train['route_id'] in "456":
                    line_color = "#00933C"  # Green
                elif train['route_id'] in "7":
                    line_color = "#B933AD"  # Purple
                elif train['route_id'] in "ACE":
                    line_color = "#0039A6"  # Blue
                elif train['route_id'] in "BDFM":
                    line_color = "#FF6319"  # Orange
                elif train['route_id'] in "G":
                    line_color = "#6CBE45"  # Light Green
                elif train['route_id'] in "JZ":
                    line_color = "#996633"  # Brown
                elif train['route_id'] in "NQRW":
                    line_color = "#FCCC0A"  # Yellow with dark text
                elif train['route_id'] in "L":
                    line_color = "#A7A9AC"  # Grey
                else:
                    line_color = "#999999"  # Default grey
                
                text_color = "white"
                if train['route_id'] in "NQRW":  # Yellow lines need dark text
                    text_color = "black"
                
                # Instead of using columns inside columns, create a single row with the train info
                arrival_text = "Arriving now" if mins <= 0 else f"{mins} min"
                train_html = f"""
                <div style="display:flex;align-items:center;margin-bottom:8px;">
                    <div style="width:30px;height:30px;border-radius:50%;background-color:{line_color};
                    color:{text_color};display:flex;align-items:center;justify-content:center;font-weight:bold;margin-right:10px;">
                    {train['route_id']}
                    </div>
                    <div>
                        <strong>{arrival_text}</strong> ({train['arrival_time'].strftime('%I:%M %p')})
                    </div>
                </div>
                """
                st.markdown(train_html, unsafe_allow_html=True)
        else:
            st.caption("No upcoming trains found")

# --------------- DASHBOARD PAGE ---------------
@timed
def show_dashboard():
    st.title("NYC Local Dashboard")
    
    # Initialize clients
    weather_client = get_weather_client(st.session_state.zip_code)
    mta_client = get_mta_client()
    
    # Weather section
    weather_col, stations_col = st.columns([1, 2])
    
    with weather_col:
        st.subheader("Weather")
        with st.spinner("Loading weather data..."):
            current = weather_client.fetch_current_weather()
            if current:
                location = current["location"]["name"]
                region = current["location"]["region"]
                
                st.subheader(f"{location}, {region}")
                
                temp = current["current"]["temp_c"]
                condition = current["current"]["condition"]["text"]
                
                st.metric("Temperature", f"{temp}°C / {current['current']['temp_f']}°F")
                st.write(f"**{condition}**")
                
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Wind", f"{current['current']['wind_kph']} km/h")
                with cols[1]:
                    st.metric("Humidity", f"{current['current']['humidity']}%")
                with cols[2]:
                    st.metric("UV Index", current['current']['uv'])
                
                st.caption(f"Last updated: {current['current']['last_updated']}")
            else:
                st.error("Weather data unavailable")
                
        # Next few hours forecast
        st.subheader("Next 3 Hours")
        with st.spinner("Loading forecast..."):
            forecast = weather_client.fetch_forecast_weather(days=1)
            if forecast and "forecast" in forecast:
                now = datetime.now()
                current_hour = now.hour
                
                # Get hourly data
                hours = []
                for day in forecast["forecast"]["forecastday"]:
                    for hour in day["hour"]:
                        hour_time = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
                        if (day == forecast["forecast"]["forecastday"][0] and hour_time.hour >= current_hour) or \
                           (day != forecast["forecast"]["forecastday"][0]):
                            hours.append(hour)
                
                # Display next 3 hours in a compact format
                hour_cols = st.columns(3)
                for i in range(3):
                    if i < len(hours):
                        hour = hours[i]
                        hour_time = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
                        
                        with hour_cols[i]:
                            st.write(f"**{hour_time.strftime('%I %p')}**")
                            st.write(f"{hour['temp_c']}°C")
                            if int(hour['chance_of_rain']) > 0:
                                st.write(f"🌧️ {hour['chance_of_rain']}%")
            else:
                st.error("Forecast data unavailable")
    
    with stations_col:
        st.subheader("Closest Train Stations")
        
        # Create 3 containers for the 3 default stations
        for station in st.session_state.default_stations:
            with st.container():
                display_train_arrivals(station, mta_client)
                st.divider()
    
    # Auto-refresh toggle at the bottom of the dashboard
    st.divider()
    auto_refresh = st.checkbox(
        "Auto-refresh data every minute",
        value=st.session_state.get("autorefresh_enabled", False)
    )
    
    # Update session state if the checkbox value has changed
    if auto_refresh != st.session_state.get("autorefresh_enabled", False):
        st.session_state.autorefresh_enabled = auto_refresh
        st.rerun()  # Rerun to apply the auto-refresh setting
    
    # Show the last update time
    now = datetime.now()
    st.caption(f"Last updated: {now.strftime('%I:%M:%S %p')}")

# --------------- WEATHER DETAILS PAGE ---------------
@timed
def show_weather_details():
    st.title("NYC Weather Details")
    
    # Get settings
    zip_code = st.session_state.zip_code
    
    # Initialize weather client
    weather = get_weather_client(zip_code)
    
    # Fetch data
    with st.spinner("Fetching detailed weather..."):
        current = weather.fetch_current_weather()
        forecast = weather.fetch_forecast_weather(days=3)
    
    if current:
        location = current["location"]["name"]
        region = current["location"]["region"]
        
        st.header(f"Current Weather in {location}, {region}")
        
        current_data = current["current"]
        
        # Main current weather display
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Temperature and condition
            temp = current_data["temp_c"]
            condition = current_data["condition"]["text"]
            
            st.metric(
                "Temperature", 
                f"{temp}°C / {current_data['temp_f']}°F", 
                f"Feels like: {current_data['feelslike_c']}°C"
            )
            
            st.markdown(f"### {condition}")
            st.caption(f"Last updated: {current_data['last_updated']}")
        
        with col2:
            # Wind and pressure
            st.metric("Wind", f"{current_data['wind_kph']} km/h {current_data['wind_dir']}")
            st.metric("Pressure", f"{current_data['pressure_mb']} mb")
            st.metric("Humidity", f"{current_data['humidity']}%")
        
        with col3:
            # Visibility and UV
            st.metric("Visibility", f"{current_data['vis_km']} km")
            st.metric("UV Index", current_data['uv'])
            st.metric("Cloud Cover", f"{current_data['cloud']}%")
        
        # Air Quality section (if available)
        if "air_quality" in current_data:
            st.subheader("Air Quality")
            
            aq = current_data["air_quality"]
            
            # AQI metrics
            aqi_cols = st.columns(3)
            
            with aqi_cols[0]:
                if "us-epa-index" in aq:
                    epa_index = aq["us-epa-index"]
                    epa_desc = weather.get_epa_description(epa_index)
                    st.metric("US EPA Index", f"{epa_index} - {epa_desc}")
            
            with aqi_cols[1]:
                if "pm2_5" in aq:
                    st.metric("PM2.5", f"{aq['pm2_5']:.1f}")
                
            with aqi_cols[2]:
                if "pm10" in aq:
                    st.metric("PM10", f"{aq['pm10']:.1f}")
        
        # Daily forecast
        if forecast and "forecast" in forecast:
            st.header("3-Day Forecast")
            
            forecast_days = forecast["forecast"]["forecastday"]
            day_cols = st.columns(len(forecast_days))
            
            for i, day in enumerate(forecast_days):
                date = datetime.strptime(day["date"], "%Y-%m-%d")
                day_data = day["day"]
                
                with day_cols[i]:
                    st.subheader(date.strftime("%A, %b %d"))
                    st.write(f"**{day_data['condition']['text']}**")
                    
                    # Temperature range
                    st.metric(
                        "High", 
                        f"{day_data['maxtemp_c']}°C", 
                    )
                    st.metric(
                        "Low", 
                        f"{day_data['mintemp_c']}°C",
                    )
                    
                    st.write(f"Rain: {day_data['daily_chance_of_rain']}%")
                    st.write(f"Wind: {day_data['maxwind_kph']} km/h")
                    st.write(f"Humidity: {day_data['avghumidity']}%")
    else:
        st.error("Weather data unavailable. Please check your API key and connection.")

# --------------- SUBWAY LOOKUP PAGE ---------------
@timed
def show_subway_lookup():
    st.title("NYC Subway Lookup")
    
    # Initialize MTA client
    mta = get_mta_client()
    
    # Station search section
    st.header("Find a Station")
    
    search_cols = st.columns([3, 1])
    
    with search_cols[0]:
        search_term = st.text_input("Station name", placeholder="e.g. Times Square, Grand Central")
    
    with search_cols[1]:
        search_button = st.button("Search", use_container_width=True)
    
    # Search results
    if search_term and search_button:
        with st.spinner("Searching for stations..."):
            stations = mta.find_stations_by_name(search_term)
        
        if not stations.empty:
            st.success(f"Found {len(stations)} stations matching '{search_term}'")
            
            # Group by core_id to avoid duplicates
            grouped = stations.groupby('core_id').first().reset_index()
            
            for _, station in grouped.iterrows():
                with st.container():
                    cols = st.columns([3, 2])
                    
                    with cols[0]:
                        st.write(f"**{station['clean_name']}** (ID: {station['core_id']})")
                    
                    with cols[1]:
                        if 'lines' in station and station['lines']:
                            st.write("Lines: " + ", ".join(station['lines']))
                    
                    # Display the trains for this station
                    if st.button(f"Show trains at {station['clean_name']}", key=f"station_{station['core_id']}"):
                        # Create a station info dictionary
                        station_info = {
                            "id": station['core_id'],
                            "name": station['clean_name'],
                            "lines": station['lines'] if 'lines' in station and station['lines'] else ["1"]
                        }
                        
                        # Display train arrivals for this station
                        display_train_arrivals(station_info, mta, num_trains=4)
                
                st.divider()
        else:
            st.warning(f"No stations found matching '{search_term}'")
    
    # Display default stations
    st.header("Default Stations")
    
    for station in st.session_state.default_stations:
        with st.expander(f"{station['name']} ({', '.join(station['lines'])})"):
            display_train_arrivals(station, mta, num_trains=4)
    
    # Option to set a station as default
    st.divider()
    st.subheader("Customize Default Stations")
    
    # Input fields for a new default station
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        new_station_id = st.text_input("Station ID", placeholder="e.g. 127")
    
    with col2:
        new_station_name = st.text_input("Station Name", placeholder="e.g. Times Square")
    
    with col3:
        new_station_line = st.text_input("Primary Line", placeholder="e.g. 1")
    
    with col4:
        if st.button("Add to Defaults"):
            if new_station_id and new_station_name and new_station_line:
                # Create a new station entry
                new_station = {
                    "id": new_station_id,
                    "name": new_station_name,
                    "lines": [new_station_line]
                }
                
                # Add to session state
                if len(st.session_state.default_stations) < 3:
                    st.session_state.default_stations.append(new_station)
                else:
                    # Replace the last one
                    st.session_state.default_stations[2] = new_station
                
                st.success(f"Added {new_station_name} to default stations!")
                st.rerun()

# --------------- MAIN APP ---------------
# Initialize session state
init_session_state()

# Setup auto-refresh
refresh_count = setup_auto_refresh()

# Create sidebar and get selected page
selected_page = create_sidebar()

# Display the selected page
if selected_page == "Dashboard":
    show_dashboard()
elif selected_page == "Weather Details":
    show_weather_details()
elif selected_page == "Subway Lookup":
    show_subway_lookup()