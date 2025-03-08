import streamlit as st
import time

# Import data classes
from lib.weather.nyc_weather import NYCWeather
from lib.mta.mta_client import MTAClient

# Import display components
from app.components import weather_card, subway_card

def show():
    """Show the main dashboard with weather and subway information."""
    
    st.title("NYC Local Dashboard")
    
    # Get user settings from session state
    zip_code = st.session_state.zip_code
    station_id = st.session_state.station_id
    subway_line = st.session_state.subway_line
    direction = st.session_state.direction
    
    # Use two columns for layout
    col1, col2 = st.columns(2)
    
    # Data loading indicators
    with col1:
        weather_placeholder = st.empty()
        with weather_placeholder.container():
            st.subheader("Weather")
            st.info("Loading weather data...")
    
    with col2:
        subway_placeholder = st.empty()
        with subway_placeholder.container():
            st.subheader("Subway")
            st.info("Loading subway data...")
    
    # Load data in parallel (conceptually)
    # Initialize MTA client
    mta_client = MTAClient()
    
    # Weather data
    try:
        weather_client = NYCWeather(zip_code=zip_code)
        current_weather = weather_client.fetch_current_weather()
        # Add a timeout to avoid infinite loading
        forecast_data = weather_client.fetch_forecast_weather(days=2)
    except Exception as e:
        st.error(f"Error loading weather data: {e}")
        current_weather = None
        forecast_data = None
    
    # Subway data
    try:
        train_arrivals = mta_client.get_upcoming_trains(
            subway_line,
            station_id,
            direction,
            limit=5
        )
        
        # Get station info
        stations = mta_client.find_stations_by_id(station_id)
        if not stations.empty:
            station_name = stations.iloc[0]["clean_name"]
        else:
            station_name = f"Station {station_id}"
            
    except Exception as e:
        train_arrivals = None
        station_name = f"Station {station_id}"
        st.error(f"Error loading subway data: {e}")
    
    # Display weather data
    with weather_placeholder.container():
        weather_card.display_current_card(current_weather)
    
    # Display subway data
    with subway_placeholder.container():
        subway_card.display_trains_card(
            train_arrivals, 
            subway_line, 
            station_name, 
            direction
        )
    
    # Lower section with forecasts
    st.divider()
    
    # 5-hour forecast
    st.subheader("Next 5 Hours")
    weather_card.display_hourly_forecast(forecast_data)
    
    # Divider
    st.divider()
    
    # 3-day forecast
    st.subheader("3-Day Forecast")
    weather_card.display_daily_forecast(forecast_data)
    
    # Add auto-refresh option
    st.sidebar.divider()
    
    if st.sidebar.checkbox("Auto-refresh data (1 min)"):
        st.sidebar.write("Auto-refreshing enabled")
        time.sleep(60)
        st.rerun()