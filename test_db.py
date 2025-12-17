from flask import Flask
from flask_pymongo import PyMongo
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
mongo = PyMongo(app)

with app.app_context():
    try:
        db = mongo.db
        print(f"Connected to database: {db}")
        print(f"Database name: {db.name}")
        # Test if we can access collections
        users = db.users
        print(f"Users collection: {users}")
    except Exception as e:
        print(f"Error: {e}")
