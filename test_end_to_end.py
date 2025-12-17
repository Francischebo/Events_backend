#!/usr/bin/env python3
"""
End-to-end integration test using Flask test client.
This script runs a sequence:
 - register organizer
 - register attendee
 - organizer creates event
 - organizer follows attendee
 - attendee RSVPs to event
 - organizer checks event stats (rsvp_count should be 1)
 - organizer fetches feed (should include RSVP activity)

Run with the project's venv Python.
"""
import json
from app import create_app
from extensions import mongo


def pretty(resp):
    try:
        return json.dumps(resp.get_json(), indent=2)
    except Exception:
        return resp.data.decode('utf-8')


def main():
    app = create_app('testing')

    with app.app_context():
        # Clean test database
        db = mongo.db
        db.users.delete_many({})
        db.events.delete_many({})
        db.activities.delete_many({})
        db.messages.delete_many({})

        client = app.test_client()

        # Register organizer
        org_reg = client.post('/api/v1/auth/register', json={
            'username': 'org_user',
            'email': 'org@example.com',
            'password': 'password123',
            'role': 'organizer'
        })
        assert org_reg.status_code == 201, f"Org register failed: {pretty(org_reg)}"
        org_token = org_reg.get_json()['access_token']
        org_user = org_reg.get_json()['user']
        org_id = org_user['_id']

        # Register attendee
        att_reg = client.post('/api/v1/auth/register', json={
            'username': 'att_user',
            'email': 'att@example.com',
            'password': 'password123',
            'role': 'attendee'
        })
        assert att_reg.status_code == 201, f"Att register failed: {pretty(att_reg)}"
        att_token = att_reg.get_json()['access_token']
        att_user = att_reg.get_json()['user']
        att_id = att_user['_id']

        # Organizer creates an event
        headers_org = {'Authorization': f'Bearer {org_token}'}
        event_payload = {
            'title': 'E2E Test Event',
            'description': 'Integration test event',
            'date': '2025-12-31T12:00:00Z',
            'location_address': 'Testville',
            'location': {'type': 'Point', 'coordinates': [0.0, 0.0]}
        }
        ev_resp = client.post('/api/v1/events', json=event_payload, headers=headers_org)
        assert ev_resp.status_code == 201, f"Create event failed: {pretty(ev_resp)}"
        event_id = ev_resp.get_json()['event_id']

        # Organizer follows attendee so organizer feed will include attendee activities
        follow_resp = client.post(f'/api/v1/users/{att_id}/follow', headers=headers_org)
        assert follow_resp.status_code == 200, f"Follow failed: {pretty(follow_resp)}"

        # Attendee RSVPs to event
        headers_att = {'Authorization': f'Bearer {att_token}'}
        rsvp_resp = client.post(f'/api/v1/events/{event_id}/rsvp', json={'username': 'att_user'}, headers=headers_att)
        assert rsvp_resp.status_code in (200,201), f"RSVP failed: {pretty(rsvp_resp)}"

        # Organizer checks stats
        stats_resp = client.get(f'/api/v1/events/{event_id}/stats', headers=headers_org)
        assert stats_resp.status_code == 200, f"Stats fetch failed: {pretty(stats_resp)}"
        stats = stats_resp.get_json()
        assert stats.get('rsvp_count', 0) >= 1, f"Unexpected rsvp_count: {stats}"

        # Organizer fetches feed
        feed_resp = client.get('/api/v1/feed', headers=headers_org)
        assert feed_resp.status_code == 200, f"Feed fetch failed: {pretty(feed_resp)}"
        feed = feed_resp.get_json().get('feed', [])
        # Look for an RSVP activity related to our event
        rsvp_activities = [a for a in feed if a.get('type') == 'RSVP' and a.get('event_id') == event_id]
        assert len(rsvp_activities) >= 1, f"No RSVP activity found in feed: {feed}"

        print("✅ End-to-end integration test passed")
        return True


if __name__ == '__main__':
    ok = main()
    if not ok:
        raise SystemExit(1)
