#!/usr/bin/env python3
"""
Database validation script for event management system
Tests MongoDB connection, user operations, and authentication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extensions import mongo, bcrypt
from models.user import User
from config import Config
from flask import Flask
from flask_pymongo import PyMongo
import pymongo
import re

def test_database_connection():
    """Test MongoDB connection"""
    print("Testing MongoDB connection...")
    try:
        # Test connection
        client = pymongo.MongoClient(Config.MONGO_URI, ssl=True)
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

def test_database_operations():
    """Test basic database operations"""
    print("\nTesting database operations...")

    # Create Flask app context for testing
    app = Flask(__name__)
    app.config.from_object(Config)
    # Ensure MONGO_URI contains a database name; some Atlas URIs used here include no DB path
    # Flask-PyMongo will not expose `mongo.db` if the URI lacks a default database.
    uri = app.config.get('MONGO_URI', '')
    if uri and re.search(r'/\?$', uri):
        # replace '/?' with '/<dbname>?'
        app.config['MONGO_URI'] = uri.replace('/?', '/event_management?')
    elif uri and re.search(r'mongodb(\+srv)?:\/\/[^\/\?]+$', uri):
        # append '/event_management' when no path/query present
        app.config['MONGO_URI'] = uri + '/event_management'

    # DEBUG: show final MONGO_URI used by Flask app
    print(f"DEBUG: app.config['MONGO_URI'] = {app.config.get('MONGO_URI')}")

    mongo.init_app(app)
    bcrypt.init_app(app)

    with app.app_context():
        try:
            # Test user collection access
            db = mongo.db
            if db is None:
                print("❌ Database object is None")
                return False

            # Test user operations
            print("Testing user operations...")

            # Create test user
            test_user = User(
                username="testuser",
                email="test@example.com",
                password="password123",
                role="attendee"
            )

            # Save user
            user_id = test_user.save()
            print(f"✅ User created with ID: {user_id}")

            # Find user by email
            found_user = User.find_by_email("test@example.com")
            if found_user:
                print("✅ User found by email")
            else:
                print("❌ User not found by email")
                return False

            # Find user by ID
            found_user_by_id = User.find_by_id(str(user_id))
            if found_user_by_id:
                print("✅ User found by ID")
            else:
                print("❌ User not found by ID")
                return False

            # Clean up - delete test user
            db.users.delete_one({"_id": user_id})
            print("✅ Test user cleaned up")

            print("✅ All database operations successful")
            return True

        except Exception as e:
            print(f"❌ Database operations failed: {e}")
            return False

def test_authentication_flow():
    """Test authentication flow"""
    print("\nTesting authentication flow...")

    app = Flask(__name__)
    app.config.from_object(Config)
    mongo.init_app(app)
    bcrypt.init_app(app)

    with app.app_context():
        try:
            # Create test user
            test_user = User(
                username="auth_test",
                email="auth@example.com",
                password="authpass123",
                role="attendee"
            )
            user_id = test_user.save()

            # Test password verification
            stored_user = User.find_by_email("auth@example.com")
            if stored_user and bcrypt.check_password_hash(stored_user['password_hash'], "authpass123"):
                print("✅ Password verification successful")
            else:
                print("❌ Password verification failed")
                return False

            # Clean up
            mongo.db.users.delete_one({"_id": user_id})
            print("✅ Authentication flow test completed")
            return True

        except Exception as e:
            print(f"❌ Authentication flow test failed: {e}")
            return False

def main():
    """Run all database tests"""
    print("🧪 Starting database validation tests...\n")

    # Test connection
    if not test_database_connection():
        print("\n❌ Database connection test failed. Please ensure MongoDB is running.")
        return False

    # Test operations
    if not test_database_operations():
        print("\n❌ Database operations test failed.")
        return False

    # Test authentication
    if not test_authentication_flow():
        print("\n❌ Authentication flow test failed.")
        return False

    print("\n🎉 All database tests passed! The database is correctly configured and working.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
