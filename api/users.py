# api/users.py - User Management Endpoints
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import mongo
from bson import ObjectId
from datetime import datetime

users_bp = Blueprint('users', __name__)


@users_bp.route('/<string:user_id>', methods=['GET'])
def get_public_profile(user_id):
    """Return a public view of a user's profile by id."""
    try:
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)}, {'password_hash': 0})
        if not user:
            return jsonify({'message': 'User not found'}), 404

        user['_id'] = str(user['_id'])
        if user.get('home_location') and user['home_location'].get('coordinates'):
            user['home_location']['coordinates'] = list(user['home_location']['coordinates'])

        # Convert follower/following ObjectIds to strings
        user['followers'] = [str(x) for x in user.get('followers', [])]
        user['following'] = [str(x) for x in user.get('following', [])]

        return jsonify(user), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching user profile: {e}")
        return jsonify({'message': 'An error occurred fetching profile'}), 500


@users_bp.route('/<string:user_id>', methods=['PUT'])
@jwt_required()
def update_user_profile(user_id):
    """Allow the authenticated user to update their own profile fields."""
    try:
        auth_user_id = get_jwt_identity()
        if auth_user_id != user_id:
            return jsonify({'message': 'Unauthorized to update this profile'}), 403

        data = request.get_json() or {}
        allowed_fields = {}

        # Allow updating common profile fields
        if 'username' in data:
            allowed_fields['username'] = data['username']
        if 'bio' in data:
            allowed_fields['bio'] = data['bio']
        if 'photo_url' in data:
            allowed_fields['photo_url'] = data['photo_url']

        # Handle home_location either as GeoJSON or {lat, lon}
        if 'home_location' in data:
            loc = data['home_location']
            if isinstance(loc, dict) and 'lat' in loc and 'lon' in loc:
                allowed_fields['home_location'] = {
                    'type': 'Point',
                    'coordinates': [float(loc['lon']), float(loc['lat'])]
                }
            else:
                allowed_fields['home_location'] = loc

        if not allowed_fields:
            return jsonify({'message': 'No valid fields provided for update'}), 400

        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': allowed_fields}
        )

        updated = mongo.db.users.find_one({'_id': ObjectId(user_id)}, {'password_hash': 0})
        updated['_id'] = str(updated['_id'])
        if updated.get('home_location') and updated['home_location'].get('coordinates'):
            updated['home_location']['coordinates'] = list(updated['home_location']['coordinates'])

        updated['followers'] = [str(x) for x in updated.get('followers', [])]
        updated['following'] = [str(x) for x in updated.get('following', [])]

        return jsonify({'message': 'Profile updated', 'user': updated}), 200
    except Exception as e:
        current_app.logger.error(f"Error updating profile: {e}")
        return jsonify({'message': 'An error occurred updating profile'}), 500


@users_bp.route('/<string:user_id>/avatar', methods=['POST'])
@jwt_required()
def upload_user_avatar(user_id):
    """Upload or update a user's avatar/profile photo."""
    try:
        auth_user_id = get_jwt_identity()
        if auth_user_id != user_id:
            return jsonify({'message': 'Unauthorized to update this profile'}), 403

        if 'photo' not in request.files:
            return jsonify({'message': 'No photo file provided'}), 400

        file = request.files['photo']
        if file.filename == '':
            return jsonify({'message': 'No file selected'}), 400

        # Import upload helper lazily to avoid circular imports at module load
        from utils.file_upload import upload_photo_to_cloud, allowed_file

        if not allowed_file(file.filename):
            return jsonify({'message': 'File type not allowed'}), 400

        # Upload to cloud (avatars folder)
        photo_url = upload_photo_to_cloud(file, folder_name=f"avatars/{user_id}")
        if not photo_url:
            return jsonify({'message': 'Avatar upload failed'}), 500

        # Update user document
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'photo_url': photo_url}}
        )

        updated = mongo.db.users.find_one({'_id': ObjectId(user_id)}, {'password_hash': 0})
        updated['_id'] = str(updated['_id'])
        updated['followers'] = [str(x) for x in updated.get('followers', [])]
        updated['following'] = [str(x) for x in updated.get('following', [])]

        return jsonify({'message': 'Avatar uploaded', 'user': updated, 'photo_url': photo_url}), 201

    except Exception as e:
        current_app.logger.error(f"Avatar upload failed: {e}")
        return jsonify({'message': 'Avatar upload failed'}), 500

@users_bp.route('/<string:user_id>/follow', methods=['POST'])
@jwt_required()
def follow_user(user_id):
    """Follow another user/organizer"""
    try:
        follower_id = get_jwt_identity()
        
        # Can't follow yourself
        if follower_id == user_id:
            return jsonify({'message': 'Cannot follow yourself'}), 400
        
        # Verify target user exists
        target_user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not target_user:
            return jsonify({'message': 'User not found'}), 404
        
        # Check if already following
        follower = mongo.db.users.find_one({'_id': ObjectId(follower_id)})
        if ObjectId(user_id) in follower.get('following', []):
            return jsonify({'message': 'Already following this user'}), 400
        
        # Add to following list
        mongo.db.users.update_one(
            {'_id': ObjectId(follower_id)},
            {'$push': {'following': ObjectId(user_id)}}
        )
        
        # Add to target's followers list
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$push': {'followers': ObjectId(follower_id)}}
        )
        
        # Create activity
        mongo.db.activities.insert_one({
            'actor_id': ObjectId(follower_id),
            'actor_name': follower['username'],
            'type': 'FOLLOW',
            'target_user_id': ObjectId(user_id),
            'summary': f"{follower['username']} followed {target_user['username']}",
            'timestamp': datetime.utcnow()
        })
        
        return jsonify({'message': 'Follow successful'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Follow failed: {e}")
        return jsonify({'message': 'Follow failed'}), 500

@users_bp.route('/<string:user_id>/unfollow', methods=['POST'])
@jwt_required()
def unfollow_user(user_id):
    """Unfollow a user/organizer"""
    try:
        follower_id = get_jwt_identity()
        
        # Verify target user exists
        target_user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not target_user:
            return jsonify({'message': 'User not found'}), 404
        
        # Remove from following list
        mongo.db.users.update_one(
            {'_id': ObjectId(follower_id)},
            {'$pull': {'following': ObjectId(user_id)}}
        )
        
        # Remove from target's followers list
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$pull': {'followers': ObjectId(follower_id)}}
        )
        
        return jsonify({'message': 'Unfollow successful'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Unfollow failed: {e}")
        return jsonify({'message': 'Unfollow failed'}), 500