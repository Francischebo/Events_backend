# auth_routes.py: Handles /api/v1/auth/* and /api/v1/user/* endpoints
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from firebase_admin import auth
from extensions import mongo, bcrypt

auth_bp = Blueprint('auth_routes', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        if mongo.db is None:
            return jsonify({"message": "Database connection not available"}), 500
        data = request.json
        if mongo.db.users.find_one({"email": data['email']}):
            return jsonify({"message": "Email already registered"}), 400
        if mongo.db.users.find_one({"username": data['username']}):
            return jsonify({"message": "Username already taken"}), 400

        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

        user_data = {
            "username": data['username'],
            "email": data['email'],
            "password_hash": hashed_password,
            "role": data.get('role', 'attendee'),
            "home_location": None,
            "following": [],
            "followers": [],
            "created_at": datetime.utcnow().isoformat()
        }
        user_id = mongo.db.users.insert_one(user_data).inserted_id

        # Remove sensitive data
        user_data.pop('password_hash', None)
        user_data['_id'] = str(user_id)

        token = create_access_token(identity=str(user_id), additional_claims={"role": user_data['role']})

        return jsonify({
            "access_token": token,
            "user": user_data
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error in user registration: {e}")
        return jsonify({"message": "An error occurred during registration."}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        user = mongo.db.users.find_one({"email": data['email']})
        if not user or not user.get('password_hash') or not bcrypt.check_password_hash(user['password_hash'], data['password']):
            return jsonify({"message": "Invalid credentials"}), 401

        # Remove sensitive data
        user.pop('password_hash', None)
        user['_id'] = str(user['_id'])
        if user.get('home_location') and user['home_location'].get('coordinates'):
            user['home_location']['coordinates'] = list(user['home_location']['coordinates'])
        # Convert ObjectIds in lists to strings
        if 'following' in user and user['following']:
            user['following'] = [str(id) for id in user['following']]
        if 'followers' in user and user['followers']:
            user['followers'] = [str(id) for id in user['followers']]
        if 'rsvped_events' in user and user['rsvped_events']:
            user['rsvped_events'] = [str(id) for id in user['rsvped_events']]
        if 'created_events' in user and user['created_events']:
            user['created_events'] = [str(id) for id in user['created_events']]

        role = user.get('role', 'attendee')
        token = create_access_token(identity=str(user['_id']), additional_claims={"role": role})

        return jsonify({
            "access_token": token,
            "user": user
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error in user login: {e}")
        return jsonify({"message": "An error occurred during login."}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    # This is a simulation. In a real app, you'd use Flask-Mail here.
    try:
        data = request.json
        email = data.get('email')
        if not mongo.db.users.find_one({"email": email}):
            return jsonify({"message": "User with that email not found."}), 404
        
        current_app.logger.info(f"Password reset initiated for {email}.")
        return jsonify({"message": "Password reset link sent to your email."}), 200
    except Exception as e:
        current_app.logger.error(f"Error in forgot password: {e}")
        return jsonify({"message": "An error occurred."}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # In a stateless JWT setup, logout is handled client-side by deleting the token.
    # This endpoint can be used to confirm token validity and log the action.
    try:
        # Optionally, you could add the token to a blacklist here.
        jwt_identity = get_jwt_identity()
        current_app.logger.info(f"User {jwt_identity} logged out.")
        return jsonify({"message": "Logged out successfully."}), 200
    except Exception as e:
        current_app.logger.error(f"Error in logout: {e}")
        return jsonify({"message": "An error occurred during logout."}), 500

@auth_bp.route('/user/me', methods=['POST','GET'])
@jwt_required()
def get_user_profile():
    try:
        user_id = get_jwt_identity()
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)}, {"password": 0})
        if not user:
            return jsonify({"error": "User not found"}), 404

        user['_id'] = str(user['_id'])
        if user.get('home_location') and user['home_location'].get('coordinates'):
             user['home_location']['coordinates'] = list(user['home_location']['coordinates'])
        # Convert ObjectIds in lists to strings
        if 'following' in user and user['following']:
            user['following'] = [str(id) for id in user['following']]
        if 'followers' in user and user['followers']:
            user['followers'] = [str(id) for id in user['followers']]
        if 'rsvped_events' in user and user['rsvped_events']:
            user['rsvped_events'] = [str(id) for id in user['rsvped_events']]
        if 'created_events' in user and user['created_events']:
            user['created_events'] = [str(id) for id in user['created_events']]

        return jsonify(user)
    except Exception as e:
        current_app.logger.error(f"Error getting user profile: {e}")
        return jsonify({"message": "An error occurred."}), 500

@auth_bp.route('/user/location', methods=['PUT'])
@jwt_required()
def update_user_location():
    try:
        user_id = get_jwt_identity()
        data = request.json

        # Store coordinates in GeoJSON format: [Longitude, Latitude]
        new_location = {
            "type": "Point",
            "coordinates": [data['lon'], data['lat']]
        }

        result = mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"home_location": new_location}}
        )
        if result.matched_count == 0:
            return jsonify({"message": "User not found"}), 404
        return jsonify({"success": True, "message": "Home location updated"})
    except Exception as e:
        current_app.logger.error(f"Error updating user location: {e}")
        return jsonify({"message": "An error occurred."}), 500

@auth_bp.route('/user/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    try:
        user_id = get_jwt_identity()
        data = request.json
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return jsonify({"message": "Current password and new password are required"}), 400

        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get('password_hash'):
            return jsonify({"message": "User not found"}), 404

        if not bcrypt.check_password_hash(user['password_hash'], current_password):
            return jsonify({"message": "Current password is incorrect"}), 400

        hashed_new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password_hash": hashed_new_password}}
        )

        return jsonify({"message": "Password changed successfully"}), 200
    except Exception as e:
        current_app.logger.error(f"Error changing password: {e}")
        return jsonify({"message": "An error occurred."}), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_firebase_token():
    """
    Verify a Firebase ID token from the client.
    If the user is new, create an account.
    Returns the application's internal JWT.
    """
    try:
        data = request.get_json()
        token = data.get('token')

        if not token:
            return jsonify({'message': 'Firebase ID token is required'}), 400

        decoded_token = auth.verify_id_token(token)
        firebase_uid = decoded_token['uid']
        email = decoded_token.get('email')

        user_data = mongo.db.users.find_one({'firebase_uid': firebase_uid})

        if not user_data:
            # Create a new user if they don't exist
            new_user = {
                "firebase_uid": firebase_uid,
                "email": email,
                "username": decoded_token.get('name', email),
                "photo_url": decoded_token.get('picture'),
                "role": 'attendee',
                "following": [],
                "followers": [],
                "created_at": datetime.utcnow().isoformat()
            }
            user_id = mongo.db.users.insert_one(new_user).inserted_id
            user_data = mongo.db.users.find_one({"_id": user_id})

        access_token = create_access_token(
            identity=str(user_data['_id']),
            additional_claims={'role': user_data.get('role', 'attendee')}
        )

        return jsonify({
            'access_token': access_token,
            'username': user_data['username'],
            'role': user_data.get('role', 'attendee')
        }), 200

    except auth.InvalidIdTokenError as e:
        current_app.logger.warn(f"Invalid Firebase token received: {e}")
        return jsonify({'message': 'Invalid or expired Firebase token'}), 401
    except Exception as e:
        current_app.logger.error(f"Error in Firebase token verification: {e}")
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500