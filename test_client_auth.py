import os
import json
from uuid import uuid4
from app import create_app


def run_auth_test():
    # Use the 'production' config to mirror real runtime behavior.
    app = create_app('production')

    # Create a unique test user to avoid collisions
    suffix = str(uuid4())[:8]
    email = f"mobile_test_{suffix}@example.com"
    username = f"mobile_test_{suffix}"
    password = "TestPass!234"

    with app.test_client() as client:
        # Register
        reg_resp = client.post('/api/v1/auth/register', json={
            'username': username,
            'email': email,
            'password': password,
            'role': 'attendee'
        })
        print('REGISTER status:', reg_resp.status_code)
        try:
            print('REGISTER body:', reg_resp.get_json())
        except Exception:
            print('REGISTER text:', reg_resp.data)

        # Login
        login_resp = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
        print('\nLOGIN status:', login_resp.status_code)
        try:
            print('LOGIN body:', login_resp.get_json())
        except Exception:
            print('LOGIN text:', login_resp.data)


if __name__ == '__main__':
    print('Running Flask test-client auth test...')
    run_auth_test()
