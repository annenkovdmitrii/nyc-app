```
nyc-app/
├── docker-compose.yml           # Orchestrates all containers
├── Dockerfile                   # Main app container
├── requirements.txt             # Combined dependencies
├── .env                         # Environment variables (API keys, etc.)
│
├── app/                         # Streamlit application
│   ├── __init__.py 
│   ├── main.py                  # Main Streamlit entry point
│   ├── sidebar.py               # Sidebar navigation component
│   ├── pages/                   # Page components
│   │   ├── dashboard.py         # Combined dashboard view
│   │   ├── weather_page.py      # Detailed weather page
│   │   └── subway_page.py       # Detailed subway information
│   │
│   ├── components/              # Reusable UI components
│   ├── __init__.py 
│   │   ├── weather_card.py      # Weather display components
│   │   └── subway_card.py       # Subway display components
│   │
│   └── assets/                  # Static assets
│       ├── styles.css           # Custom styling
│       └── nyc_icon.png         # App icon
│
├── lib/                         # Core functionality
│   ├── __init__.py              # Make lib a package
│   ├── weather/                 # Weather module
│   │   ├── __init__.py
│   │   └── nyc_weather.py       # NYCWeather class
│   │
│   └── mta/                     # MTA module
│       ├── __init__.py
│       └── mta_client.py        # MTAClient class
│
└── data/                        # Data storage
    ├── weather_cache/           # Cache for weather data
    └── mta_cache/               # Cache for MTA data
```
