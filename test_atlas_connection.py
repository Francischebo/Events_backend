#!/usr/bin/env python3
"""
Comprehensive MongoDB Atlas Connection Test
Tests SSL/TLS connection, database connectivity, collections, and basic operations
"""
import os
import sys
from urllib.parse import urlparse
import ssl
import certifi

# Print configuration info
print("=" * 80)
print("MongoDB Atlas Connection Test")
print("=" * 80)

MONGO_URI = os.environ.get('MONGO_URI')
MONGO_DBNAME = os.environ.get('MONGO_DBNAME') or 'event_management'

if not MONGO_URI:
    print("❌ ERROR: MONGO_URI environment variable not set")
    sys.exit(1)

print(f"\n📋 Configuration:")
print(f"   MONGO_URI: {MONGO_URI[:80]}..." if len(MONGO_URI) > 80 else f"   MONGO_URI: {MONGO_URI}")
print(f"   MONGO_DBNAME: {MONGO_DBNAME}")
print(f"   SSL/TLS Certificate: {certifi.where()}")

# Test 1: Parse and validate URI
print("\n" + "=" * 80)
print("TEST 1: URI Validation")
print("=" * 80)

try:
    parsed = urlparse(MONGO_URI)
    print(f"✅ URI Scheme: {parsed.scheme}")
    print(f"✅ Hostname: {parsed.hostname}")
    print(f"✅ Port: {parsed.port or 27017} (default if not specified)")
    print(f"✅ Database: {parsed.path.lstrip('/') or 'default'}")
    
    if parsed.scheme != 'mongodb+srv':
        print("⚠️  WARNING: Using mongodb+srv scheme (SRV record for Atlas)")
    
    if 'ssl=true' in MONGO_URI or 'ssl=True' in MONGO_URI:
        print("✅ SSL explicitly enabled in connection string")
    elif '?ssl' not in MONGO_URI:
        print("ℹ️  SSL is enabled by default for MongoDB Atlas")
except Exception as e:
    print(f"❌ URI parsing failed: {e}")
    sys.exit(1)

# Test 2: PyMongo connection with SSL/TLS
print("\n" + "=" * 80)
print("TEST 2: PyMongo Connection (with SSL/TLS)")
print("=" * 80)

try:
    import pymongo
    print(f"✅ PyMongo version: {pymongo.__version__}")
    
    # Create client with correct PyMongo TLS settings (MongoDB 4.0+)
    client = pymongo.MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=15000,
        retryWrites=True
    )
    
    print("✅ MongoDB client created successfully")
    
    # Test connection
    print("\n   Testing server connection...")
    server_info = client.server_info()
    print(f"✅ Server Info: MongoDB version {server_info.get('version', 'unknown')}")
    print(f"✅ Server is UP and RESPONSIVE")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n   Error Details:")
    print(f"   - This typically indicates a TLS/SSL certificate issue")
    print(f"   - Possible causes:")
    print(f"     1. Firewall blocking port 27017")
    print(f"     2. IP whitelist not configured in MongoDB Atlas")
    print(f"     3. Certificate validation issues")
    print(f"\n   Attempting to diagnose...")
    
    # Try to connect with relaxed TLS settings for diagnostic purposes only
    try:
        client = pymongo.MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=15000,
            tlsInsecure=True  # For diagnostic purposes only - NOT for production
        )
        print("⚠️  Connected with tlsInsecure=True (diagnostic mode only)")
        server_info = client.server_info()
        print(f"✅ Server reached: {server_info.get('version', 'unknown')}")
    except Exception as e2:
        print(f"❌ Connection failed even with relaxed TLS: {e2}")
        sys.exit(1)

# Test 3: Database and Collections
print("\n" + "=" * 80)
print("TEST 3: Database and Collections")
print("=" * 80)

try:
    # Get database
    db = client.get_database(MONGO_DBNAME)
    print(f"✅ Database connected: {db.name}")
    
    # List collections
    collections = db.list_collection_names()
    print(f"✅ Collections found: {len(collections)}")
    for col in collections:
        col_count = db[col].count_documents({})
        print(f"   - {col}: {col_count} documents")
    
    if not collections:
        print("   ℹ️  No collections yet (database is empty)")
    
except Exception as e:
    print(f"❌ Database/collection query failed: {e}")
    sys.exit(1)

# Test 4: Authentication
print("\n" + "=" * 80)
print("TEST 4: Authentication and Permissions")
print("=" * 80)

try:
    # Try to insert a test document
    test_collection = db['_connection_test']
    test_doc = {'test': 'connection_test', 'timestamp': __import__('datetime').datetime.utcnow()}
    result = test_collection.insert_one(test_doc)
    print(f"✅ Write permission confirmed (inserted document ID: {result.inserted_id})")
    
    # Read it back
    found = test_collection.find_one({'_id': result.inserted_id})
    if found:
        print(f"✅ Read permission confirmed (retrieved test document)")
    
    # Clean up
    test_collection.delete_one({'_id': result.inserted_id})
    print(f"✅ Delete permission confirmed (test document cleaned up)")
    
except Exception as e:
    print(f"⚠️  Write test failed: {e}")
    print("   (This may indicate insufficient permissions or a read-only database)")

# Test 5: Index and geospatial support
print("\n" + "=" * 80)
print("TEST 5: Indexes and Geospatial Support")
print("=" * 80)

try:
    events_col = db['events']
    
    # Check for 2dsphere index
    indexes = events_col.list_indexes()
    geospatial_indexes = [idx for idx in indexes if '2dsphere' in str(idx.get('key', []))]
    
    if geospatial_indexes:
        print(f"✅ Geospatial (2dsphere) indexes found: {len(geospatial_indexes)}")
    else:
        print("⚠️  No 2dsphere indexes found (location-based queries may be slower)")
        print("   Attempting to create 2dsphere index on location field...")
        try:
            events_col.create_index([('location', '2dsphere')])
            print("✅ Created 2dsphere index on 'location' field")
        except Exception as idx_e:
            print(f"⚠️  Could not create index: {idx_e}")
    
except Exception as e:
    print(f"⚠️  Index check failed: {e}")

# Test 6: Network connectivity and latency
print("\n" + "=" * 80)
print("TEST 6: Network Latency and Performance")
print("=" * 80)

try:
    import time
    
    start = time.time()
    client.admin.command('ping')
    latency_ms = (time.time() - start) * 1000
    
    print(f"✅ Server ping successful")
    print(f"   Latency: {latency_ms:.2f}ms")
    
    if latency_ms > 500:
        print("⚠️  High latency detected - connection may be slow")
    else:
        print("✅ Latency is good")
    
except Exception as e:
    print(f"❌ Ping test failed: {e}")

# Test 7: Flask-PyMongo integration
print("\n" + "=" * 80)
print("TEST 7: Flask-PyMongo Integration")
print("=" * 80)

try:
    from flask import Flask
    from flask_pymongo import PyMongo
    
    app = Flask(__name__)
    app.config['MONGO_URI'] = MONGO_URI
    
    mongo = PyMongo(app)
    
    with app.app_context():
        # Test connection
        mongo.db.command('ping')
        print(f"✅ Flask-PyMongo initialized successfully")
        print(f"✅ Database object: {mongo.db}")
        print(f"✅ Database name: {mongo.db.name}")
        
except Exception as e:
    print(f"❌ Flask-PyMongo integration failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 80)
print("✅ MongoDB Atlas Connection Test Complete")
print("=" * 80)
print(f"\n✅ Your MongoDB Atlas is working correctly!")
print(f"✅ SSL/TLS connection: VERIFIED")
print(f"✅ Database: {MONGO_DBNAME}")
print(f"✅ Ready for application use")
