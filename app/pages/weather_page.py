import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

# Import weather class
from lib.weather.nyc_weather import NYCWeather

def show():
    """Display detailed weather page."""
    
    st.title("NYC Weather")
    
    # Get user settings from session state
    zip_code = st.session_state.zip_code
    
    # Initialize weather client
    weather_client = NYCWeather(zip_code=zip_code)
    
    # Fetch data (current and 3-day forecast)
    with st.spinner("Fetching weather data..."):
        current_data = weather_client.fetch_current_weather()
        forecast_data = weather_client.fetch_forecast_weather(days=3)
    
    if not current_data:
        st.error("Failed to load weather data. Please check your connection and API key.")
        return
    
    # Location information
    location = current_data["location"]["name"]
    region = current_data["location"]["region"]
    
    # Current weather section
    st.header(f"Current Weather in {location}, {region}")
    
    # Main current weather display
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Temperature and condition
        current = current_data["current"]
        temp = current["temp_c"]
        condition = current["condition"]["text"]
        
        st.metric(
            "Temperature", 
            f"{temp}°C / {current['temp_f']}°F", 
            f"Feels like: {current['feelslike_c']}°C"
        )
        
        # Display condition with icon (text-based for efficiency)
        st.markdown(f"### {condition}")
        
        # Last updated time
        st.caption(f"Last updated: {current['last_updated']}")
    
    with col2:
        # Wind and pressure
        st.metric("Wind", f"{current['wind_kph']} km/h {current['wind_dir']}")
        st.metric("Pressure", f"{current['pressure_mb']} mb")
        st.metric("Humidity", f"{current['humidity']}%")
    
    with col3:
        # Visibility and UV
        st.metric("Visibility", f"{current['vis_km']} km")
        st.metric("UV Index", current['uv'])
        st.metric("Cloud Cover", f"{current['cloud']}%")
    
    # Air Quality section (if available)
    if "air_quality" in current_data["current"]:
        st.subheader("Air Quality")
        
        aq = current_data["current"]["air_quality"]
        
        # AQI metrics
        aqi_cols = st.columns(3)
        
        with aqi_cols[0]:
            if "us-epa-index" in aq:
                epa_index = aq["us-epa-index"]
                epa_desc = get_epa_description(epa_index)
                st.metric("US EPA Index", f"{epa_index} - {epa_desc}")
        
        with aqi_cols[1]:
            if "pm2_5" in aq:
                st.metric("PM2.5", f"{aq['pm2_5']:.1f}")
            
        with aqi_cols[2]:
            if "pm10" in aq:
                st.metric("PM10", f"{aq['pm10']:.1f}")
        
        # Additional air quality metrics
        aq_cols2 = st.columns(3)
        
        with aq_cols2[0]:
            if "o3" in aq:
                st.metric("Ozone", f"{aq['o3']:.1f}")
        
        with aq_cols2[1]:
            if "no2" in aq:
                st.metric("Nitrogen Dioxide", f"{aq['no2']:.1f}")
        
        with aq_cols2[2]:
            if "co" in aq:
                st.metric("Carbon Monoxide", f"{aq['co']:.1f}")
    
    # Hourly forecast section
    st.header("Hourly Forecast")
    
    # Get hourly data from forecast
    if forecast_data and "forecast" in forecast_data:
        hours_data = []
        
        # Get current hour
        current_hour = datetime.now().hour
        
        # Collect next 24 hours across days
        total_hours = 0
        
        for day in forecast_data["forecast"]["forecastday"]:
            for hour in day["hour"]:
                hour_time = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
                
                # Only include hours from current hour onwards
                if (day == forecast_data["forecast"]["forecastday"][0] and 
                    hour_time.hour < current_hour):
                    continue
                
                if total_hours < 24:
                    hours_data.append({
                        "time": hour_time,
                        "temp_c": hour["temp_c"],
                        "condition": hour["condition"]["text"],
                        "chance_of_rain": hour["chance_of_rain"],
                        "wind_kph": hour["wind_kph"],
                        "humidity": hour["humidity"]
                    })
                    total_hours += 1
        
        # Create dataframe for plotting
        df = pd.DataFrame(hours_data)
        
        # Create simplified temperature chart (for Raspberry Pi efficiency)
        times = [h.strftime("%I %p") for h in df["time"]]
        
        # Temperature chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times, 
            y=df["temp_c"],
            mode='lines+markers',
            name='Temperature (°C)',
            line=dict(color='#FF9E00', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="24-Hour Temperature Forecast",
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display hourly details in expandable sections
        with st.expander("Hourly Details"):
            # Display in 6-hour chunks for better organization
            for i in range(0, len(hours_data), 6):
                chunk = hours_data[i:i+6]
                
                cols = st.columns(len(chunk))
                
                for j, hour_data in enumerate(chunk):
                    with cols[j]:
                        hour_time = hour_data["time"]
                        st.markdown(f"**{hour_time.strftime('%I %p')}**")
                        st.write(f"{hour_data['temp_c']}°C")
                        st.write(f"{hour_data['condition']}")
                        st.write(f"Rain: {hour_data['chance_of_rain']}%")
                        st.write(f"Wind: {hour_data['wind_kph']} km/h")
                
                if i + 6 < len(hours_data):
                    st.divider()
    
    # 3-Day forecast section
    st.header("3-Day Forecast")
    
    if forecast_data and "forecast" in forecast_data:
        forecast_days = forecast_data["forecast"]["forecastday"]
        
        # Use columns for daily forecasts
        day_cols = st.columns(len(forecast_days))
        
        for i, day in enumerate(forecast_days):
            with day_cols[i]:
                date = datetime.strptime(day["date"], "%Y-%m-%d")
                date_str = date.strftime("%A, %b %d")
                
                st.subheader(date_str)
                
                day_data = day["day"]
                st.write(f"**{day_data['condition']['text']}**")
                
                # Temperature range
                st.metric(
                    "Temperature", 
                    f"{day_data['avgtemp_c']}°C", 
                    delta=f"Range: {day_data['mintemp_c']} - {day_data['maxtemp_c']}°C"
                )
                
                st.write(f"💧 Rain: {day_data['daily_chance_of_rain']}%")
                st.write(f"💨 Max Wind: {day_data['maxwind_kph']} km/h")
                st.write(f"☂️ Precipitation: {day_data['totalprecip_mm']} mm")
                st.write(f"💧 Humidity: {day_data['avghumidity']}%")
                st.write(f"☀️ UV Index: {day_data['uv']}")
    
    # Provide option to refresh data
    if st.button("Refresh Weather Data"):
        st.experimental_rerun()

# Helper function for EPA description
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