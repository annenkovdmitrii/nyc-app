import streamlit as st
import os
from datetime import datetime
import pytz
import pandas as pd
import time

# Import our custom classes
from nyc_weather import NYCWeather
from mta_client import MTAClient

try:
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception as e:
    st.warning(f"Note: Could not load custom CSS file: {e}")

# Configure the page
st.set_page_config(
    page_title="NYC Local Dashboard",
    page_icon="🗽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------- SIDEBAR NAVIGATION ---------------
def create_sidebar():
    with st.sidebar:
        st.title("NYC Dashboard")
        
        # Try to load image, but don't crash if missing
        try:
            if os.path.exists("assets/nyc_icon.png"):
                st.image("assets/nyc_icon.png", width=100)
            else:
                st.write("🗽 NYC")
        except:
            st.write("🗽 NYC")
        
        # Current time
        now = datetime.now()
        st.write(f"**{now.strftime('%A, %B %d, %Y')}**")
        st.write(f"*{now.strftime('%I:%M %p')}*")
        
        st.divider()
        
        # Navigation
        page = st.radio(
            "Select Page:",
            ["Dashboard", "Weather Details", "Subway Lookup"]
        )
        
        st.divider()
        
        # Simple settings
        with st.expander("Settings"):
            zip_code = st.text_input(
                "ZIP Code",
                value=st.session_state.get("zip_code", "10022"),
                help="NYC ZIP code for weather data"
            )
            
            station_id = st.text_input(
                "Station ID",
                value=st.session_state.get("station_id", "127"),
                help="MTA station ID (e.g., 127 for Times Square)"
            )
            
            subway_line = st.selectbox(
                "Subway Line",
                ["1", "2", "3", "4", "5", "6", "7", "A", "C", "E", "B", "D", "F", "M", "N", "Q", "R", "W"],
                index=["1", "2", "3", "4", "5", "6", "7", "A", "C", "E", "B", "D", "F", "M", "N", "Q", "R", "W"].index(
                    st.session_state.get("subway_line", "1")
                ) if st.session_state.get("subway_line", "1") in ["1", "2", "3", "4", "5", "6", "7", "A", "C", "E", "B", "D", "F", "M", "N", "Q", "R", "W"] else 0
            )
            
            direction = st.radio(
                "Direction",
                ["Northbound", "Southbound"],
                index=0 if st.session_state.get("direction", "N") == "N" else 1
            )
            
            if st.button("Save Settings"):
                st.session_state.zip_code = zip_code
                st.session_state.station_id = station_id
                st.session_state.subway_line = subway_line
                st.session_state.direction = "N" if direction == "Northbound" else "S"
                st.success("Settings saved!")
                st.rerun()
        
        # Initialize session state if not already set
        if "zip_code" not in st.session_state:
            st.session_state.zip_code = "10022"
        if "station_id" not in st.session_state:
            st.session_state.station_id = "127"
        if "subway_line" not in st.session_state:
            st.session_state.subway_line = "1"
        if "direction" not in st.session_state:
            st.session_state.direction = "N"
        
        if st.button("Refresh Data"):
            st.rerun()
        
        # Auto-refresh option
        auto_refresh = st.checkbox("Auto-refresh (1 min)", value=False)
        if auto_refresh:
            st.caption("Refreshing automatically...")
            # Use JavaScript to auto-refresh after 60 seconds
            st.markdown(
                """
                <script>
                    setTimeout(function() {
                        window.location.reload();
                    }, 60000);
                </script>
                """,
                unsafe_allow_html=True
            )
        
        st.divider()
        st.caption("© 2025 NYC Local Dashboard")
    
    return page

# --------------- DASHBOARD PAGE ---------------
def show_dashboard():
    st.title("NYC Local Dashboard")
    
    # Get settings
    zip_code = st.session_state.zip_code
    station_id = st.session_state.station_id
    subway_line = st.session_state.subway_line
    direction = st.session_state.direction
    
    # Initialize clients
    weather = NYCWeather(zip_code=zip_code)
    mta = MTAClient()
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Weather")
        with st.spinner("Loading weather data..."):
            current = weather.fetch_current_weather()
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
    
    with col2:
        st.subheader("Subway")
        with st.spinner("Loading subway data..."):
            # Get subway info
            station_info = mta.find_stations_by_id(station_id)
            station_name = station_info.iloc[0]["clean_name"] if not station_info.empty else f"Station {station_id}"
            
            st.subheader(f"Line {subway_line} at {station_name}")
            st.caption(f"{'Northbound' if direction == 'N' else 'Southbound'}")
            
            # Get train arrivals
            trains = mta.get_upcoming_trains(subway_line, station_id, direction)
            
            if not trains.empty:
                # Draw train arrivals
                now = datetime.now(pytz.timezone('America/New_York'))
                
                for _, train in trains.iterrows():
                    mins = int((train['arrival_time'] - now).total_seconds() / 60)
                    cols = st.columns([1, 3, 1])
                    
                    with cols[0]:
                        # Subway line circle
                        line_color = "#EE352E" if subway_line in "123" else "#00933C"
                        st.markdown(
                            f"""
                            <div style="width:40px;height:40px;border-radius:50%;background-color:{line_color};
                            color:white;display:flex;align-items:center;justify-content:center;font-weight:bold;">
                            {subway_line}
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    
                    with cols[1]:
                        if mins <= 0:
                            st.markdown("**Arriving now**")
                        else:
                            st.markdown(f"**Arrives in {mins} min**")
                        st.caption(f"Train: {train['trip_id'][:6]}")
                    
                    with cols[2]:
                        st.markdown(f"**{train['arrival_time'].strftime('%I:%M %p')}**")
                    
                    st.divider()
                
                st.caption(f"Last updated: {now.strftime('%I:%M:%S %p')}")
            else:
                st.error("Train data unavailable")
    
    # Hourly forecast
    st.header("Next 5 Hours")
    with st.spinner("Loading forecast..."):
        forecast = weather.fetch_forecast_weather(days=2)
        if forecast and "forecast" in forecast:
            # Get current hour and upcoming hours
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
            
            # Display next 5 hours
            hour_cols = st.columns(5)
            for i in range(5):
                if i < len(hours):
                    hour = hours[i]
                    hour_time = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
                    
                    with hour_cols[i]:
                        st.write(f"**{hour_time.strftime('%I %p')}**")
                        st.write(f"{hour['temp_c']}°C")
                        st.write(hour['condition']['text'])
                        
                        if int(hour['chance_of_rain']) > 0:
                            st.write(f"Rain: {hour['chance_of_rain']}%")
        else:
            st.error("Forecast data unavailable")

# --------------- WEATHER DETAILS PAGE ---------------
def show_weather_details():
    st.title("NYC Weather Details")
    
    # Get settings
    zip_code = st.session_state.zip_code
    
    # Initialize weather client
    weather = NYCWeather(zip_code=zip_code)
    
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
def show_subway_lookup():
    st.title("NYC Subway Lookup")
    
    # Get settings
    station_id = st.session_state.station_id
    subway_line = st.session_state.subway_line
    direction = st.session_state.direction
    
    # Initialize MTA client
    mta = MTAClient()
    
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
                    
                    # Button to select this station
                    if st.button(f"Show trains at {station['clean_name']}", key=f"station_{station['core_id']}"):
                        st.session_state.station_id = station['core_id']
                        
                        # If station has multiple lines, choose the first one
                        if 'lines' in station and station['lines']:
                            st.session_state.subway_line = station['lines'][0]
                        
                        st.rerun()
                
                st.divider()
        else:
            st.warning(f"No stations found matching '{search_term}'")
    
    # Train arrival section
    st.header("Upcoming Trains")
    
    # Station selection widget
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        station_info = mta.find_stations_by_id(station_id)
        station_name = station_info.iloc[0]["clean_name"] if not station_info.empty else f"Station {station_id}"
        st.write(f"**{station_name}** (ID: {station_id})")
    
    with col2:
        selected_line = st.selectbox("Line", ["1", "2", "3", "4", "5", "6", "7", "A", "C", "E", "N", "Q", "R", "W"], 
                                    index=0 if subway_line not in ["1", "2", "3", "4", "5", "6", "7", "A", "C", "E", "N", "Q", "R", "W"] else 
                                    ["1", "2", "3", "4", "5", "6", "7", "A", "C", "E", "N", "Q", "R", "W"].index(subway_line))
    
    with col3:
        selected_direction = st.radio("Direction", ["Northbound", "Southbound"], 
                                     index=0 if direction == "N" else 1)
    
    if st.button("Get Train Times"):
        st.session_state.subway_line = selected_line
        st.session_state.direction = "N" if selected_direction == "Northbound" else "S"
        st.rerun()
    
    # Display train times
    st.subheader(f"Line {subway_line} at {station_name}")
    st.caption(f"{'Northbound' if direction == 'N' else 'Southbound'}")
    
    with st.spinner("Loading train data..."):
        trains = mta.get_upcoming_trains(subway_line, station_id, direction, limit=10)
        
        if not trains.empty:
            # Create a nicely formatted table of arrivals
            now = datetime.now(pytz.timezone('America/New_York'))
            
            # Header row
            cols = st.columns([1, 2, 2, 2])
            with cols[0]:
                st.write("**Line**")
            with cols[1]:
                st.write("**Train ID**")
            with cols[2]:
                st.write("**Minutes**")
            with cols[3]:
                st.write("**Time**")
            
            st.divider()
            
            # Train rows
            for _, train in trains.iterrows():
                mins = int((train['arrival_time'] - now).total_seconds() / 60)
                
                cols = st.columns([1, 2, 2, 2])
                
                with cols[0]:
                    # Subway line circle
                    line_color = "#EE352E" if subway_line in "123" else "#00933C"
                    st.markdown(
                        f"""
                        <div style="width:30px;height:30px;border-radius:50%;background-color:{line_color};
                        color:white;display:flex;align-items:center;justify-content:center;font-weight:bold;">
                        {subway_line}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                
                with cols[1]:
                    st.write(train['trip_id'][:6])
                
                with cols[2]:
                    if mins <= 0:
                        st.markdown("**Arriving now**")
                    else:
                        st.markdown(f"{mins} min")
                
                with cols[3]:
                    st.write(train['arrival_time'].strftime('%I:%M %p'))
                
                st.divider()
            
            st.caption(f"Last updated: {now.strftime('%I:%M:%S %p')}")
        else:
            st.error("No train data available")

# --------------- MAIN APP ---------------
# Create sidebar and get selected page
selected_page = create_sidebar()

# Display the selected page
if selected_page == "Dashboard":
    show_dashboard()
elif selected_page == "Weather Details":
    show_weather_details()
elif selected_page == "Subway Lookup":
    show_subway_lookup()