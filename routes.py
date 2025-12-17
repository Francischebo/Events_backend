# routes.py - Blueprint Registration
from auth_routes import auth_bp
from api.events import event_bp
from api.users import users_bp
from api.feed import feed_bp
from api.health import health_bp
from api.rsvp import rsvp_bp
from api.feedback import feedback_bp
from api.ai import ai_bp

def register_blueprints(app):
    """Register all application blueprints"""
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(event_bp, url_prefix='/api/v1/events')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(feed_bp, url_prefix='/api/v1')
    # Health endpoint
    app.register_blueprint(health_bp, url_prefix='/api/v1/health')
    app.register_blueprint(rsvp_bp, url_prefix='/api/v1/rsvp')
    app.register_blueprint(feedback_bp, url_prefix='/api/v1/feedback')
    app.register_blueprint(ai_bp, url_prefix='/api/v1/ai')

    # Root endpoint: provide a small JSON landing page and link to health
    try:
        from flask import jsonify

        def _root():
            return jsonify({
                'service': 'Event Management Backend',
                'status': 'running',
                'health': '/api/v1/health/',
                'api_base': '/api/v1/',
                'note': 'Use /api/v1/health/ for a health check and API endpoints under /api/v1/'
            })

        app.add_url_rule('/', endpoint='root', view_func=_root, methods=['GET'])
    except Exception:
        # If Flask isn't available here for some reason, skip adding the root route
        pass