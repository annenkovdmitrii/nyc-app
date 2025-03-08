import requests
import pandas as pd
import io
import zipfile
from google.transit import gtfs_realtime_pb2
import pytz
from datetime import datetime
import os
import re

class MTAClient:
    """Integrated client for MTA subway data, including both real-time API and station lookup."""
    
    # Base URL for MTA's GTFS-RT feeds
    RT_BASE_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2F"
    
    # Feed IDs for different subway lines
    FEED_IDS = {
        '123456': 'gtfs',         # 1,2,3,4,5,6 lines
        '7': 'gtfs-7',            # 7 line
        'ACE': 'gtfs-ace',        # A,C,E lines
        'BDFM': 'gtfs-bdfm',      # B,D,F,M lines
        'G': 'gtfs-g',            # G line
        'JZ': 'gtfs-jz',          # J,Z lines
        'NQRW': 'gtfs-nqrw',      # N,Q,R,W lines
        'L': 'gtfs-l',            # L line
        'SI': 'gtfs-si'           # Staten Island Railway
    }
    
    # URL for MTA's static GTFS data
    GTFS_URL = "http://web.mta.info/developers/data/nyct/subway/google_transit.zip"
    CACHE_DIR = "mta_data_cache"
    
    def __init__(self, use_cache=True, verbose=True):
        """
        Initialize the integrated MTA client.
        
        Args:
            use_cache: Whether to cache and use cached station data
            verbose: Whether to print status messages
        """
        self.use_cache = use_cache
        self.verbose = verbose
        self.stations = None
        self.routes = None
        
        # Load station data
        self._load_station_data()
    
    def log(self, message):
        """Print a log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    #
    # REAL-TIME TRAIN DATA METHODS
    #
    
    def get_feed(self, feed_id):
        """Get raw GTFS feed by ID."""
        url = f"{self.RT_BASE_URL}{feed_id}"
        self.log(f"Fetching feed from {url}")
        
        response = requests.get(url)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get feed: {response.status_code}, {response.text}")
        
        # Parse the protobuf data
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        return feed
    
    def get_feed_by_line(self, line):
        """Get feed for a specific subway line."""
        # Find the appropriate feed ID
        for key, value in self.FEED_IDS.items():
            if line in key:
                return self.get_feed(value)
        
        raise ValueError(f"No feed found for line {line}")
    
    def get_upcoming_trains(self, line, station_id, direction='N', limit=5):
        """
        Get upcoming trains for a specific station.
        
        Args:
            line: Subway line (e.g., '1', 'A', 'L')
            station_id: MTA station ID (e.g., '101')
            direction: 'N' for northbound, 'S' for southbound
            limit: Maximum number of trains to return
            
        Returns:
            DataFrame of upcoming trains with arrival times
        """
        self.log(f"Getting upcoming {line} trains at station {station_id}{direction}")
        
        feed = self.get_feed_by_line(line)
        
        # Extract entity data
        trips = []
        for entity in feed.entity:
            if entity.HasField('trip_update'):
                trip = entity.trip_update
                route_id = trip.trip.route_id
                
                # Check if this trip belongs to the requested line
                if route_id == line:
                    for stop in trip.stop_time_update:
                        # Match station and direction
                        if stop.stop_id == f"{station_id}{direction}":
                            # Get arrival time if available, otherwise use departure time
                            time_value = None
                            if stop.HasField('arrival'):
                                time_value = stop.arrival.time
                            elif stop.HasField('departure'):
                                time_value = stop.departure.time
                            
                            if time_value:
                                # Convert POSIX timestamp to datetime
                                arrival_time = datetime.fromtimestamp(time_value, pytz.timezone('America/New_York'))
                                
                                trips.append({
                                    'route_id': route_id,
                                    'trip_id': trip.trip.trip_id,
                                    'arrival_time': arrival_time,
                                    'stop_id': stop.stop_id
                                })
        
        # Create DataFrame and sort by arrival time
        if trips:
            df = pd.DataFrame(trips)
            df = df.sort_values('arrival_time')
            return df.head(limit)
        else:
            self.log(f"No upcoming trains found for {line} at station {station_id}{direction}")
            return pd.DataFrame(columns=['route_id', 'trip_id', 'arrival_time', 'stop_id'])
    
    #
    # STATION LOOKUP METHODS
    #
    
    def _load_station_data(self):
        """Load station data from MTA GTFS feed."""
        # Create cache directory if it doesn't exist
        if self.use_cache and not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR)
        
        # Check if we have cached data and it's less than 1 day old
        cache_file = os.path.join(self.CACHE_DIR, "stops.csv")
        routes_file = os.path.join(self.CACHE_DIR, "routes.csv")
        
        if self.use_cache and os.path.exists(cache_file) and os.path.exists(routes_file):
            # Check cache age
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            age_in_days = (datetime.now() - file_time).days
            
            if age_in_days < 1:  # Use cache if less than 1 day old
                self.log(f"Using cached station data from {file_time}")
                self.stations = pd.read_csv(cache_file)
                self.routes = pd.read_csv(routes_file)
                return
        
        self.log("Downloading MTA GTFS data...")
        response = requests.get(self.GTFS_URL)
        
        if response.status_code != 200:
            raise Exception(f"Failed to download GTFS data: {response.status_code}")
        
        self.log("Parsing GTFS data...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Load stops.txt (stations)
            with z.open("stops.txt") as f:
                self.stations = pd.read_csv(f)
                
            # Load routes.txt (subway lines)
            with z.open("routes.txt") as f:
                self.routes = pd.read_csv(f)
        
        # Cache the data for future use
        if self.use_cache:
            self.stations.to_csv(cache_file, index=False)
            self.routes.to_csv(routes_file, index=False)
                
        self.log(f"Loaded {len(self.stations)} stations and {len(self.routes)} routes.")
    
    def clean_station_name(self, name):
        """Clean up station names for better display."""
        # Remove subway line indicators
        name = re.sub(r'\([1-7ACBDEFGJLMNQRWZ]+\)', '', name)
        # Remove direction/bound information
        name = re.sub(r'(Bound|bound|Uptown|Downtown|Express)', '', name)
        # Replace multiple spaces with a single space
        name = re.sub(r'\s+', ' ', name).strip()
        return name
    
    def find_stations_by_name(self, name_query, exact=False):
        """
        Find stations by name.
        
        Args:
            name_query: String to search for in station names
            exact: If True, match exactly; if False, use substring match
            
        Returns:
            DataFrame with matching stations
        """
        if self.stations is None:
            raise Exception("Station data not loaded")
        
        # Print first 5 station names for debugging
        if self.verbose:
            self.log(f"Sample station names in the dataset:")
            self.log(self.stations['stop_name'].head(5).tolist())
        
        self.log(f"Searching for stations with name containing '{name_query}'")
        
        if exact:
            matches = self.stations[self.stations['stop_name'] == name_query]
        else:
            # More flexible search - case insensitive substring match
            matches = self.stations[self.stations['stop_name'].str.contains(name_query, case=False, na=False)]
        
        if len(matches) == 0:
            self.log(f"No stations found matching '{name_query}'")
            
            # Try alternative searches for common NYC subway station names
            if "times square" in name_query.lower() or "times sq" in name_query.lower():
                self.log("Trying alternative search for Times Square...")
                # Try different variations of Times Square
                for alt_name in ["42 St-Times", "Times Sq", "42 St", "Port Authority"]:
                    alt_matches = self.stations[self.stations['stop_name'].str.contains(alt_name, case=False, na=False)]
                    if len(alt_matches) > 0:
                        self.log(f"Found {len(alt_matches)} stations matching '{alt_name}'")
                        return self._format_station_results(alt_matches)
            
            # If still no matches, return empty DataFrame
            return pd.DataFrame()
        
        self.log(f"Found {len(matches)} stations matching '{name_query}'")
        return self._format_station_results(matches)
    
    def find_stations_by_id(self, station_id):
        """
        Find stations by ID or partial ID.
        
        Args:
            station_id: Station ID or partial ID to search for
            
        Returns:
            DataFrame with matching stations
        """
        if self.stations is None:
            raise Exception("Station data not loaded")
        
        # Convert to string for comparison
        station_id = str(station_id)
        
        matches = self.stations[self.stations['stop_id'].astype(str).str.contains(station_id)]
        
        if len(matches) == 0:
            self.log(f"No stations found with ID containing '{station_id}'")
            return pd.DataFrame()
        
        return self._format_station_results(matches)
    
    def list_all_lines(self):
        """List all subway lines/routes."""
        if self.routes is None:
            raise Exception("Route data not loaded")
        
        return self.routes[['route_id', 'route_long_name', 'route_color']]
    
    def _format_station_results(self, matches):
        """Format station results for better display."""
        # Create copy to avoid modifying original data
        result = matches.copy()
        
        # Extract core station ID (removing direction suffix if present)
        result['core_id'] = result['stop_id'].astype(str).str.extract(r'(\d+)')[0]
        
        # Add direction information based on stop_id suffix
        result['direction'] = 'Unknown'
        result.loc[result['stop_id'].astype(str).str.endswith('N'), 'direction'] = 'Northbound'
        result.loc[result['stop_id'].astype(str).str.endswith('S'), 'direction'] = 'Southbound'
        
        # Clean station names
        result['clean_name'] = result['stop_name'].apply(self.clean_station_name)
        
        # Select and order columns
        columns = ['core_id', 'stop_id', 'clean_name', 'direction', 'stop_lat', 'stop_lon']
        available_columns = [col for col in columns if col in result.columns]
        
        return result[available_columns].sort_values(['core_id', 'direction'])
    
    def get_station_arrivals(self, station_name, line=None, direction='N', limit=5):
        """
        One-stop method to get train arrivals by station name.
        
        Args:
            station_name: Name of the station (e.g., "Times Square")
            line: Subway line (e.g., '1', 'A', 'L')
            direction: 'N' for northbound, 'S' for southbound
            limit: Maximum number of trains to return
            
        Returns:
            DataFrame of upcoming trains with arrival times
        """
        # Find the station first
        stations = self.find_stations_by_name(station_name)
        
        if stations.empty:
            self.log(f"No stations found matching '{station_name}'")
            # For Times Square specifically, try a hardcoded approach as it's a common station
            if "times square" in station_name.lower() or "times sq" in station_name.lower():
                if line == '1' or line == '2' or line == '3':
                    self.log("Using hardcoded Times Square station ID for 123 lines")
                    return self.get_upcoming_trains(line, '127', direction, limit)
                elif line == 'N' or line == 'Q' or line == 'R' or line == 'W':
                    self.log("Using hardcoded Times Square station ID for NQRW lines")
                    return self.get_upcoming_trains(line, '140', direction, limit)
                elif line == '7':
                    self.log("Using hardcoded Times Square station ID for 7 line")
                    return self.get_upcoming_trains(line, '725', direction, limit)
                elif line == 'A' or line == 'C' or line == 'E':
                    self.log("Using hardcoded Times Square station ID for ACE lines")
                    return self.get_upcoming_trains(line, 'A27', direction, limit)
            return pd.DataFrame()
        
        # If line is not specified, use the first station found
        if not line:
            self.log("Line not specified. Please specify a subway line.")
            return pd.DataFrame()
        
        # Get the station ID for the specified line/direction
        filtered_stations = stations
        if 'direction' in stations.columns:
            filtered_stations = stations[stations['direction'] == ('Northbound' if direction == 'N' else 'Southbound')]
        
        if filtered_stations.empty:
            self.log(f"No {('Northbound' if direction == 'N' else 'Southbound')} platform found for {station_name}")
            filtered_stations = stations  # Fall back to all stations
        
        station_id = filtered_stations.iloc[0]['core_id']
        
        # Get upcoming trains
        return self.get_upcoming_trains(line, station_id, direction, limit)
