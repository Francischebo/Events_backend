import pytest
from uuid import uuid4
from extensions import mongo


def unique_user(role='attendee'):
    suffix = str(uuid4())[:8]
    return {
        'username': f'py_{role}_{suffix}',
        'email': f'py_{role}_{suffix}@example.com',
        'password': 'TestPass!234',
        'role': role
    }


def teardown_user_by_email(email):
    try:
        mongo.db.users.delete_one({'email': email})
    except Exception:
        pass


def teardown_event(event_id):
    try:
        from bson import ObjectId
        mongo.db.events.delete_one({'_id': ObjectId(event_id)})
        mongo.db.activities.delete_many({'event_id': ObjectId(event_id)})
    except Exception:
        pass


def test_event_create_rsvp_and_feed(client):
    # Create organizer and login
    org_payload = unique_user(role='organizer')
    teardown_user_by_email(org_payload['email'])
    r = client.post('/api/v1/auth/register', json=org_payload)
    assert r.status_code == 201
    token_org = r.get_json()['access_token']

    # Create an event as organizer
    event_data = {
        'title': 'PyTest Event',
        'description': 'Event created in pytest',
        'date': '2025-12-31T12:00:00Z',
        'location_address': 'Testville',
        'location': {'type': 'Point', 'coordinates': [0.0, 0.0]}
    }
    headers = {'Authorization': f'Bearer {token_org}'}
    r2 = client.post('/api/v1/events', json=event_data, headers=headers)
    assert r2.status_code == 201
    event_id = r2.get_json()['event_id']

    # Create attendee and login
    att_payload = unique_user(role='attendee')
    teardown_user_by_email(att_payload['email'])
    r3 = client.post('/api/v1/auth/register', json=att_payload)
    assert r3.status_code == 201
    token_att = r3.get_json()['access_token']

    # RSVP to event as attendee
    headers_att = {'Authorization': f'Bearer {token_att}'}
    r4 = client.post(f'/api/v1/events/{event_id}/rsvp', headers=headers_att)
    assert r4.status_code in (200, 201)

    # Fetch feed as attendee - should include RSVP activity
    r5 = client.get('/api/v1/feed', headers=headers_att)
    assert r5.status_code == 200
    feed = r5.get_json().get('feed', [])
    assert any(item.get('type') == 'RSVP' and item.get('event_id') == event_id for item in feed)

    # Cleanup
    teardown_event(event_id)
    teardown_user_by_email(org_payload['email'])
    teardown_user_by_email(att_payload['email'])
