from uuid import uuid4
from bson import ObjectId


def unique_payload(role='attendee'):
    suffix = str(uuid4())[:8]
    return {
        'username': f'py_{role}_{suffix}',
        'email': f'py_{role}_{suffix}@example.com',
        'password': 'TestPass!234',
        'role': role
    }


def teardown_user(mongo, email):
    try:
        mongo.db.users.delete_one({'email': email})
    except Exception:
        pass


def teardown_event(mongo, event_id):
    try:
        mongo.db.events.delete_one({'_id': ObjectId(event_id)})
        mongo.db.activities.delete_many({'event_id': ObjectId(event_id)})
        mongo.db.messages.delete_many({'event_id': ObjectId(event_id)})
    except Exception:
        pass


def register_and_get_token(client, payload):
    r = client.post('/api/v1/auth/register', json=payload)
    assert r.status_code == 201
    return r.get_json()['access_token'], r.get_json()['user']


def test_arrival_and_stats(client):
    mongo = __import__('extensions').mongo

    # Register organizer
    org = unique_payload('organizer')
    teardown_user(mongo, org['email'])
    token_org, org_user = register_and_get_token(client, org)
    headers_org = {'Authorization': f'Bearer {token_org}'}

    # Register attendee
    att = unique_payload('attendee')
    teardown_user(mongo, att['email'])
    token_att, att_user = register_and_get_token(client, att)
    headers_att = {'Authorization': f'Bearer {token_att}'}

    # Create event
    event_payload = {
        'title': 'Arrival Stats Test Event',
        'description': 'Testing arrivals and stats',
        'date': '2025-12-31T12:00:00Z',
        'location_address': 'Testville',
        'location': {'type': 'Point', 'coordinates': [0.0, 0.0]}
    }
    ev_resp = client.post('/api/v1/events', json=event_payload, headers=headers_org)
    assert ev_resp.status_code == 201
    event_id = ev_resp.get_json()['event_id']

    try:
        # Attendee RSVPs
        rsvp_resp = client.post(f'/api/v1/events/{event_id}/rsvp', headers=headers_att, json={'username': att_user['username']})
        assert rsvp_resp.status_code in (200, 201)

        # Attendee records arrival
        arrival_resp = client.post(f'/api/v1/events/{event_id}/arrival', headers=headers_att)
        assert arrival_resp.status_code == 200

        # Organizer fetches stats
        stats_resp = client.get(f'/api/v1/events/{event_id}/stats', headers=headers_org)
        assert stats_resp.status_code == 200
        stats = stats_resp.get_json()
        assert stats.get('rsvp_count', 0) >= 1
        assert stats.get('arrival_count', 0) >= 1

    finally:
        # Cleanup: delete event and users
        teardown_event(mongo, event_id)
        teardown_user(mongo, org['email'])
        teardown_user(mongo, att['email'])
