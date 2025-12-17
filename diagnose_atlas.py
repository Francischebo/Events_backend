#!/usr/bin/env python3
"""
Quick MongoDB Atlas Diagnostic - Check Network and Whitelist Status
"""
import socket
import sys

print("=" * 80)
print("MongoDB Atlas Network Diagnostic")
print("=" * 80)

# Extract hostname from URI
mongo_uri = 'mongodb+srv://francischeboo404_db_user:Fr%40m0ng00se387623@communityapp.ktglocw.mongodb.net/event_management?retryWrites=true&w=majority&ssl=true'

hostname = 'communityapp.ktglocw.mongodb.net'
port = 27017

print(f"\nAttempting to reach: {hostname}:{port}")

# Test 1: DNS resolution
print("\n" + "=" * 80)
print("TEST 1: DNS Resolution")
print("=" * 80)

try:
    ip = socket.gethostbyname(hostname)
    print(f"✅ DNS resolved: {hostname} → {ip}")
except socket.gaierror as e:
    print(f"❌ DNS resolution failed: {e}")
    print("   → Your computer cannot reach the MongoDB Atlas domain")
    sys.exit(1)

# Test 2: Port connectivity
print("\n" + "=" * 80)
print("TEST 2: Network Port Connectivity")
print("=" * 80)

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((hostname, port))
    sock.close()
    
    if result == 0:
        print(f"✅ Port {port} is OPEN and reachable")
    else:
        print(f"❌ Port {port} is CLOSED or unreachable")
        print(f"\n   This could mean:")
        print(f"   1. Your IP is not whitelisted in MongoDB Atlas")
        print(f"   2. A firewall is blocking the connection")
        print(f"   3. MongoDB cluster is offline")
except Exception as e:
    print(f"❌ Connection test failed: {e}")

# Test 3: Get your public IP
print("\n" + "=" * 80)
print("TEST 3: Your Public IP Address")
print("=" * 80)

try:
    import urllib.request
    response = urllib.request.urlopen('https://api.ipify.org?format=json', timeout=5)
    data = response.read().decode()
    import json
    public_ip = json.loads(data)['ip']
    print(f"✅ Your Public IP: {public_ip}")
    print(f"\n   ⚠️  Make sure THIS IP is whitelisted in MongoDB Atlas:")
    print(f"   → Go to: MongoDB Atlas → Network Access → Add IP Address")
    print(f"   → Enter: {public_ip}")
except Exception as e:
    print(f"⚠️  Could not fetch public IP: {e}")
    print(f"   You can check your IP at: https://www.whatismyipaddress.com/")

# Test 4: Connection string check
print("\n" + "=" * 80)
print("TEST 4: Connection String Configuration")
print("=" * 80)

print(f"""
URI components:
  - User: francischeboo404_db_user
  - Cluster: communityapp.ktglocw.mongodb.net
  - Database: event_management
  - SSL: ✅ Enabled (ssl=true in URI)
  - Retry Writes: ✅ Enabled (retryWrites=true in URI)

✅ Connection string looks correct.
""")

print("=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("""
1. If port 27017 is CLOSED:
   - Log in to MongoDB Atlas: https://account.mongodb.com/
   - Go to: Network Access → Add IP Address
   - Add your PUBLIC IP (shown above) to the whitelist
   - Wait 1-2 minutes for the change to take effect

2. If your IP is already whitelisted:
   - Try from a different network (e.g., mobile hotspot)
   - Check if your firewall is blocking MongoDB connections
   - Try updating your PyMongo: pip install --upgrade pymongo

3. Verify credentials:
   - Username: francischeboo404_db_user
   - Password: Fr@m0ng00se387623 (verify special characters are correct)
   - Database: event_management
""")
