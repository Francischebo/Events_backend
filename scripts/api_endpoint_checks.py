#!/usr/bin/env python3
"""
Simple script to run API endpoint checks against a running server.
This is not a pytest file to avoid automatic collection.
"""
import requests
import json
import time
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:5000/api/v1"

def run_register():
    url = f"{BASE_URL}/auth/register"
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "role": "attendee"
    }
    resp = requests.post(url, json=data)
    print('register', resp.status_code)
    return resp.json() if resp.ok else None

def run_login():
    url = f"{BASE_URL}/auth/login"
    data = {"email": "test@example.com", "password": "password123"}
    resp = requests.post(url, json=data)
    print('login', resp.status_code)
    return resp.json() if resp.ok else None

def main():
    time.sleep(1)
    r = run_register() or run_login()
    if not r:
        print('Auth failed')
        return
    token = r.get('access_token')
    print('Token present:', bool(token))

if __name__ == '__main__':
    main()
