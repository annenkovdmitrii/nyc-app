# NYC Local Dashboard

A streamlined Raspberry Pi-friendly dashboard for New York City weather and subway information. This application provides real-time updates on weather conditions and upcoming subway train arrivals for your favorite stations.

![NYC Dashboard Screenshot](app/assets/nyc_icon.png)

## Features

- **Current Weather**: Display current conditions, temperature, wind, humidity, and UV index for NYC
- **Weather Forecast**: Show upcoming 3-hour forecast
- **Subway Arrivals**: Monitor train arrivals at three configurable stations
- **Auto-Refresh**: Keep data updated with built-in auto-refresh functionality
- **Station Search**: Find any subway station in the MTA system
- **Detailed Weather**: Access comprehensive weather information including air quality
- **Customizable**: Configure your default stations and preferences

## Installation

### Prerequisites

- Python 3.9+
- Raspberry Pi (recommended) or any computer that can run Python
- Internet connection

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/dmitriiannenkov/nyc-dashboard.git
   cd nyc-dashboard
   ```

2. Create a virtual environment:
   ```bash
   python -m venv nyc-app
   source nyc-app/bin/activate  # On Windows: nyc-app\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API key:
   ```
   WEATHER_API_KEY=your_weatherapi_com_key
   ```

### Running the Dashboard

```bash
cd app
streamlit run main.py
```

The dashboard will open in your web browser at http://localhost:8501

## Project Structure

```
nyc-app/
├── app/                       # Application code
│   ├── assets/                # Static assets
│   │   ├── styles.css         # Custom styling
│   │   └── nyc_icon.png       # App icon
│   ├── main.py                # Main Streamlit UI and page logic
│   ├── nyc_weather.py         # NYCWeather class for weather data
│   ├── mta_client.py          # MTAClient class for subway data
│   └── utils.py               # Utility functions
├── data/                      # Data cache directories
│   ├── mta_cache/             # MTA data cache
│   └── weather_cache/         # Weather data cache
├── tests/                     # Test files
├── docker-compose.yml         # Docker configuration
├── Dockerfile                 # Docker build file
└── requirements.txt           # Python dependencies
```

## Docker Deployment

You can also run the application using Docker:

```bash
docker-compose up
```

This will build and start the container with the application running on port 8501.

## API Usage

This application uses:

1. **WeatherAPI.com**: For real-time weather data and forecasts. You'll need to [sign up](https://www.weatherapi.com/signup.aspx) for a free API key.

2. **MTA GTFS Realtime Feed**: For subway arrival information. This is publicly available and doesn't require an API key.

## Performance Considerations

The application is optimized for Raspberry Pi usage:

- Efficient caching system to reduce API calls
- Lazy loading of components to minimize startup time
- Performance monitoring with timing decorators
- Single auto-refresh mechanism to reduce resource usage

## Customization

### Adding Default Stations

1. Navigate to the "Subway Lookup" page
2. Search for a station
3. Use the "Add to Defaults" feature to set it as one of your default stations

### Changing Refresh Rate

The auto-refresh is set to 60 seconds by default. This can be modified in the `setup_auto_refresh` function in `main.py`.

## Testing

Run the tests with:

```bash
cd tests
python -m unittest test_mta_client.py
```

## License

[MIT License](LICENSE)

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Subway data from [MTA GTFS-Realtime Feed](https://api.mta.info/)
- Weather data from [WeatherAPI.com](https://www.weatherapi.com/)
