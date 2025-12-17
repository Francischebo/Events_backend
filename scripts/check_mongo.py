"""Check MongoDB Atlas connection (uses MONGO_URI env variable).
Runs a ping and prints server info and a sample list of collections for the configured DB.
"""
import os
import sys
from pymongo import MongoClient
import traceback

try:
    import certifi
except Exception:
    certifi = None


def main():
    uri = os.environ.get('MONGO_URI')
    dbname = os.environ.get('MONGO_DBNAME') or os.environ.get('MONGO_DB')

    if not uri:
        print('ERROR: MONGO_URI environment variable is not set')
        sys.exit(2)

    print('Using MONGO_URI:', '***REDACTED***' if uri else 'None')
    # Try default connection first
    try:
        client = MongoClient(uri, tls=True, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print('Connected with default TLS settings.')
    except Exception as e_default:
        print('Default TLS connection failed:', e_default)
        # Try with certifi CA bundle if available
        if certifi:
            try:
                ca = certifi.where()
                client = MongoClient(uri, tls=True, tlsCAFile=ca, serverSelectionTimeoutMS=5000)
                client.admin.command('ping')
                print('Connected using certifi CA bundle:', ca)
            except Exception as e_cert:
                print('Connection with certifi CA failed:', e_cert)
                # Last-resort: allow invalid certificates (diagnostic only)
                try:
                    client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
                    client.admin.command('ping')
                    print('Connected with tlsAllowInvalidCertificates=True (not secure).')
                except Exception as e_insecure:
                    print('Connection failed even with insecure option.')
                    print('Traceback (default):')
                    traceback.print_exception(type(e_default), e_default, e_default.__traceback__)
                    print('Traceback (certifi):')
                    traceback.print_exception(type(e_cert), e_cert, e_cert.__traceback__)
                    print('Traceback (insecure):')
                    traceback.print_exception(type(e_insecure), e_insecure, e_insecure.__traceback__)
                    return 3
        else:
            # No certifi available; try insecure only as diagnostic
            try:
                client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
                client.admin.command('ping')
                print('Connected with tlsAllowInvalidCertificates=True (not secure).')
            except Exception as e_insecure2:
                print('Connection failed (certifi not installed). Error:', e_insecure2)
                print('Original error:', e_default)
                return 3

    # If we reach here, client is connected
    try:
        info = client.server_info()
        print('MongoDB server version:', info.get('version'))
    except Exception as e:
        print('Could not fetch server_info:', e)

    if dbname:
        try:
            db = client[dbname]
            cols = db.list_collection_names()
            print(f'Collections in {dbname}:', cols[:20])
        except Exception as e:
            print('Could not list collections for', dbname, ':', e)
    else:
        try:
            dbs = client.list_database_names()
            print('Databases found (sample):', dbs[:20])
        except Exception as e:
            print('Could not list databases:', e)

    print('MongoDB connection looks healthy.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
