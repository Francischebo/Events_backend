# models/event.py - Event Model
from extensions import mongo
from datetime import datetime

class Event:
    """Event model for database operations"""
    
    def __init__(self, title, description, date, location_address, location, 
                 organizer_id, category='General', geofence_radius=200):
        self.title = title
        self.description = description
        self.date = date
        self.category = category
        self.location_address = location_address
        self.location = location
        self.organizer_id = organizer_id
        self.rsvps = []
        self.arrivals = []
        self.photo_gallery = []
        self.geofence_radius = geofence_radius
        self.created_at = datetime.utcnow()
    
    def save(self):
        """Save event to database"""
        event_data = {
            'title': self.title,
            'description': self.description,
            'date': self.date,
            'category': self.category,
            'location_address': self.location_address,
            'location': self.location,
            'organizer_id': self.organizer_id,
            'rsvps': self.rsvps,
            'arrivals': self.arrivals,
            'photo_gallery': self.photo_gallery,
            'geofence_radius': self.geofence_radius,
            'created_at': self.created_at
        }
        
        result = mongo.db.events.insert_one(event_data)
        return result.inserted_id
    
    @staticmethod
    def find_by_id(event_id):
        """Find event by ID"""
        from bson import ObjectId
        return mongo.db.events.find_one({'_id': ObjectId(event_id)})