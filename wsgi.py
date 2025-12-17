"""WSGI entrypoint for Gunicorn with Eventlet.
This module monkey-patches early, creates the Flask app, and exposes
the Socket.IO WSGI application as `application` for Gunicorn to serve.
"""
import os

try:
    import eventlet
    eventlet.monkey_patch()
except Exception:
    # eventlet missing — Gunicorn may still run with other workers
    pass

from app import create_app, socketio
from socketio import WSGIApp as SocketIO_WSGIApp

env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)

# Expose the WSGI application wrapped with the python-socketio WSGIApp middleware.
# Pass the underlying Socket.IO server object (socketio.server) if available.
try:
    sio_server = getattr(socketio, 'server', None)
    if sio_server is None:
        # Fallback: some versions expose 'server' under a different attribute
        sio_server = getattr(socketio, 'socketio', None)
    if sio_server is not None:
        application = SocketIO_WSGIApp(sio_server, app)
    else:
        # If we can't get the underlying server, fall back to the Flask app.
        application = app
except Exception:
    application = app
