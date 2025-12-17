import requests
import time

BASE = 'http://127.0.0.1:5000/api/v1'

email = 'mobile_test_user@example.com'
password = 'TestPass!234'
username = 'mobile_test_user'

print('Waiting a moment for server to be ready...')
for i in range(6):
    try:
        r = requests.get(f'{BASE}/health', timeout=2)
        print('Health:', r.status_code, r.text)
        break
    except Exception as e:
        time.sleep(1)
else:
    print('Server health check failed; continuing to try register/login')

# Try register
print('\nAttempting REGISTER...')
try:
    r = requests.post(f'{BASE}/auth/register', json={
        'username': username,
        'email': email,
        'password': password,
        'role': 'attendee'
    }, timeout=10)
    print('REGISTER status:', r.status_code)
    try:
        print('REGISTER body:', r.json())
    except Exception:
        print('REGISTER text:', r.text)
except Exception as e:
    print('REGISTER request failed:', e)

# Try login
print('\nAttempting LOGIN...')
try:
    r = requests.post(f'{BASE}/auth/login', json={'email': email, 'password': password}, timeout=10)
    print('LOGIN status:', r.status_code)
    try:
        print('LOGIN body:', r.json())
    except Exception:
        print('LOGIN text:', r.text)
except Exception as e:
    print('LOGIN request failed:', e)

print('\nDone')
