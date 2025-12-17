#!/usr/bin/env python3
"""
Test script to verify events and RSVP functionality
Tests the complete flow: create event -> fetch events -> RSVP -> verify RSVP
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5000"  # Adjust if running on different port
AUTH_BASE_URL = f"{BASE_URL}/api/v1/auth"
API_BASE_URL = f"{BASE_URL}/api/v1"

def test_event_creation_and_fetching():
    """Test creating an event and fetching it"""
    print("🧪 Testing Event Creation and Fetching...")

    # Test data
    event_data = {
        "title": "Test Community Event",
        "description": "A test event for verification",
        "date": (datetime.now() + timedelta(days=7)).isoformat(),
        "location_address": "Test Location, Nairobi",
        "location": {
            "type": "Point",
            "coordinates": [36.817223, -1.286389]  # Nairobi coordinates
        }
    }

    # First, we need to authenticate as an organizer
    auth_data = {
        "email": "test@example.com",  # You'll need to create this user first
        "password": "testpassword"
    }

    try:
        # Login
        auth_response = requests.post(f"{AUTH_BASE_URL}/login", json=auth_data)
        if auth_response.status_code != 200:
            print("❌ Authentication failed. Trying to register test user...")
            register_data = {
                "email": "test@example.com",
                "password": "testpassword",
                "username": "testuser"
            }
            register_response = requests.post(f"{AUTH_BASE_URL}/register", json=register_data)
            if register_response.status_code != 201:
                print(f"❌ Registration failed: {register_response.status_code} - {register_response.text}")
                return False
            print("✅ Test user registered successfully")
            # Now try login again
            auth_response = requests.post(f"{AUTH_BASE_URL}/login", json=auth_data)
            if auth_response.status_code != 200:
                print("❌ Authentication failed after registration.")
                return False

        token = auth_response.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}

        # Create event
        create_response = requests.post(f"{API_BASE_URL}/events", json=event_data, headers=headers)
        if create_response.status_code != 201:
            print(f"❌ Event creation failed: {create_response.status_code} - {create_response.text}")
            return False

        event_result = create_response.json()
        event_id = event_result['event_id']
        print(f"✅ Event created successfully with ID: {event_id}")

        # Fetch events
        fetch_response = requests.get(f"{API_BASE_URL}/events", headers=headers)
        if fetch_response.status_code != 200:
            print(f"❌ Event fetching failed: {fetch_response.status_code}")
            return False

        events = fetch_response.json()['events']
        created_event = next((e for e in events if e['event_id'] == event_id), None)

        if not created_event:
            print("❌ Created event not found in fetched events")
            return False

        print(f"✅ Event fetched successfully: {created_event['title']}")
        return event_id

    except Exception as e:
        print(f"❌ Error in event creation/fetching: {e}")
        return False

def test_rsvp_flow(event_id, token):
    """Test RSVP functionality"""
    print("🧪 Testing RSVP Flow...")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        # RSVP to event
        rsvp_response = requests.post(f"{BASE_URL}/events/{event_id}/rsvp", headers=headers)
        if rsvp_response.status_code != 201:
            print(f"❌ RSVP failed: {rsvp_response.status_code} - {rsvp_response.text}")
            return False

        print("✅ RSVP submitted successfully")

        # Verify RSVP by checking event stats
        stats_response = requests.get(f"{BASE_URL}/events/{event_id}/stats", headers=headers)
        if stats_response.status_code != 200:
            print(f"❌ Stats fetch failed: {stats_response.status_code}")
            return False

        stats = stats_response.json()
        rsvp_count = stats.get('rsvp_count', 0)

        if rsvp_count < 1:
            print(f"❌ RSVP count not updated correctly: {rsvp_count}")
            return False

        print(f"✅ RSVP verified - Event has {rsvp_count} RSVPs")
        return True

    except Exception as e:
        print(f"❌ Error in RSVP flow: {e}")
        return False

def test_new_rsvp_endpoint(event_id, token):
    """Test the new RSVP endpoint"""
    print("🧪 Testing New RSVP Endpoint...")

    headers = {"Authorization": f"Bearer {token}"}
    rsvp_data = {"event_id": event_id}

    try:
        # Use new RSVP endpoint
        rsvp_response = requests.post(f"{API_BASE_URL}/rsvp/submit", json=rsvp_data, headers=headers)
        if rsvp_response.status_code not in [200, 201]:
            print(f"❌ New RSVP endpoint failed: {rsvp_response.status_code} - {rsvp_response.text}")
            return False

        result = rsvp_response.json()
        total_rsvps = result.get('total_rsvps', 0)

        print(f"✅ New RSVP endpoint works - Total RSVPs: {total_rsvps}")
        return True

    except Exception as e:
        print(f"❌ Error in new RSVP endpoint: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Events and RSVP Flow Verification")
    print("=" * 50)

    # Test event creation and fetching
    event_id = test_event_creation_and_fetching()
    if not event_id:
        print("❌ Event creation/fetching test failed")
        return

    # Get token for RSVP tests
    auth_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }

    auth_response = requests.post(f"{AUTH_BASE_URL}/login", json=auth_data)
    if auth_response.status_code != 200:
        print("❌ Could not get auth token for RSVP tests")
        return

    token = auth_response.json()['access_token']

    # Test RSVP flow
    if not test_rsvp_flow(event_id, token):
        print("❌ RSVP flow test failed")
        return

    # Test new RSVP endpoint
    if not test_new_rsvp_endpoint(event_id, token):
        print("❌ New RSVP endpoint test failed")
        return

    print("=" * 50)
    print("🎉 All tests passed! Events and RSVP functionality is working correctly.")

if __name__ == "__main__":
    main()
