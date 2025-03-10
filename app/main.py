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
    {"id": "F12", "name": "5 Av/53 St", "lines": ["E", "M"]},
    {"id": "F11", "name": "Lexington Av/53 St", "lines": ["E", "M"]}
]

# Maximum number of API call retries
MAX_RETRIES = 3

# Line colors for consistent styling
LINE_COLORS = {
    # Red lines (1,2,3)
    "1": {"bg": "#EE352E", "text": "white"},
    "2": {"bg": "#EE352E", "text": "white"},
    "3": {"bg": "#EE352E", "text": "white"},
    # Green lines (4,5,6)
    "4": {"bg": "#00933C", "text": "white"},
    "5": {"bg": "#00933C", "text": "white"},
    "6": {"bg": "#00933C", "text": "white"},
    "6X": {"bg": "#00933C", "text": "white"},
    # Purple lines (7)
    "7": {"bg": "#B933AD", "text": "white"},
    "7X": {"bg": "#B933AD", "text": "white"},
    # Blue lines (A,C,E)
    "A": {"bg": "#0039A6", "text": "white"},
    "C": {"bg": "#0039A6", "text": "white"},
    "E": {"bg": "#0039A6", "text": "white"},
    # Orange lines (B,D,F,M)
    "B": {"bg": "#FF6319", "text": "white"},
    "D": {"bg": "#FF6319", "text": "white"},
    "F": {"bg": "#FF6319", "text": "white"},
    "M": {"bg": "#FF6319", "text": "white"},
    # Light Green lines (G)
    "G": {"bg": "#6CBE45", "text": "white"},
    # Brown lines (J,Z)
    "J": {"bg": "#996633", "text": "white"},
    "Z": {"bg": "#996633", "text": "white"},
    # Yellow lines (N,Q,R,W)
    "N": {"bg": "#FCCC0A", "text": "black"},
    "Q": {"bg": "#FCCC0A", "text": "black"},
    "R": {"bg": "#FCCC0A", "text": "black"},
    "W": {"bg": "#FCCC0A", "text": "black"},
    # Grey lines (L,S)
    "L": {"bg": "#A7A9AC", "text": "white"},
    "S": {"bg": "#808183", "text": "white"},
    # Default
    "default": {"bg": "#999999", "text": "white"}
}

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
    
    # Add some additional CSS tweaks without creating colored bars
    st.markdown("""
    <style>
    /* Make the dashboard more modern without colored backgrounds */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Subtle card styling without background color */
    .custom-card {
        border-radius: 8px;
        padding: 15px;
        border: 1px solid rgba(49, 51, 63, 0.1);
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    /* Train line badge */
    .train-badge {
        display: inline-block;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        text-align: center;
        line-height: 28px;
        font-weight: bold;
        font-size: 14px;
        margin-right: 5px;
    }
    
    /* Status badge for trains */
    .status-badge {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .status-normal {
        background-color: #28a745;
        color: white;
    }
    
    .status-delay {
        background-color: #ffc107;
        color: black;
    }
    
    .status-alert {
        background-color: #dc3545;
        color: white;
    }
    
    /* No trains running message */
    .no-trains {
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #ffc107;
        margin-bottom: 10px;
        font-size: 14px;
    }
    
    /* Remove extra padding */
    .css-k1vhr4 {
        padding: 5px;
    }
    
    /* Make metrics more compact */
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    
    div[data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
    }
    
    /* Ensure text is legible */
    .train-info {
        margin-bottom: 8px;
        padding: 8px;
        border-radius: 4px;
        border: 1px solid rgba(49, 51, 63, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)
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
        
        # Current time with improved styling
        now = datetime.now(pytz.timezone('America/New_York'))
        st.markdown(f"<h3 style='margin-bottom:0; font-size:1.2em;'>{now.strftime('%A, %B %d, %Y')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:1.5em; margin-top:0;'>{now.strftime('%I:%M %p')}</p>", unsafe_allow_html=True)
        
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
        
        # Use a button with an icon for better visibility
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        st.divider()
        st.caption("© 2025 NYC Local Dashboard")
    
    return page

# --------------- TRAIN ARRIVALS DISPLAY ---------------
def display_train_arrivals(station_info, mta_client, num_trains=2):
    """Display train arrivals for a single station in both directions."""
    station_id = station_info["id"]
    station_name = station_info["name"]
    station_lines = station_info["lines"]  # Now can handle multiple lines
    
    # Display station name with line badges directly using Streamlit components
    st.subheader(station_name)
    
    # Create a compact horizontal layout for train line badges using Streamlit columns
    # Determine the width of each column based on number of lines
    col_width = min(1, 3/len(station_lines))  # Ensure badges are grouped together
    badge_cols = st.columns([col_width] * len(station_lines))
    
    for i, line in enumerate(station_lines):
        style = get_line_style(line)
        with badge_cols[i]:
            # Use a simple colored button to represent train line
            st.markdown(
                f'<div style="background-color:{style["bg"]}; color:{style["text"]}; '
                f'width:28px; height:28px; border-radius:50%; display:flex; align-items:center; '
                f'justify-content:center; font-weight:bold;">{line}</div>',
                unsafe_allow_html=True
            )
    
    # Use a single level of columns for the directions
    cols = st.columns(2)
    
    # Display northbound trains
    with cols[0]:
        st.markdown("**🔼 Northbound**")
        display_direction_trains(station_id, station_lines, "N", mta_client, num_trains)
    
    # Display southbound trains
    with cols[1]:
        st.markdown("**🔽 Southbound**")
        display_direction_trains(station_id, station_lines, "S", mta_client, num_trains)

def get_line_style(route_id):
    """Get the style for a subway line based on its ID."""
    if route_id in LINE_COLORS:
        return LINE_COLORS[route_id]
    return LINE_COLORS["default"]

def display_direction_trains(station_id, lines, direction, mta_client, limit=2):
    """Display trains for a specific direction with support for multiple lines."""
    with st.spinner("Loading..."):
        all_trains = pd.DataFrame()  # Empty dataframe to collect trains from all lines
        error_lines = []  # Keep track of which lines had errors
        
        # Fetch trains for each line at this station
        for line in lines:
            try:
                # No special handling for express trains - query normally
                trains = mta_client.get_upcoming_trains(line, station_id, direction, limit=limit)
                
                if not trains.empty:
                    all_trains = pd.concat([all_trains, trains])
            except Exception as e:
                error_lines.append(line)
                print(f"Could not fetch {line} train data: {e}")  # Use print instead of st.warning
        
        # Sort all collected trains by arrival time
        if not all_trains.empty:
            all_trains = all_trains.sort_values('arrival_time').reset_index(drop=True)
            
            # Only show the earliest trains up to the limit
            if len(all_trains) > limit:
                all_trains = all_trains.head(limit)
                
            now = datetime.now(pytz.timezone('America/New_York'))
            
            for _, train in all_trains.iterrows():
                mins = int((train['arrival_time'] - now).total_seconds() / 60)
                
                # Get style for this line
                style = get_line_style(train['route_id'])
                
                # Create train info display using Streamlit components instead of raw HTML
                arrival_text = "Arriving now" if mins <= 0 else f"{mins} min"
                arrival_time = train['arrival_time'].strftime('%I:%M %p')
                
                # Use columns for layout, but make them tighter with less space
                # Use a 1:5 ratio to keep badge compact
                train_cols = st.columns([1, 5])
                
                with train_cols[0]:
                    # Create badge using st.markdown but with minimal HTML
                    st.markdown(
                        f'<div style="background-color:{style["bg"]}; color:{style["text"]}; '
                        f'width:28px; height:28px; border-radius:50%; display:flex; align-items:center; '
                        f'justify-content:center; font-weight:bold; margin-top:4px;">{train["route_id"]}</div>',
                        unsafe_allow_html=True
                    )
                
                with train_cols[1]:
                    # Use more compact text display
                    st.markdown(f"**{arrival_text}** ({arrival_time})")
                    
        else:
            # Show a friendly message for no trains instead of just "No upcoming trains found"
            service_status = check_line_service_status(lines)
            
            # If we had errors for all lines, show a different message
            if len(error_lines) == len(lines):
                service_status = {"status": "error", "message": f"Could not fetch train data for {', '.join(error_lines)}"}
                
            display_no_trains_message(lines, service_status)

# Add info about MTA API limitations for express trains
def check_line_service_status(lines):
    """
    Check if there are known service issues for these lines.
    In a real app, this would connect to MTA service status API.
    For now we'll return placeholder statuses.
    """
    # This is a placeholder - in production, you would want to fetch real service statuses
    # from the MTA's service status API
    
    # For demonstration, we'll return some mock statuses
    # In reality, this would parse the MTA's service status feed
    
    current_time = datetime.now(pytz.timezone('America/New_York'))
    is_weekend = current_time.weekday() >= 5  # 5=Saturday, 6=Sunday
    is_late_night = current_time.hour < 6 or current_time.hour >= 23
    
    status = "normal"
    message = ""
    
    # Check for express trains specifically (like 6X)
    express_lines = [line for line in lines if 'X' in line]
    if express_lines and is_weekend:
        status = "weekend_express"
        message = "Express trains typically don't run on weekends"
    elif is_late_night:
        status = "limited"
        message = "Late night service - trains run less frequently"
    elif is_weekend:
        status = "weekend"
        message = "Weekend schedule in effect"
    
    return {
        "status": status,
        "message": message
    }

def display_no_trains_message(lines, service_status):
    """Display a helpful message when no trains are found."""
    lines_str = ", ".join(lines)
    
    if service_status["status"] == "normal":
        st.info(f"No upcoming {lines_str} trains found. There may be a temporary service gap.")
    elif service_status["status"] == "weekend":
        st.info(f"Weekend Service: {lines_str} trains may be running on a modified schedule. Check MTA website for service changes.")
    elif service_status["status"] == "weekend_express":
        st.info(f"{service_status['message']}. Regular trains may still be available.")
    elif service_status["status"] == "limited":
        st.info(f"Limited Service: {service_status['message']}")
    elif service_status["status"] == "error":
        st.warning(f"Data Error: {service_status['message']}")
    else:
        st.caption("No upcoming trains found")

# --------------- DASHBOARD PAGE ---------------
@timed
def show_dashboard():
    st.title("NYC Local Dashboard")
    
    # Initialize clients
    weather_client = get_weather_client(st.session_state.zip_code)
    mta_client = get_mta_client()
    
    # First row: Weather (current and 3-hour forecast)
    st.subheader("Weather")
    
    # Create a more horizontal layout for weather information
    weather_cols = st.columns([2, 3])
    
    with weather_cols[0]:
        # Current weather in a compact format
        with st.container():
            with st.spinner("Loading weather data..."):
                current = weather_client.fetch_current_weather()
                if current:
                    location = current["location"]["name"]
                    region = current["location"]["region"]
                    
                    st.write(f"**{location}, {region}**")
                    
                    temp_c = current["current"]["temp_c"]
                    temp_f = current["current"]["temp_f"]
                    condition = current["current"]["condition"]["text"]
                    
                    # Compact temperature display
                    temp_cols = st.columns([1, 2])
                    with temp_cols[0]:
                        st.metric("Temperature", f"{temp_c}°C")
                    with temp_cols[1]:
                        st.write(f"**{condition}**")
                    
                    # Metrics in a single row
                    metric_cols = st.columns(3)
                    with metric_cols[0]:
                        st.metric("Wind", f"{current['current']['wind_kph']} km/h")
                    with metric_cols[1]:
                        st.metric("Humidity", f"{current['current']['humidity']}%")
                    with metric_cols[2]:
                        st.metric("UV", f"{current['current']['uv']}")
                    
                    st.caption(f"Last updated: {current['current']['last_updated']}")
                else:
                    st.error("Weather data unavailable")
    
    with weather_cols[1]:
        # Next 3 hours forecast horizontally
        st.write("**Next 3 Hours**")
        with st.spinner("Loading forecast..."):
            forecast = weather_client.fetch_forecast_weather(days=1)
            if forecast and "forecast" in forecast:
                now = datetime.now(pytz.timezone('America/New_York'))
                current_hour = now.hour
                
                # Get hourly data
                hours = []
                for day in forecast["forecast"]["forecastday"]:
                    for hour in day["hour"]:
                        hour_time = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
                        if (day == forecast["forecast"]["forecastday"][0] and hour_time.hour >= current_hour) or \
                           (day != forecast["forecast"]["forecastday"][0]):
                            hours.append(hour)
                
                # Display next 3 hours in a horizontal format
                hour_cols = st.columns(3)
                for i in range(3):
                    if i < len(hours):
                        hour = hours[i]
                        hour_time = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
                        
                        with hour_cols[i]:
                            # Simple hour display
                            st.write(f"**{hour_time.strftime('%I %p')}**")
                            st.write(f"{hour['temp_c']}°C")
                            rain_chance = int(hour['chance_of_rain'])
                            if rain_chance > 0:
                                st.write(f"🌧️ {rain_chance}%")
                            else:
                                st.write("☀️")
            else:
                st.error("Forecast data unavailable")
    
    # Second row: Closest Train Stations (no white bar)
    st.divider()
    st.subheader("Closest Train Stations")
    
    # Create containers for the default stations directly - no outer container with white space
    for station in st.session_state.default_stations:
        # Display station information without extra wrapping div
        display_train_arrivals(station, mta_client)
        st.divider()  # Add divider between stations
    
    # Auto-refresh toggle at the bottom of the dashboard with improved styling
    st.divider()
    
    refresh_cols = st.columns([3, 1])
    with refresh_cols[0]:
        auto_refresh = st.checkbox(
            "Auto-refresh data every minute",
            value=st.session_state.get("autorefresh_enabled", False)
        )
        
        # Update session state if the checkbox value has changed
        if auto_refresh != st.session_state.get("autorefresh_enabled", False):
            st.session_state.autorefresh_enabled = auto_refresh
            st.rerun()  # Rerun to apply the auto-refresh setting
    
    # Show the last update time with a better visual style
    with refresh_cols[1]:
        now = datetime.now(pytz.timezone('America/New_York'))
        st.markdown(f"""
        <div style="text-align:right; opacity:0.7;">
            Last updated:<br>{now.strftime('%I:%M:%S %p')}
        </div>
        """, unsafe_allow_html=True)

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
        
        st.header(f"{location}, {region}")
        
        current_data = current["current"]
        
        # Main current weather display with standard Streamlit components
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Temperature and condition with standard components
            temp_c = current_data["temp_c"]
            temp_f = current_data["temp_f"]
            feels_like = current_data["feelslike_c"]
            condition = current_data["condition"]["text"]
            
            st.metric(
                "Temperature", 
                f"{temp_c}°C / {temp_f}°F", 
                f"Feels like: {feels_like}°C"
            )
            
            st.write(f"**{condition}**")
            st.caption(f"Last updated: {current_data['last_updated']}")
        
        with col2:
            # Wind and pressure with standard metrics
            st.metric("Wind", f"{current_data['wind_kph']} km/h {current_data['wind_dir']}")
            st.metric("Pressure", f"{current_data['pressure_mb']} mb")
            st.metric("Humidity", f"{current_data['humidity']}%")
        
        with col3:
            # Visibility and UV with standard metrics
            st.metric("Visibility", f"{current_data['vis_km']} km")
            st.metric("UV Index", current_data['uv'])
            st.metric("Cloud Cover", f"{current_data['cloud']}%")
        
        # Air Quality section (if available)
        if "air_quality" in current_data:
            st.divider()
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
            st.divider()
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
        
        # Air Quality section (if available) with improved styling
        if "air_quality" in current_data:
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
            st.subheader("Air Quality")
            
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            
            aq = current_data["air_quality"]
            
            # AQI metrics with better styling
            aqi_cols = st.columns(3)
            
            with aqi_cols[0]:
                if "us-epa-index" in aq:
                    epa_index = aq["us-epa-index"]
                    epa_desc = weather.get_epa_description(epa_index)
                    
                    # Color-code the AQI based on the index
                    aqi_colors = {
                        1: "#00e400",  # Good - Green
                        2: "#ffff00",  # Moderate - Yellow
                        3: "#ff7e00",  # Unhealthy for Sensitive Groups - Orange
                        4: "#ff0000",  # Unhealthy - Red
                        5: "#99004c",  # Very Unhealthy - Purple
                        6: "#7e0023"   # Hazardous - Maroon
                    }
                    
                    aqi_color = aqi_colors.get(epa_index, "#777777")
                    aqi_text_color = "black" if epa_index <= 2 else "white"
                    
                    st.markdown(f"""
                    <div style="text-align:center;">
                        <div style="background-color:{aqi_color}; color:{aqi_text_color}; 
                                    padding:10px; border-radius:5px; font-weight:bold;">
                            US EPA Index: {epa_index}
                        </div>
                        <div style="margin-top:5px;">{epa_desc}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with aqi_cols[1]:
                if "pm2_5" in aq:
                    st.metric("PM2.5", f"{aq['pm2_5']:.1f}")
                
            with aqi_cols[2]:
                if "pm10" in aq:
                    st.metric("PM10", f"{aq['pm10']:.1f}")
                    
            st.markdown('</div>', unsafe_allow_html=True)  # Close custom card
        
        # Daily forecast with improved styling
        if forecast and "forecast" in forecast:
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
            st.header("3-Day Forecast")
            
            forecast_days = forecast["forecast"]["forecastday"]
            
            # Create a more attractive forecast display
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            day_cols = st.columns(len(forecast_days))
            
            for i, day in enumerate(forecast_days):
                date = datetime.strptime(day["date"], "%Y-%m-%d")
                day_data = day["day"]
                
                with day_cols[i]:
                    # Enhanced day forecast card
                    st.markdown(f"""
                    <div style="text-align:center; padding:10px;">
                        <div style="font-size:1.3em; font-weight:bold; margin-bottom:5px;">
                            {date.strftime("%A")}
                        </div>
                        <div style="opacity:0.8; margin-bottom:10px;">
                            {date.strftime("%b %d")}
                        </div>
                        <div style="margin:15px 0;">
                            <img src="https://cdn.weatherapi.com/weather/64x64/day/{day_data['condition']['icon'].split('/')[-1]}" 
                                 alt="{day_data['condition']['text']}" style="margin:auto;">
                        </div>
                        <div style="margin-bottom:5px;">
                            {day_data['condition']['text']}
                        </div>
                        <div style="margin:15px 0;">
                            <span style="font-size:1.4em; font-weight:bold;">{day_data['maxtemp_c']}°</span>
                            <span style="opacity:0.7; margin-left:10px;">{day_data['mintemp_c']}°</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; text-align:left; margin-top:15px;">
                            <div>🌧️ {day_data['daily_chance_of_rain']}%</div>
                            <div>💨 {day_data['maxwind_kph']} km/h</div>
                        </div>
                        <div style="text-align:left; margin-top:5px;">
                            💧 Humidity: {day_data['avghumidity']}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close custom card
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
        search_button = st.button("🔍 Search", use_container_width=True)
    
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
                        st.subheader(station['clean_name'])
                        st.caption(f"Station ID: {station['core_id']}")
                    
                    with cols[1]:
                        if 'lines' in station and station['lines']:
                            # Create a simple text representation of available lines
                            lines_str = ", ".join(station['lines'])
                            st.write(f"Lines: {lines_str}")
                    
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
    
    for i, station in enumerate(st.session_state.default_stations):
        # Create a simple expanded
        with st.expander(f"{station['name']} ({', '.join(station['lines'])})", expanded=(i==0)):
            display_train_arrivals(station, mta, num_trains=4)
    
    # Option to set a station as default
    st.divider()
    st.subheader("Customize Default Stations")
    
    # Input fields for a new default station
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        new_station_id = st.text_input("Station ID", placeholder="e.g. 127", key="new_station_id")
    
    with col2:
        new_station_name = st.text_input("Station Name", placeholder="e.g. Times Square", key="new_station_name")
    
    with col3:
        new_station_line = st.text_input("Primary Line", placeholder="e.g. 1", key="new_station_line")
    
    with col4:
        # Add a secondary line option
        new_station_line2 = st.text_input("Secondary Line", placeholder="e.g. 2", key="new_station_line2")
    
    # Helper text
    st.caption("You can find Station IDs by searching for stations above.")
    
    # Add button with better handling
    if st.button("Add to Default Stations", use_container_width=True):
        if new_station_id and new_station_name and new_station_line:
            # Create a new station entry with support for multiple lines
            lines = [new_station_line]
            if new_station_line2:
                lines.append(new_station_line2)
                
            new_station = {
                "id": new_station_id,
                "name": new_station_name,
                "lines": lines
            }
            
            # Add to session state
            if len(st.session_state.default_stations) < 3:
                st.session_state.default_stations.append(new_station)
                st.success(f"Added {new_station_name} to default stations!")
                st.rerun()
            else:
                # Just replace the last one and inform the user
                st.session_state.default_stations[2] = new_station
                st.success(f"Added {new_station_name}, replacing {st.session_state.default_stations[2]['name']}")
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