import unittest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import os
import sys
import datetime
import pytz

# Add the project root directory to the Python path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.transit import gtfs_realtime_pb2
from app.mta_client import MTAClient

class TestMTAClient(unittest.TestCase):
    """Test cases for the MTAClient class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Patch MTAClient._load_station_data to avoid API calls during initialization
        with patch.object(MTAClient, '_load_station_data'):
            # Create a client with cache disabled for most tests
            self.client = MTAClient(use_cache=False, verbose=False)
        
        # Override the cache dir to match your actual structure
        self.client.CACHE_DIR = "data/mta_cache"
        
        # Sample station data
        self.sample_stations = pd.DataFrame({
            'stop_id': ['127N', '127S', '128N', '128S'],
            'stop_name': ['Times Sq-42 St (1)', 'Times Sq-42 St (1)', 'Penn Station (1)', 'Penn Station (1)'],
            'stop_lat': [40.75529, 40.75529, 40.75058, 40.75058],
            'stop_lon': [-73.9879, -73.9879, -73.99134, -73.99134]
        })
        
        # Sample routes data
        self.sample_routes = pd.DataFrame({
            'route_id': ['1', '2', '3', 'A'],
            'route_long_name': ['Broadway - 7 Avenue Local', 'Broadway - 7 Avenue Express', 
                               'Broadway - 7 Avenue Express', '8 Avenue Express'],
            'route_color': ['EE352E', 'EE352E', 'EE352E', '0039A6']
        })
        
        # Set the sample data on the client to avoid API calls
        self.client.stations = self.sample_stations
        self.client.routes = self.sample_routes

    @patch('app.mta_client.requests.get')
    def test_get_feed(self, mock_get):
        """Test getting a GTFS feed."""
        # Create mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'test_content'
        mock_get.return_value = mock_response
        
        # Monkey patch the protobuf ParseFromString method
        gtfs_realtime_pb2.FeedMessage.ParseFromString = MagicMock()
        
        # Call the method
        result = self.client.get_feed('gtfs')
        
        # Assert requests.get was called with the correct URL
        mock_get.assert_called_once_with(f"{self.client.RT_BASE_URL}gtfs")
        
        # Assert ParseFromString was called with the response content
        gtfs_realtime_pb2.FeedMessage.ParseFromString.assert_called_once_with(b'test_content')

    @patch('app.mta_client.requests.get')
    def test_get_feed_error(self, mock_get):
        """Test error handling when getting a feed."""
        # Mock an error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response
        
        # Check that the appropriate exception is raised
        with self.assertRaises(Exception) as context:
            self.client.get_feed('gtfs')
        
        self.assertIn("Failed to get feed: 404", str(context.exception))

    def test_get_feed_by_line_valid(self):
        """Test getting feed by valid line."""
        # Patch the get_feed method to avoid actual API calls
        self.client.get_feed = MagicMock()
        
        # Call the method with line in FEED_IDS
        self.client.get_feed_by_line('1')
        
        # Assert get_feed was called with the correct feed ID
        self.client.get_feed.assert_called_once_with('gtfs')

    def test_get_feed_by_line_invalid(self):
        """Test getting feed by invalid line."""
        with self.assertRaises(ValueError) as context:
            self.client.get_feed_by_line('X')  # Line that doesn't exist
        
        self.assertIn("No feed found for line X", str(context.exception))

    @patch('app.mta_client.MTAClient.get_feed_by_line')
    def test_get_upcoming_trains(self, mock_get_feed):
        """Test getting upcoming trains for a station."""
        # Create a mock feed response
        feed = gtfs_realtime_pb2.FeedMessage()
        
        # Create an entity with a trip update
        entity = feed.entity.add()
        entity.id = "trip1"
        trip_update = entity.trip_update
        trip_update.trip.trip_id = "trip1"
        trip_update.trip.route_id = "1"
        
        # Add a stop time update for our target station
        stop_time = trip_update.stop_time_update.add()
        stop_time.stop_id = "127N"
        stop_time.arrival.time = int(datetime.datetime.now().timestamp() + 300)  # 5 minutes from now
        
        # Set the mock to return our feed
        mock_get_feed.return_value = feed
        
        # Call the method
        result = self.client.get_upcoming_trains('1', '127', 'N', limit=5)
        
        # Assert result is a DataFrame with expected columns
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(list(result.columns), ['route_id', 'trip_id', 'arrival_time', 'stop_id'])
        
        # Verify there's at least one row
        self.assertTrue(len(result) > 0)
        
        # Verify the first row has the expected values
        self.assertEqual(result.iloc[0]['route_id'], '1')
        self.assertEqual(result.iloc[0]['trip_id'], 'trip1')
        self.assertEqual(result.iloc[0]['stop_id'], '127N')

    @patch('os.path.exists')
    @patch('os.path.getmtime')
    @patch('pandas.read_csv')
    def test_load_station_data_from_cache(self, mock_read_csv, mock_getmtime, mock_exists):
        """Test loading station data from cache."""
        # First patch _load_station_data during initialization
        with patch.object(MTAClient, '_load_station_data'):
            client = MTAClient(use_cache=True, verbose=False)
        
        # Override cache dir
        client.CACHE_DIR = "data/mta_cache"
        
        # Create path variables
        cache_file = os.path.join(client.CACHE_DIR, "stops.csv")
        routes_file = os.path.join(client.CACHE_DIR, "routes.csv")
        
        # Configure exists mock to return True for cache files
        mock_exists.side_effect = lambda path: path in [client.CACHE_DIR, cache_file, routes_file]
        
        # Configure getmtime to return a recent timestamp
        mock_getmtime.return_value = datetime.datetime.now().timestamp()
        
        # Configure read_csv mock
        mock_read_csv.side_effect = [self.sample_stations, self.sample_routes]
        
        # Reset the mock to clear any calls from initialization
        mock_read_csv.reset_mock()
        
        # Call the method explicitly
        client._load_station_data()
        
        # Verify read_csv was called twice
        self.assertEqual(mock_read_csv.call_count, 2)
        mock_read_csv.assert_any_call(cache_file)
        mock_read_csv.assert_any_call(routes_file)

    @patch('app.mta_client.requests.get')
    @patch('zipfile.ZipFile')
    @patch('pandas.read_csv')
    def test_load_station_data_from_api(self, mock_read_csv, mock_zipfile, mock_get):
        """Test loading station data from the API."""
        # First patch _load_station_data to prevent it from running during initialization
        with patch.object(MTAClient, '_load_station_data'):
            client = MTAClient(use_cache=False, verbose=False)
        
        # Set up the mock response BEFORE calling _load_station_data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'zip_content'
        mock_get.return_value = mock_response
        
        # Configure the zipfile mock
        mock_zipfile_instance = MagicMock()
        mock_zipfile_instance.open.side_effect = [MagicMock(), MagicMock()]
        mock_zipfile.return_value.__enter__.return_value = mock_zipfile_instance
        
        # Configure read_csv mock
        mock_read_csv.side_effect = [self.sample_stations, self.sample_routes]
        
        # Clear the stations and routes to force a reload
        client.stations = None
        client.routes = None
        
        # Now call the method after all mocks are configured
        client._load_station_data()
        
        # Verify requests.get was called with the correct URL
        mock_get.assert_called_once_with(client.GTFS_URL)

    def test_clean_station_name(self):
        """Test cleaning station names."""
        # Test various station name formats
        test_cases = [
            ('Times Sq-42 St (123)', 'Times Sq-42 St'),
            ('34 St-Penn Station (123)', '34 St-Penn Station'),
            ('Fulton St (JZ)', 'Fulton St'),
            ('Chambers St Uptown', 'Chambers St'),
            ('Brooklyn Bridge-City Hall Bound', 'Brooklyn Bridge-City Hall'),
            ('Times  Square   42 St Express', 'Times Square 42 St')
        ]
        
        for input_name, expected_output in test_cases:
            result = self.client.clean_station_name(input_name)
            self.assertEqual(result, expected_output)

    def test_find_stations_by_name(self):
        """Test finding stations by name."""
        # Test exact match
        result = self.client.find_stations_by_name('Times Sq-42 St (1)', exact=True)
        self.assertEqual(len(result), 2)  # Should find both N and S directions
        
        # Test partial match
        result = self.client.find_stations_by_name('Times')
        self.assertEqual(len(result), 2)
        
        # Test no match
        result = self.client.find_stations_by_name('NonexistentStation')
        self.assertTrue(result.empty)

    def test_find_stations_by_id(self):
        """Test finding stations by ID."""
        # Test finding by full ID
        result = self.client.find_stations_by_id('127N')
        self.assertEqual(len(result), 1)
        
        # Test finding by core ID (should find both directions)
        result = self.client.find_stations_by_id('127')
        self.assertEqual(len(result), 2)
        
        # Test no match
        result = self.client.find_stations_by_id('999')
        self.assertTrue(result.empty)

    def test_list_all_lines(self):
        """Test listing all subway lines."""
        # Call the method
        result = self.client.list_all_lines()
        
        # Verify result is a DataFrame with expected columns
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(list(result.columns), ['route_id', 'route_long_name', 'route_color'])
        
        # Verify all routes are included
        self.assertEqual(len(result), 4)

    @patch('app.mta_client.MTAClient.find_stations_by_name')
    @patch('app.mta_client.MTAClient.get_upcoming_trains')
    def test_get_station_arrivals(self, mock_get_trains, mock_find_stations):
        """Test the integrated get_station_arrivals method."""
        # Create mock station results
        station_results = pd.DataFrame({
            'core_id': ['127', '127'],
            'stop_id': ['127N', '127S'],
            'clean_name': ['Times Sq-42 St', 'Times Sq-42 St'],
            'direction': ['Northbound', 'Southbound']
        })
        mock_find_stations.return_value = station_results
        
        # Create mock train results
        train_results = pd.DataFrame({
            'route_id': ['1', '1'],
            'trip_id': ['trip1', 'trip2'],
            'arrival_time': [
                datetime.datetime.now(pytz.timezone('America/New_York')) + datetime.timedelta(minutes=5),
                datetime.datetime.now(pytz.timezone('America/New_York')) + datetime.timedelta(minutes=10)
            ],
            'stop_id': ['127N', '127N']
        })
        mock_get_trains.return_value = train_results
        
        # Call the method
        result = self.client.get_station_arrivals('Times Square', '1', 'N', 5)
        
        # Verify find_stations_by_name was called with the correct station name
        mock_find_stations.assert_called_once_with('Times Square')
        
        # Verify get_upcoming_trains was called with the correct parameters
        mock_get_trains.assert_called_once_with('1', '127', 'N', 5)
        
        # Verify result matches our mock train results
        pd.testing.assert_frame_equal(result, train_results)

    @patch('app.mta_client.MTAClient.find_stations_by_name')
    def test_get_station_arrivals_no_station(self, mock_find_stations):
        """Test get_station_arrivals when no station is found."""
        # Return empty DataFrame for station search
        mock_find_stations.return_value = pd.DataFrame()
        
        # Mock the get_upcoming_trains method to avoid API calls
        self.client.get_upcoming_trains = MagicMock()
        
        # Call the method with a station that won't be found
        result = self.client.get_station_arrivals('NonexistentStation', '1', 'N')
        
        # For a non-Times Square station, we should get an empty DataFrame
        self.assertTrue(result.empty)
        
        # Verify get_upcoming_trains was not called
        self.client.get_upcoming_trains.assert_not_called()
        
        # Test Times Square special case
        result = self.client.get_station_arrivals('Times Square', '1', 'N')
        
        # For Times Square, we should use hardcoded IDs
        self.client.get_upcoming_trains.assert_called_once_with('1', '127', 'N', 5)

if __name__ == '__main__':
    unittest.main()