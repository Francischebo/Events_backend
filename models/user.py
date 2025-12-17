# models/user.py - User Model
from extensions import mongo, bcrypt
from datetime import datetime

class User:
    """User model for database operations"""

    def __init__(self, username, email, password, role='attendee', firebase_uid=None, photo_url=None):
        if not password and not firebase_uid:
            raise ValueError("Password is required for non-Firebase users")
        self.username = username
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8') if password else None
        self.role = role
        self.firebase_uid = firebase_uid
        self.photo_url = photo_url
        self.following = []
        self.followers = []
        self.created_events = []
        self.rsvped_events = []
        self.created_at = datetime.utcnow()

    def save(self):
        """Save user to database"""
        user_data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role,
            'firebase_uid': self.firebase_uid,
            'photo_url': self.photo_url,
            'following': self.following,
            'followers': self.followers,
            'created_events': self.created_events,
            'rsvped_events': self.rsvped_events,
            'created_at': self.created_at
        }

        result = mongo.db.users.insert_one(user_data)
        return result.inserted_id

    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        return mongo.db.users.find_one({'email': email})

    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        from bson import ObjectId
        return mongo.db.users.find_one({'_id': ObjectId(user_id)})

    @staticmethod
    def find_by_firebase_uid(firebase_uid):
        """Find user by Firebase UID"""
        return mongo.db.users.find_one({'firebase_uid': firebase_uid})
