import requests
import time

base = 'http://127.0.0.1:5000'

stamp = str(int(time.time()))
username = f'e2e_user_{stamp}'
email = f'e2e_{stamp}@example.com'
password = 'password123'

print('Registering user:', email)
resp = requests.post(f'{base}/api/v1/auth/register', json={
    'username': username,
    'email': email,
    'password': password,
    'role': 'attendee'
})
print('Status:', resp.status_code)
try:
    print(resp.json())
except Exception:
    print(resp.text)

if resp.status_code in (200,201):
    print('Logging in...')
    resp2 = requests.post(f'{base}/api/v1/auth/login', json={'email': email, 'password': password})
    print('Login status:', resp2.status_code)
    try:
        print(resp2.json())
    except Exception:
        print(resp2.text)
else:
    print('Register failed; skipping login')
