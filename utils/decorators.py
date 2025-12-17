# utils/decorators.py - Custom Decorators
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt

def organizer_required(fn):
    """Decorator to ensure user has organizer role"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'organizer':
            return jsonify({'message': 'Organizer access required'}), 403
        return fn(*args, **kwargs)
    return wrapper