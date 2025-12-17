from flask import Blueprint, jsonify, current_app
from extensions import mongo
from datetime import datetime

health_bp = Blueprint('health', __name__)


@health_bp.route('/', methods=['GET'])
def health_check():
    """Health check endpoint. Returns DB connectivity and timestamp."""
    status = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'db': 'unavailable',
        'services': {}
    }

    try:
        # Try a lightweight ping using the underlying client when available
        client = getattr(mongo, 'client', None) or getattr(mongo, '_py', None)
        if client is not None:
            # If we have a pymongo.MongoClient instance, run ping
            try:
                # Some wrappers expose .client, others expose .cx; try both
                real_client = getattr(mongo, 'client', None) or getattr(mongo, '_py', None)
                real_client.admin.command('ping')
                status['db'] = 'ok'
            except Exception:
                # Fall back to attempting a simple operation on mongo.db
                try:
                    if getattr(mongo, 'db', None) is not None:
                        # list collections is lightweight
                        _ = mongo.db.list_collection_names(limit=1)
                        status['db'] = 'ok'
                except Exception:
                    status['db'] = 'unavailable'
        else:
            status['db'] = 'unknown'
    except Exception as e:
        current_app.logger.error(f"Health check DB probe failed: {e}")
        status['db'] = 'unavailable'

    return jsonify({'status': 'ok' if status['db'] == 'ok' else 'degraded', 'details': status}), 200 if status['db'] == 'ok' else 503
