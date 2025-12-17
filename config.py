# config.py - Application Configuration
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # MongoDB URI (read from environment)
    MONGO_URI = os.environ.get('MONGO_URI')
    MONGO_DBNAME = os.environ.get('MONGO_DBNAME') or 'event_management'

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or './uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Firebase
    FIREBASE_SERVICE_ACCOUNT_KEY = os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY')

    # Email config
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Geofencing
    DEFAULT_GEOFENCE_RADIUS = 200
    REQUEST_TIMEOUT_MS = int(os.environ.get('REQUEST_TIMEOUT_MS') or 5000)


class DevelopmentConfig(Config):
    DEBUG = True
    FIREBASE_SERVICE_ACCOUNT_KEY = None  # Disable Firebase locally
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/event_management'


class ProductionConfig(Config):
    DEBUG = False
    # Must provide Atlas URI in environment
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb+srv://francischeboo404_db_user:Fr%40m0ng00se387623@communityapp.ktglocw.mongodb.net/event_management?retryWrites=true&w=majority&ssl=true'


class TestingConfig(Config):
    TESTING = True
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/event_management'
