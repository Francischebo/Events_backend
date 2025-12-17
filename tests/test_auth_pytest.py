import os
import pytest
from uuid import uuid4

from app import create_app
from extensions import mongo


@pytest.fixture(scope='module')
def app():
    # Use testing config by default; allow overriding via MONGO_URI_TEST env var
    test_env_uri = os.environ.get('MONGO_URI_TEST')
    app = create_app('testing')
    if test_env_uri:
        app.config['MONGO_URI'] = test_env_uri
    # ensure the app initializes extensions with the possibly-updated config
    with app.app_context():
        # mongo is initialized in create_app; nothing else needed
        pass
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def create_unique_user_payload():
    suffix = str(uuid4())[:8]
    return {
        'username': f'py_test_{suffix}',
        'email': f'py_test_{suffix}@example.com',
        'password': 'TestPass!234',
        'role': 'attendee'
    }


def teardown_user_by_email(email):
    try:
        mongo.db.users.delete_one({'email': email})
    except Exception:
        pass


def test_register_and_login_flow(client):
    payload = create_unique_user_payload()
    email = payload['email']

    # Ensure cleanup in case of leftovers
    teardown_user_by_email(email)

    # Register
    resp = client.post('/api/v1/auth/register', json=payload)
    assert resp.status_code == 201, f"Register failed: {resp.status_code} {resp.get_data(as_text=True)}"
    body = resp.get_json()
    assert 'access_token' in body
    assert 'user' in body and body['user']['email'] == email

    # Login
    resp2 = client.post('/api/v1/auth/login', json={'email': email, 'password': payload['password']})
    assert resp2.status_code == 200, f"Login failed: {resp2.status_code} {resp2.get_data(as_text=True)}"
    body2 = resp2.get_json()
    assert 'access_token' in body2
    assert 'user' in body2 and body2['user']['email'] == email

    # Teardown
    teardown_user_by_email(email)
