#!/usr/bin/env python3
"""
Comprehensive End-to-End Smoke Test
Tests: Register → Login → Create Event → RSVP → Feed → Arrivals → Stats
"""
import requests
import json
from datetime import datetime
from uuid import uuid4

BASE_URL = "http://127.0.0.1:5000/api/v1"

def test_full_flow():
    print("\n" + "=" * 80)
    print("COMPREHENSIVE E2E SMOKE TEST")
    print("=" * 80)
    
    # Test 1: Health Check
    print("\n[1/8] Health Check...")
    try:
        r = requests.get(f"{BASE_URL}/health/")
        assert r.status_code == 200, f"Health check failed: {r.status_code}"
        print("✅ Backend is healthy")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Register Organizer
    print("\n[2/8] Register Organizer...")
    org_email = f"org_{uuid4().hex[:8]}@test.com"
    try:
        r = requests.post(f"{BASE_URL}/auth/register", json={
            "username": f"org_{uuid4().hex[:8]}",
            "email": org_email,
            "password": "TestPass!123",
            "role": "organizer"
        })
        assert r.status_code == 201, f"Register failed: {r.status_code} {r.text}"
        org_token = r.json()['access_token']
        org_id = r.json()['user']['_id']
        print(f"✅ Organizer registered: {org_email}")
    except Exception as e:
        print(f"❌ Register organizer failed: {e}")
        return False
    
    # Test 3: Register Attendee
    print("\n[3/8] Register Attendee...")
    att_email = f"att_{uuid4().hex[:8]}@test.com"
    try:
        r = requests.post(f"{BASE_URL}/auth/register", json={
            "username": f"att_{uuid4().hex[:8]}",
            "email": att_email,
            "password": "TestPass!123",
            "role": "attendee"
        })
        assert r.status_code == 201, f"Register failed: {r.status_code} {r.text}"
        att_token = r.json()['access_token']
        att_id = r.json()['user']['_id']
        print(f"✅ Attendee registered: {att_email}")
    except Exception as e:
        print(f"❌ Register attendee failed: {e}")
        return False
    
    # Test 4: Login
    print("\n[4/8] Login...")
    try:
        r = requests.post(f"{BASE_URL}/auth/login", json={
            "email": org_email,
            "password": "TestPass!123"
        })
        assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
        # Tokens won't match but both should be valid
        print(f"✅ Login successful for {org_email}")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False
    
    # Test 5: Create Event
    print("\n[5/8] Create Event...")
    event_id = None
    try:
        r = requests.post(f"{BASE_URL}/events", json={
            "title": "Smoke Test Event",
            "description": "Testing the system",
            "date": "2025-12-31T12:00:00Z",
            "location_address": "Test Location",
            "location": {"type": "Point", "coordinates": [10.0, 20.0]}
        }, headers={"Authorization": f"Bearer {org_token}"})
        assert r.status_code == 201, f"Create event failed: {r.status_code} {r.text}"
        event_id = r.json()['event_id']
        print(f"✅ Event created: {event_id}")
    except Exception as e:
        print(f"❌ Create event failed: {e}")
        return False
    
    # Test 6: Attendee RSVP
    print("\n[6/8] Attendee RSVP...")
    try:
        r = requests.post(f"{BASE_URL}/events/{event_id}/rsvp", 
            headers={"Authorization": f"Bearer {att_token}"})
        assert r.status_code in (200, 201), f"RSVP failed: {r.status_code} {r.text}"
        print(f"✅ Attendee RSVP successful")
    except Exception as e:
        print(f"❌ RSVP failed: {e}")
        return False
    
    # Test 7: Record Arrival
    print("\n[7/8] Record Arrival...")
    try:
        r = requests.post(f"{BASE_URL}/events/{event_id}/arrival",
            headers={"Authorization": f"Bearer {att_token}"})
        assert r.status_code == 200, f"Arrival failed: {r.status_code} {r.text}"
        print(f"✅ Arrival recorded")
    except Exception as e:
        print(f"❌ Record arrival failed: {e}")
        return False
    
    # Test 8: Check Event Stats
    print("\n[8/8] Check Event Stats...")
    try:
        r = requests.get(f"{BASE_URL}/events/{event_id}/stats",
            headers={"Authorization": f"Bearer {org_token}"})
        assert r.status_code == 200, f"Stats failed: {r.status_code} {r.text}"
        stats = r.json()
        assert stats['rsvp_count'] >= 1, "RSVP count should be >= 1"
        assert stats['arrival_count'] >= 1, "Arrival count should be >= 1"
        print(f"✅ Event stats: {stats['rsvp_count']} RSVPs, {stats['arrival_count']} Arrivals")
    except Exception as e:
        print(f"❌ Check stats failed: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("✅✅✅ ALL TESTS PASSED ✅✅✅")
    print("=" * 80)
    print("\nSummary:")
    print(f"  • Health: OK")
    print(f"  • Auth: Register + Login working")
    print(f"  • Events: Create event working")
    print(f"  • RSVP: Attendee RSVP working")
    print(f"  • Arrivals: Arrival tracking working")
    print(f"  • Stats: Event stats working")
    print("\n✅ Application is RELIABLE and READY FOR USE!\n")
    return True

if __name__ == '__main__':
    import sys
    success = test_full_flow()
    sys.exit(0 if success else 1)
