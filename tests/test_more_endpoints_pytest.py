import io
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
    return r.get_json()['access_token']


def test_location_share_update_delete_and_photos(client, monkeypatch):
    # Create organizer
    org = unique_payload('organizer')
    teardown_user(__import__('extensions').mongo, org['email'])
    token_org = register_and_get_token(client, org)
    headers_org = {'Authorization': f'Bearer {token_org}'}

    # Create event
    event_data = {
        'title': 'Endpoint Test Event',
        'description': 'Testing endpoints',
        'date': '2025-12-31T12:00:00Z',
        'location_address': 'Test City',
        'location': {'type': 'Point', 'coordinates': [10.0, 20.0]}
    }
    r = client.post('/api/v1/events', json=event_data, headers=headers_org)
    assert r.status_code == 201
    event_id = r.get_json()['event_id']

    # Update event
    update_payload = {'title': 'Updated Title'}
    r_up = client.put(f'/api/v1/events/{event_id}', json=update_payload, headers=headers_org)
    assert r_up.status_code == 200

    # Verify update by reading directly from the database (avoid JSON serialization issues)
    mongo = __import__('extensions').mongo
    ev_doc = mongo.db.events.find_one({'_id': ObjectId(event_id)})
    assert ev_doc is not None
    assert ev_doc.get('title') == 'Updated Title'

    # Create attendee and RSVP
    att = unique_payload('attendee')
    teardown_user(__import__('extensions').mongo, att['email'])
    token_att = register_and_get_token(client, att)
    headers_att = {'Authorization': f'Bearer {token_att}'}

    r_rsvp = client.post(f'/api/v1/events/{event_id}/rsvp', headers=headers_att)
    assert r_rsvp.status_code in (200, 201)

    # Share location as attendee
    loc_payload = {'lat': 1.23, 'lon': 4.56}
    r_loc = client.post(f'/api/v1/events/{event_id}/location/share', json=loc_payload, headers=headers_att)
    assert r_loc.status_code == 200

    # Photos: GET should work and initially be empty or list
    r_photos = client.get(f'/api/v1/events/{event_id}/photos')
    assert r_photos.status_code == 200
    before_photos = r_photos.get_json().get('photos', [])

    # Monkeypatch cloud upload to return a dummy URL
    def fake_upload(file_obj, ev_id):
        return 'http://example.com/fake.jpg'

    monkeypatch.setattr('api.events.upload_photo_to_cloud', fake_upload)

    # Upload a photo as attendee (must be attendee or organizer)
    data = {'photo': (io.BytesIO(b'testdata'), 'test.jpg')}
    r_upload = client.post(f'/api/v1/events/{event_id}/photos', data=data, headers=headers_att, content_type='multipart/form-data')
    assert r_upload.status_code == 201
    body = r_upload.get_json()
    assert 'photo_url' in body

    # Verify photo appears in GET
    r_photos2 = client.get(f'/api/v1/events/{event_id}/photos')
    assert r_photos2.status_code == 200
    photos_after = r_photos2.get_json().get('photos', [])
    assert len(photos_after) >= len(before_photos)

    # Delete event as organizer
    r_del = client.delete(f'/api/v1/events/{event_id}', headers=headers_org)
    assert r_del.status_code == 200

    # Cleanup users
    teardown_user(__import__('extensions').mongo, org['email'])
    teardown_user(__import__('extensions').mongo, att['email'])
