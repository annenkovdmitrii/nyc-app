import os
import requests
import json
from datetime import datetime, timedelta

class NYCWeather:
    """Class for fetching and handling NYC weather data from WeatherAPI.com."""
    
    def __init__(self, zip_code="10022", api_key=None, use_cache=True):
        """
        Initialize the NYC Weather object.
        
        Args:
            zip_code (str): ZIP code for weather location
            api_key (str, optional): WeatherAPI.com API key. If None, tries to get from env vars.
            use_cache (bool): Whether to use cached data to reduce API calls
        """
        self.zip_code = zip_code
        self.api_key = api_key or os.environ.get("WEATHER_API_KEY", "your_api_key_here")
        self.use_cache = use_cache
        self.current_url = "http://api.weatherapi.com/v1/current.json"
        self.forecast_url = "http://api.weatherapi.com/v1/forecast.json"
        
        # Cache paths
        self.cache_dir = "data/weather_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _log_error(self, message):
        """Log an error message without using streamlit."""
        print(f"ERROR: {message}")
    
    def _get_cache_path(self, data_type):
        """Get path for a specific cache file."""
        return os.path.join(self.cache_dir, f"{data_type}_{self.zip_code}.json")
    
    def _save_to_cache(self, data, data_type):
        """Save data to cache file."""
        if not self.use_cache:
            return
            
        try:
            cache_path = self._get_cache_path(data_type)
            with open(cache_path, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }, f)
        except Exception as e:
            self._log_error(f"Error saving to cache: {e}")
    
    def _load_from_cache(self, data_type, max_age_minutes=30):
        """Load data from cache if not too old."""
        if not self.use_cache:
            return None
            
        try:
            cache_path = self._get_cache_path(data_type)
            if not os.path.exists(cache_path):
                return None
                
            with open(cache_path, 'r') as f:
                cache = json.load(f)
                
            # Check cache age
            cached_time = datetime.fromisoformat(cache['timestamp'])
            age = datetime.now() - cached_time
            
            if age < timedelta(minutes=max_age_minutes):
                return cache['data']
        except Exception as e:
            self._log_error(f"Error loading from cache: {e}")
            
        return None

    def fetch_current_weather(self):
        """
        Fetch current weather data from the API or cache.
        
        Returns:
            dict: Current weather data or None if request fails.
        """
        # Try from cache first
        cached_data = self._load_from_cache('current', max_age_minutes=30)
        if cached_data:
            return cached_data
            
        # If not in cache, fetch from API
        try:
            params = {
                "key": self.api_key,
                "q": self.zip_code,
                "aqi": "yes"  # Enable AQI data
            }
            response = requests.get(self.current_url, params=params)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            data = response.json()
            self._save_to_cache(data, 'current')
            return data
        except Exception as e:
            self._log_error(f"Error fetching weather: {e}")
            return None

    def fetch_forecast_weather(self, days=1):
        """
        Fetch forecast weather data from the API or cache.
        
        Args:
            days (int): Number of days for forecast (1-3)
            
        Returns:
            dict: Forecast weather data or None if request fails.
        """
        # Try from cache first (forecast can be cached longer)
        cache_key = f'forecast_{days}day'
        cached_data = self._load_from_cache(cache_key, max_age_minutes=180)  # 3 hours
        if cached_data:
            return cached_data
            
        # If not in cache, fetch from API
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
            
            data = response.json()
            self._save_to_cache(data, cache_key)
            return data
        except Exception as e:
            self._log_error(f"Error fetching forecast: {e}")
            return None
            
    def get_epa_description(self, index):
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