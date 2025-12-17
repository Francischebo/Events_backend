# app.py
import ssl
import os
import json
import certifi
import threading
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from pymongo import MongoClient, errors
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

from extensions import mongo, jwt, socketio, bcrypt
from routes import register_blueprints
from websocket_handlers import register_socketio_handlers
from config import DevelopmentConfig, ProductionConfig, TestingConfig

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")

def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "production")

    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig
    }
    app.config.from_object(config_map.get(config_name, ProductionConfig))

    # Firebase
    if not firebase_admin._apps:
        key_path = app.config.get("FIREBASE_SERVICE_ACCOUNT_KEY")
        if key_path:
            try:
                if os.path.exists(key_path):
                    cred = credentials.Certificate(key_path)
                else:
                    cred = credentials.Certificate(json.loads(key_path))
                firebase_admin.initialize_app(cred)
            except Exception as e:
                app.logger.error(f"Firebase init failed: {e}")

    # MongoDB
    app.config["MONGO_URI"] = os.getenv("MONGODB_URI")
    mongo.init_app(app)

    # Extensions
    CORS(app)
    jwt.init_app(app)
    bcrypt.init_app(app)

    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="threading"
    )

    register_blueprints(app)
    register_socketio_handlers(socketio)

    with app.app_context():
        try:
            mongo.db.users.create_index("email", unique=True)
            mongo.db.users.create_index("username", unique=True)
            mongo.db.events.create_index([("location", "2dsphere")])
            app.logger.info("Indexes created successfully")
        except Exception as e:
            app.logger.error(f"Index creation failed: {e}")

    return app
app = create_app()

if __name__ == "__main__":
    app = create_app()
    bind_host = os.environ.get("BIND_HOST", app.config.get("BIND_HOST", "0.0.0.0"))
    bind_port = int(os.environ.get("PORT", app.config.get("PORT", 8080)))
    app.logger.info(f"Starting server on {bind_host}:{bind_port}")
    socketio.run(
        app,
        host=bind_host,
        port=bind_port,
        debug=app.debug,
        use_reloader=False
    )
