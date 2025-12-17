# app.py - Corrected Flask + PyMongo + Socket.IO setup
import os
import json
import threading
import time
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from pymongo import MongoClient, errors
import firebase_admin
from firebase_admin import credentials

from extensions import mongo, jwt, socketio, bcrypt
from routes import register_blueprints
from websocket_handlers import register_socketio_handlers
from config import DevelopmentConfig, ProductionConfig, TestingConfig
from dotenv import load_dotenv

# Load environment variables from .env if exists
load_dotenv()

def create_app(config_name=None):
    """Application factory"""
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig
    }
    app.config.from_object(config_map.get(config_name, DevelopmentConfig))

    # --- Initialize Firebase if key is provided ---
    if not firebase_admin._apps:
        key_path = app.config.get("FIREBASE_SERVICE_ACCOUNT_KEY")
        if key_path:
            try:
                if os.path.exists(key_path):
                    cred = credentials.Certificate(key_path)
                    firebase_admin.initialize_app(cred)
                else:
                    key_dict = json.loads(key_path)
                    cred = credentials.Certificate(key_dict)
                    firebase_admin.initialize_app(cred)
            except Exception as e:
                app.logger.error(f"Failed to initialize Firebase: {e}")
        else:
            app.logger.info("No Firebase key provided; skipping Firebase initialization.")

    # --- MongoDB connection ---
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable not set.")

    app.config["MONGO_URI"] = mongo_uri
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        # Test connection
        client.admin.command('ping')
        app.logger.info("MongoDB connection successful.")
    except errors.ServerSelectionTimeoutError as e:
        app.logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

    mongo.init_app(app)

    # --- Extensions ---
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    jwt.init_app(app)
    bcrypt.init_app(app)

    # --- Socket.IO ---
    timeout_ms = int(app.config.get("REQUEST_TIMEOUT_MS", 10000))
    socketio.init_app(app, cors_allowed_origins="*", ping_timeout=max(1, timeout_ms / 1000.0), async_mode='threading')

    # --- Blueprints & WebSocket handlers ---
    register_blueprints(app)
    register_socketio_handlers(socketio)

    # --- Database indexes ---
    def _ensure_indexes():
        try:
            db = mongo.db
            # Users
            db.users.create_index("email", unique=True)
            db.users.create_index("username", unique=True)
            db.users.create_index("firebase_uid", sparse=True, unique=True)
            # Events
            db.events.create_index([("location", "2dsphere")])
            db.events.create_index("organizer_id")
            db.events.create_index("date")
            # Messages
            db.messages.create_index([("event_id", 1), ("timestamp", -1)])
            # Activities
            db.activities.create_index([("actor_id", 1), ("timestamp", -1)])
            db.activities.create_index("timestamp")
            app.logger.info("Database indexes ensured successfully.")
        except Exception as e:
            app.logger.error(f"Failed to create indexes: {e}")

    threading.Thread(target=_ensure_indexes, daemon=True).start()

    return app


if __name__ == "__main__":
    app = create_app()
    bind_host = os.environ.get("BIND_HOST", app.config.get("BIND_HOST", "0.0.0.0"))
    bind_port = int(os.environ.get("PORT", app.config.get("PORT", 5000)))
    app.logger.info(f"Starting server on {bind_host}:{bind_port}")
    socketio.run(app, host=bind_host, port=bind_port, debug=app.debug, use_reloader=False)
