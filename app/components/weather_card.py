import streamlit as st
from datetime import datetime
import pandas as pd

def display_current_card(data):
    """
    Display current weather in a card format.
    
    Args:
        data: Weather data from API
    """
    if not data:
        st.warning("Weather data unavailable")
        return
    
    # Extract location and current weather
    location = data["location"]["name"]
    region = data["location"]["region"]
    current = data["current"]
    
    # Create card container
    with st.container():
        st.subheader(f"Weather: {location}, {region}")
        
        # Layout with columns
        col1, col2 = st.columns([2, 3])
        
        with col1:
            # Temperature and condition
            temp = current["temp_c"]
            condition = current["condition"]["text"]
            
            # Display large temperature
            st.markdown(f"### {temp}°C / {current['temp_f']}°F")
            st.markdown(f"**{condition}**")
            st.caption(f"Feels like {current['feelslike_c']}°C / {current['feelslike_f']}°F")
        
        with col2:
            # Weather details
            metrics = [
                f"💨 Wind: {current['wind_kph']} km/h {current['wind_dir']}",
                f"💧 Humidity: {current['humidity']}%",
                f"☁️ Cloud Cover: {current['cloud']}%",
                f"👁️ Visibility: {current['vis_km']} km",
                f"🔆 UV Index: {current['uv']}"
            ]
            
            # Display metrics as a list for compact view
            for metric in metrics:
                st.markdown(metric)
        
        # Last updated information
        st.caption(f"Last updated: {current['last_updated']}")

def display_hourly_forecast(data, num_hours=5):
    """
    Display hourly forecast in a compact format.
    
    Args:
        data: Weather forecast data from API
        num_hours: Number of hours to display
    """
    if not data or "forecast" not in data:
        st.warning("Hourly forecast data unavailable")
        return
    
    # Get hourly data
    try:
        forecast_day = data["forecast"]["forecastday"][0]
        hours = forecast_day["hour"]
        
        # Get current hour
        current_hour = datetime.now().hour
        
        # Select upcoming hours
        next_hours = []
        total_selected = 0
        
        # First try to get hours from current day
        for hour in hours:
            hour_time = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
            if hour_time.hour >= current_hour and total_selected < num_hours:
                next_hours.append(hour)
                total_selected += 1
        
        # If we need more hours, check if there's another day available
        if total_selected < num_hours and len(data["forecast"]["forecastday"]) > 1:
            next_day_hours = data["forecast"]["forecastday"][1]["hour"]
            for hour in next_day_hours:
                if total_selected < num_hours:
                    next_hours.append(hour)
                    total_selected += 1
        
        if not next_hours:
            st.info("No hourly forecast available for upcoming hours")
            return
        
        # Create columns for display
        cols = st.columns(len(next_hours))
        
        for i, hour in enumerate(next_hours):
            with cols[i]:
                # Extract hour time and format it
                hour_time = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
                time_str = hour_time.strftime("%I %p")
                
                # Display hour card
                st.markdown(f"**{time_str}**")
                st.markdown(f"{hour['temp_c']}°C")
                st.caption(f"{hour['condition']['text']}")
                
                # Display chance of rain if above 0%
                if int(hour['chance_of_rain']) > 0:
                    st.caption(f"Rain: {hour['chance_of_rain']}%")
                
                # Wind info
                st.caption(f"{hour['wind_kph']} km/h")
    
    except Exception as e:
        st.error(f"Error displaying hourly forecast: {str(e)}")

def display_daily_forecast(data):
    """
    Display daily forecast in a compact format.
    
    Args:
        data: Weather forecast data from API
    """
    if not data or "forecast" not in data:
        st.warning("Daily forecast data unavailable")
        return
    
    try:
        forecast_days = data["forecast"]["forecastday"]
        
        # Create columns for display
        cols = st.columns(len(forecast_days))
        
        for i, day in enumerate(forecast_days):
            with cols[i]:
                # Format date
                date = datetime.strptime(day["date"], "%Y-%m-%d")
                date_str = date.strftime("%a, %b %d") if i > 0 else "Today"
                
                # Get day data
                day_data = day["day"]
                
                # Display day card
                st.markdown(f"**{date_str}**")
                st.markdown(f"{day_data['condition']['text']}")
                
                # Temperature range
                st.markdown(f"🔼 {day_data['maxtemp_c']}°C / {day_data['maxtemp_f']}°F")
                st.markdown(f"🔽 {day_data['mintemp_c']}°C / {day_data['mintemp_f']}°F")
                
                # Display chance of rain if above 0%
                if int(day_data['daily_chance_of_rain']) > 0:
                    st.caption(f"Rain: {day_data['daily_chance_of_rain']}%")
                    st.caption(f"Precip: {day_data['totalprecip_mm']} mm")
                
                # Wind
                st.caption(f"Wind: {day_data['maxwind_kph']} km/h")
    
    except Exception as e:
        st.error(f"Error displaying daily forecast: {str(e)}")

def display_aqi_card(data):
    """
    Display air quality information in a card format.
    
    Args:
        data: Weather data from API
    """
    if not data or "current" not in data or "air_quality" not in data["current"]:
        st.info("Air quality data unavailable")
        return
    
    try:
        # Extract AQI data
        aq = data["current"]["air_quality"]
        
        # Create card container
        with st.container():
            st.subheader("Air Quality")
            
            # EPA index if available
            if "us-epa-index" in aq:
                epa_index = aq["us-epa-index"]
                epa_desc = get_epa_description(epa_index)
                
                # Style based on index
                if epa_index <= 2:  # Good or Moderate
                    st.success(f"US EPA Index: {epa_index} - {epa_desc}")
                elif epa_index <= 4:  # Unhealthy for sensitive groups or Unhealthy
                    st.warning(f"US EPA Index: {epa_index} - {epa_desc}")
                else:  # Very Unhealthy or Hazardous
                    st.error(f"US EPA Index: {epa_index} - {epa_desc}")
            
            # Layout with columns for details
            col1, col2 = st.columns(2)
            
            with col1:
                if "pm2_5" in aq:
                    st.metric("PM2.5", f"{aq['pm2_5']:.1f}")
                if "o3" in aq:
                    st.metric("Ozone", f"{aq['o3']:.1f}")
                if "so2" in aq:
                    st.metric("Sulfur Dioxide", f"{aq['so2']:.1f}")
            
            with col2:
                if "pm10" in aq:
                    st.metric("PM10", f"{aq['pm10']:.1f}")
                if "no2" in aq:
                    st.metric("Nitrogen Dioxide", f"{aq['no2']:.1f}")
                if "co" in aq:
                    st.metric("Carbon Monoxide", f"{aq['co']:.1f}")
    
    except Exception as e:
        st.error(f"Error displaying air quality: {str(e)}")

def get_epa_description(index):
    """Get descriptive text for EPA air quality index values."""
    descriptions = {
        1: "Good",
        2: "Moderate",
        3: "Unhealthy for sensitive groups",
        4: "Unhealthy",
        5: "Very Unhealthy",
        6: "Hazardous"
    }
    return descriptions.get(index, "Unknown")