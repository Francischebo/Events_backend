import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extensions import mongo
from config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
mongo.init_app(app)

with app.app_context():
    result = mongo.db.users.delete_one({"email": "test@example.com"})
    if result.deleted_count > 0:
        print("User deleted successfully")
    else:
        print("User not found")
