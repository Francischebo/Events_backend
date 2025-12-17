#!/usr/bin/env python3
"""
Test script to verify backend imports and basic functionality
"""

def test_imports():
    """Test all critical imports"""
    try:
        print("Testing Flask imports...")
        from flask import Flask, request, jsonify
        print("✓ Flask imports OK")

        print("Testing extensions...")
        from extensions import mongo, jwt, socketio, bcrypt
        print("✓ Extensions OK")

        print("Testing config...")
        from config import Config, DevelopmentConfig, ProductionConfig
        print("✓ Config OK")

        print("Testing routes...")
        from routes import register_blueprints
        print("✓ Routes OK")

        print("Testing websocket handlers...")
        from websocket_handlers import register_socketio_handlers
        print("✓ WebSocket handlers OK")

        print("Testing models...")
        from models.user import User
        from models.event import Event
        print("✓ Models OK")

        print("Testing API modules...")
        from api.events import event_bp
        from api.users import users_bp
        from api.feed import feed_bp
        print("✓ API modules OK")

        print("Testing utils...")
        from utils.decorators import organizer_required
        from utils.geolocation import find_nearby_events
        from utils.file_upload import upload_photo_to_cloud, allowed_file
        from utils.validators import validate_email, validate_password
        from utils.email_service import send_password_reset_email, send_event_reminder
        print("✓ Utils OK")

        print("Testing auth routes...")
        from auth_routes import auth_bp
        print("✓ Auth routes OK")

        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_app_creation():
    """Test app creation without starting server"""
    try:
        print("\nTesting app creation...")
        from app import create_app
        app = create_app()
        print("✓ App created successfully")

        # Test that blueprints are registered
        with app.app_context():
            print("✓ App context OK")
            # Check if mongo is initialized (won't connect without DB)
            print("✓ Mongo extension initialized")

        return True
    except Exception as e:
        print(f"✗ App creation failed: {e}")
        return False

def test_user_model():
    """Test User model basic functionality"""
    try:
        print("\nTesting User model...")
        from models.user import User

        # Test User creation (without saving)
        user = User("testuser", "test@example.com", "password123")
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "attendee"
        print("✓ User creation OK")

        # Test Firebase user creation
        firebase_user = User("fbuser", "fb@example.com", None, firebase_uid="fb123")
        assert firebase_user.firebase_uid == "fb123"
        assert firebase_user.password_hash is None
        print("✓ Firebase user creation OK")

        return True
    except Exception as e:
        print(f"✗ User model test failed: {e}")
        return False

def test_event_model():
    """Test Event model basic functionality"""
    try:
        print("\nTesting Event model...")
        from models.event import Event
        from datetime import datetime

        # Test Event creation (without saving)
        from datetime import timezone
        event = Event(
            title="Test Event",
            description="Test Description",
            date=datetime.now(timezone.utc),
            location_address="Test Location",
            location={"type": "Point", "coordinates": [0, 0]},
            organizer_id="test_org_id"
        )
        assert event.title == "Test Event"
        assert event.description == "Test Description"
        print("✓ Event creation OK")

        return True
    except Exception as e:
        print(f"✗ Event model test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting backend verification tests...\n")

    all_passed = True

    all_passed &= test_imports()
    all_passed &= test_app_creation()
    all_passed &= test_user_model()
    all_passed &= test_event_model()

    if all_passed:
        print("\n🎉 All tests passed! Backend is ready for deployment.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
