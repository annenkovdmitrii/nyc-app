```
nyc-app/
├── app/
│   ├── assets/
│   │   ├── styles.css              # Custom styling
│   │   └── nyc_icon.png            # Only the icon file needed
│   ├── main.py                     # Main Streamlit UI and page logic
│   ├── nyc_weather.py              # NYCWeather class
│   └── mta_client.py               # MTAClient class
├── data/                           # Keep data cache folders
│   ├── mta_cache/
│   └── weather_cache/
├── docker-compose.yml              # Keep Docker configuration
├── Dockerfile                      # Keep Docker configuration
└── requirements.txt                # Keep dependencies list
```
