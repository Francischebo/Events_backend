#!/usr/bin/env python3
"""
Test script to verify API endpoints work correctly for frontend integration
"""

import requests
import json
import time
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:5000/api/v1"

def test_register():
    """Test user registration"""
    print("Testing user registration...")
    url = f"{BASE_URL}/auth/register"
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "role": "attendee"
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 201:
            result = response.json()
            print("✓ Registration successful")
            return result.get('access_token')
        else:
            print(f"✗ Registration failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Registration error: {e}")
        return None

def test_login():
    """Test user login"""
    print("Testing user login...")
    url = f"{BASE_URL}/auth/login"
    data = {
        "email": "test@example.com",
        "password": "password123"
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print("✓ Login successful")
            return result.get('access_token')
        else:
            print(f"✗ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Login error: {e}")
        return None

def test_get_user_profile(token):
    """Test getting user profile"""
    print("Testing get user profile...")
    url = f"{BASE_URL}/auth/user/me"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print("✓ Get user profile successful")
            return result
        else:
            print(f"✗ Get user profile failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Get user profile error: {e}")
        return None

def test_create_event(token):
    """Test creating an event"""
    print("Testing event creation...")
    url = f"{BASE_URL}/events"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "title": "Test Event",
        "description": "This is a test event",
        "date": datetime.now(timezone.utc).isoformat(),
        "location_address": "Test Location",
        "location": {
            "type": "Point",
            "coordinates": [0.0, 0.0]
        }
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            result = response.json()
            print("✓ Event creation successful")
            return result.get('event_id')
        else:
            print(f"✗ Event creation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Event creation error: {e}")
        return None

def test_get_events(token):
    """Test getting events"""
    print("Testing get events...")
    url = f"{BASE_URL}/events"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            events = result.get('events', [])
            print(f"✓ Get events successful - found {len(events)} events")
            return events
        else:
            print(f"✗ Get events failed: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"✗ Get events error: {e}")
        return []

def test_rsvp_to_event(token, event_id):
    """Test RSVPing to an event"""
    print("Testing RSVP to event...")
    url = f"{BASE_URL}/events/{event_id}/rsvp"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"username": "testuser"}
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code in [200, 201]:
            print("✓ RSVP successful")
            return True
        else:
            print(f"✗ RSVP failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ RSVP error: {e}")
        return False

def test_get_activity_feed(token):
    """Test getting activity feed"""
    print("Testing get activity feed...")
    url = f"{BASE_URL}/feed"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            feed = result.get('feed', [])
            print(f"✓ Get activity feed successful - found {len(feed)} items")
            return feed
        else:
            print(f"✗ Get activity feed failed: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"✗ Get activity feed error: {e}")
        return []

def test_update_user_location(token):
    """Test updating user location"""
    print("Testing update user location...")
    url = f"{BASE_URL}/auth/user/location"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"lat": 40.7128, "lon": -74.0060}  # New York coordinates
    try:
        response = requests.put(url, json=data, headers=headers)
        if response.status_code == 200:
            print("✓ Update user location successful")
            return True
        else:
            print(f"✗ Update user location failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Update user location error: {e}")
        return False

def test_location_share(token, event_id):
    """Test location sharing for event"""
    print("Testing location share...")
    url = f"{BASE_URL}/events/{event_id}/location/share"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"lat": 40.7128, "lon": -74.0060}
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print("✓ Location share successful")
            return True
        else:
            print(f"✗ Location share failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Location share error: {e}")
        return False

def main():
    """Run all API endpoint tests"""
    print("Starting API endpoint tests for frontend integration...\n")

    # Wait a moment for server to start
    time.sleep(2)

    # Test authentication flow
    token = test_register()
    if not token:
        token = test_login()

    if not token:
        print("❌ Cannot proceed without authentication token")
        return False

    # Test authenticated endpoints
    user_profile = test_get_user_profile(token)
    event_id = test_create_event(token)
    events = test_get_events(token)

    if event_id:
        test_rsvp_to_event(token, event_id)
        test_location_share(token, event_id)

    test_get_activity_feed(token)
    test_update_user_location(token)

    print("\n🎉 API endpoint tests completed!")
    return True

if __name__ == "__main__":
    main()
