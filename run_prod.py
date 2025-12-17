"""run_prod.py
Production-grade runner for the Flask + Socket.IO application.
Prefers Eventlet (already listed in requirements) for async support.
Usage: set env vars (MONGO_URI, BIND_HOST, PORT) then run `python run_prod.py`.
"""
import os
import logging

try:
    import eventlet
    eventlet.monkey_patch()
    _has_eventlet = True
except Exception:
    _has_eventlet = False

from app import create_app, socketio


def main():
    logging.basicConfig(level=logging.INFO)
    env = os.environ.get('FLASK_ENV', 'production')
    app = create_app(env)

    bind_host = os.environ.get('BIND_HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))

    if _has_eventlet:
        app.logger.info('Starting server with eventlet (recommended for Socket.IO)')
    else:
        app.logger.warning('Eventlet not available; falling back to default Socket.IO server. For best performance install eventlet.')

    # In production, debug=False and use_reloader=False
    socketio.run(app, host=bind_host, port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
