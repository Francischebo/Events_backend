# utils/geolocation.py - Geolocation and Distance Calculation
from extensions import mongo
from math import radians, cos, sin, asin, sqrt

def calculate_distance(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def find_nearby_events(latitude, longitude, radius_km, additional_query=None):
    """
    Find events near a given location using MongoDB geospatial queries
    
    Args:
        latitude: User's latitude
        longitude: User's longitude
        radius_km: Search radius in kilometers
        additional_query: Optional additional MongoDB query filters
    
    Returns:
        List of events with distance information
    """
    # Convert km to meters for MongoDB
    radius_meters = radius_km * 1000
    
    # Build geospatial query
    geo_query = {
        'location': {
            '$near': {
                '$geometry': {
                    'type': 'Point',
                    'coordinates': [longitude, latitude]
                },
                '$maxDistance': radius_meters
            }
        }
    }
    
    # Merge with additional query filters if provided
    if additional_query:
        geo_query.update(additional_query)
    
    # Execute query
    events_cursor = mongo.db.events.find(geo_query).limit(50)
    
    events = []
    for event in events_cursor:
        # Calculate distance
        event_lon, event_lat = event['location']['coordinates']
        distance = calculate_distance(longitude, latitude, event_lon, event_lat)
        
        # Format event data
        event_data = {
            'event_id': str(event['_id']),
            'title': event['title'],
            'description': event['description'],
            'date': event['date'].isoformat(),
            'category': event.get('category', 'General'),
            'location_address': event['location_address'],
            'location': event['location'],
            'organizer_id': str(event['organizer_id']),
            'distance_km': round(distance, 2),
            'geofence_radius': event.get('geofence_radius', 200)
        }
        
        events.append(event_data)
    
    # Sort by distance
    events.sort(key=lambda x: x['distance_km'])
    
    return events

def is_within_geofence(user_lat, user_lon, event_lat, event_lon, radius_meters):
    """
    Check if user is within the geofence radius of an event
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        event_lat: Event's latitude
        event_lon: Event's longitude
        radius_meters: Geofence radius in meters
    
    Returns:
        Boolean indicating if user is within geofence
    """
    distance_km = calculate_distance(user_lon, user_lat, event_lon, event_lat)
    distance_meters = distance_km * 1000
    return distance_meters <= radius_meters