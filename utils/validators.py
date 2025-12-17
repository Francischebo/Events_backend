# utils/validators.py - Input Validation Functions
import re

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    # At least 8 characters
    if len(password) < 8:
        return False
    return True

def validate_coordinates(longitude, latitude):
    """Validate geographic coordinates"""
    if not (-180 <= longitude <= 180):
        return False
    if not (-90 <= latitude <= 90):
        return False
    return True