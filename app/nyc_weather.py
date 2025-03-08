import os
import requests
from datetime import datetime

class NYCWeather:
    """Class for fetching and displaying NYC weather data."""
    
    def __init__(self, api_key=None, zip_code="10022"):
        """
        Initialize the NYC Weather object.
        
        Args:
            api_key (str, optional): WeatherAPI.com API key. If None, tries to get from env vars.
            zip_code (str, optional): NYC ZIP code to use. Defaults to 10022 (Midtown Manhattan).
        """
        self.api_key = api_key or os.environ.get("WEATHER_API_KEY", "your_api_key_here")
        self.zip_code = zip_code
        self.current_url = "http://api.weatherapi.com/v1/current.json"
        self.forecast_url = "http://api.weatherapi.com/v1/forecast.json"
        
        # Cache for API responses to avoid duplicate calls
        self._cache = {
            "current": None,
            "forecast_1day": None,
            "forecast_3day": None
        }
        
        print(f"Initialized NYC Weather with ZIP code: {self.zip_code}")
    
    def fetch_current_weather(self):
        """
        Fetch current weather data from the API.
        
        Returns:
            dict: Current weather data or None if request fails.
        """
        if self._cache["current"]:
            return self._cache["current"]
            
        try:
            params = {
                "key": self.api_key,
                "q": self.zip_code,
                "aqi": "yes"  # Enable AQI data
            }
            response = requests.get(self.current_url, params=params)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            self._cache["current"] = response.json()
            return self._cache["current"]
        except requests.exceptions.RequestException as e:
            print(f"API request error: {e}")
            return None

    def fetch_forecast_weather(self, days=1):
        """
        Fetch forecast weather data from the API.
        
        Args:
            days (int, optional): Number of days for forecast. Defaults to 1.
            
        Returns:
            dict: Forecast weather data or None if request fails.
        """
        cache_key = f"forecast_{days}day"
        if cache_key in self._cache and self._cache[cache_key]:
            return self._cache[cache_key]
            
        try:
            params = {
                "key": self.api_key,
                "q": self.zip_code,
                "days": days,
                "aqi": "yes",  # Enable AQI data
                "alerts": "no"  # Disable alerts to reduce response size
            }
            response = requests.get(self.forecast_url, params=params)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            self._cache[cache_key] = response.json()
            return self._cache[cache_key]
        except requests.exceptions.RequestException as e:
            print(f"API request error: {e}")
            return None
    
    def display_current_weather(self, data=None):
        """
        Display current weather information.
        
        Args:
            data (dict, optional): Pre-fetched weather data. If None, fetches it.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        data = data or self.fetch_current_weather()
        
        if not data:
            print("No current weather data available.")
            return False
        
        location = data["location"]["name"]
        region = data["location"]["region"]
        current = data["current"]
        
        print("\n" + "="*50)
        print(f"CURRENT WEATHER FOR {location}, {region}")
        print("="*50)
        print(f"Last Updated: {current['last_updated']}")
        print(f"Temperature: {current['temp_c']}°C / {current['temp_f']}°F")
        print(f"Feels Like: {current['feelslike_c']}°C / {current['feelslike_f']}°F")
        print(f"Condition: {current['condition']['text']}")
        print(f"Wind: {current['wind_kph']} km/h {current['wind_dir']}")
        print(f"Pressure: {current['pressure_mb']} mb")
        print(f"Humidity: {current['humidity']}%")
        print(f"Cloud Cover: {current['cloud']}%")
        print(f"Visibility: {current['vis_km']} km")
        print(f"UV Index: {current['uv']}")
        
        if "air_quality" in current:
            print("\nAIR QUALITY:")
            aq = current["air_quality"]
            if aq.get("us-epa-index"):
                epa_index = aq["us-epa-index"]
                epa_desc = self.get_epa_description(epa_index)
                print(f"US EPA Index: {epa_index} - {epa_desc}")
            
            for key, name in [
                ("pm2_5", "PM2.5"),
                ("pm10", "PM10"),
                ("o3", "Ozone"),
                ("no2", "Nitrogen Dioxide"),
                ("so2", "Sulfur Dioxide"),
                ("co", "Carbon Monoxide")
            ]:
                if key in aq and aq[key] is not None:
                    print(f"{name}: {aq[key]:.1f}")
        
        return True
    
    def display_5hour_forecast(self, data=None):
        """
        Display 5-hour forecast information.
        
        Args:
            data (dict, optional): Pre-fetched forecast data. If None, fetches it.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        data = data or self.fetch_forecast_weather(days=2)  # Need 2 days to ensure enough hours
        
        if not data or "forecast" not in data:
            print("No forecast data available.")
            return False
        
        location = data["location"]["name"]
        region = data["location"]["region"]
        forecast_day = data["forecast"]["forecastday"][0]
        hours = forecast_day["hour"]
        
        # Get current hour
        current_hour = datetime.now().hour
        
        # Select next 5 hours
        next_hours = []
        total_selected = 0
        
        # First try to get hours from current day
        for hour in hours:
            hour_time = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
            if hour_time.hour >= current_hour and total_selected < 5:
                next_hours.append(hour)
                total_selected += 1
        
        # If we still need more hours, check if there's another day available
        if total_selected < 5 and len(data["forecast"]["forecastday"]) > 1:
            next_day_hours = data["forecast"]["forecastday"][1]["hour"]
            for hour in next_day_hours:
                if total_selected < 5:
                    next_hours.append(hour)
                    total_selected += 1
        
        print("\n" + "="*50)
        print(f"5-HOUR FORECAST FOR {location}, {region}")
        print("="*50)
        
        for hour in next_hours:
            time_str = hour["time"].split()[1]  # Extract just the time part
            print(f"\nTime: {time_str}")
            print(f"Temperature: {hour['temp_c']}°C / {hour['temp_f']}°F")
            print(f"Condition: {hour['condition']['text']}")
            print(f"Chance of Rain: {hour['chance_of_rain']}%")
            print(f"Wind: {hour['wind_kph']} km/h {hour['wind_dir']}")
            print(f"Humidity: {hour['humidity']}%")
        
        return True
    
    def display_3day_forecast(self, data=None):
        """
        Display 3-day forecast information.
        
        Args:
            data (dict, optional): Pre-fetched forecast data. If None, fetches it.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        data = data or self.fetch_forecast_weather(days=3)
        
        if not data or "forecast" not in data:
            print("No forecast data available.")
            return False
        
        location = data["location"]["name"]
        region = data["location"]["region"]
        forecast_days = data["forecast"]["forecastday"]
        
        print("\n" + "="*50)
        print(f"3-DAY FORECAST FOR {location}, {region}")
        print("="*50)
        
        for day in forecast_days:
            date = day["date"]
            day_data = day["day"]
            
            print(f"\nDate: {date}")
            print(f"Max Temperature: {day_data['maxtemp_c']}°C / {day_data['maxtemp_f']}°F")
            print(f"Min Temperature: {day_data['mintemp_c']}°C / {day_data['mintemp_f']}°F")
            print(f"Average Temperature: {day_data['avgtemp_c']}°C / {day_data['avgtemp_f']}°F")
            print(f"Condition: {day_data['condition']['text']}")
            print(f"Chance of Rain: {day_data['daily_chance_of_rain']}%")
            print(f"Max Wind: {day_data['maxwind_kph']} km/h")
            print(f"Total Precipitation: {day_data['totalprecip_mm']} mm")
            print(f"Average Humidity: {day_data['avghumidity']}%")
            print(f"UV Index: {day_data['uv']}")
        
        return True
    
    def get_epa_description(self, index):
        """
        Get descriptive text for EPA air quality index values.
        
        Args:
            index (int): EPA air quality index (1-6)
            
        Returns:
            str: Description of the air quality level
        """
        descriptions = {
            1: "Good",
            2: "Moderate",
            3: "Unhealthy for sensitive groups",
            4: "Unhealthy",
            5: "Very Unhealthy",
            6: "Hazardous"
        }
        return descriptions.get(index, "Unknown")
    
    def run(self):
        """
        Run the complete weather report (current, 5-hour, and 3-day forecasts).
        """
        print("Fetching NYC weather data...")
        
        # Get current weather
        self.display_current_weather()
        
        # Get 5-hour forecast
        self.display_5hour_forecast()
        
        # Get 3-day forecast
        self.display_3day_forecast()
        
        print("\nWeather data fetch complete!")
