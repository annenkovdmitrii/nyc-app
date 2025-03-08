from lib.mta.mta_client import MTAClient
import pytz
from datetime import datetime


# Example usage
if __name__ == "__main__":
    # Initialize the integrated client
    client = MTAClient(verbose=True)
    
    # Example: Find Times Square station
    stations = client.find_stations_by_name("Times Square")
    print("\nTimes Square stations:")
    print(stations.to_string(index=False))
    
    # If not found, try a more specific search
    if stations.empty:
        print("\nTrying more specific search:")
        stations = client.find_stations_by_name("42 St-Times")
        print(stations.to_string(index=False))
    
    # Example: Get upcoming trains at Times Square
    if not stations.empty:
        station_id = stations.iloc[0]['core_id']
        line = '1'  # 1 train
        direction = 'N'  # Northbound
        
        print(f"\nUpcoming {line} trains at Times Square ({direction}bound):")
        upcoming = client.get_upcoming_trains(line, station_id, direction)
        
        if not upcoming.empty:
            for _, train in upcoming.iterrows():
                now = datetime.now(pytz.timezone('America/New_York'))
                minutes = int((train['arrival_time'] - now).total_seconds() / 60)
                print(f"Train {train['trip_id']} arriving in {minutes} minutes at {train['arrival_time'].strftime('%I:%M %p')}")
        else:
            print("No upcoming trains found")
    else:
        # Hardcoded approach for Times Square if not found
        line = '1'  # 1 train
        station_id = '127'  # Known ID for Times Square
        direction = 'N'  # Northbound
        
        print(f"\nUsing hardcoded approach - Upcoming {line} trains at Times Square ({direction}bound):")
        upcoming = client.get_upcoming_trains(line, station_id, direction)
        
        if not upcoming.empty:
            for _, train in upcoming.iterrows():
                now = datetime.now(pytz.timezone('America/New_York'))
                minutes = int((train['arrival_time'] - now).total_seconds() / 60)
                print(f"Train {train['trip_id']} arriving in {minutes} minutes at {train['arrival_time'].strftime('%I:%M %p')}")
        else:
            print("No upcoming trains found")
    
    # Example: One-stop method to get arrivals by station name
    print("\nUsing one-stop method:")
    arrivals = client.get_station_arrivals("Times Square", "1", "N")
    if not arrivals.empty:
        for _, train in arrivals.iterrows():
            now = datetime.now(pytz.timezone('America/New_York'))
            minutes = int((train['arrival_time'] - now).total_seconds() / 60)
            print(f"Train {train['trip_id']} arriving in {minutes} minutes at {train['arrival_time'].strftime('%I:%M %p')}")