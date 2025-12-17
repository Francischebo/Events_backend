# api/feed.py - Feed and Organizer Endpoints
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import mongo
from utils.decorators import organizer_required
from bson import ObjectId

feed_bp = Blueprint('feed', __name__)

@feed_bp.route('/feed', methods=['GET'])
@jwt_required()
def get_feed():
    """Get personalized activity feed"""
    try:
        user_id = get_jwt_identity()
        
        # Get pagination parameters
        limit = request.args.get('limit', type=int, default=20)
        offset = request.args.get('offset', type=int, default=0)
        
        # Get user's following list
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        following_ids = user.get('following', [])
        following_ids.append(ObjectId(user_id))  # Include own activities
        
        # Fetch activities from followed users
        activities_cursor = mongo.db.activities.find({
            'actor_id': {'$in': following_ids}
        }).sort('timestamp', -1).skip(offset).limit(limit)

        # Prepare for efficient event title lookup
        activities = list(activities_cursor)
        event_ids = [activity['event_id'] for activity in activities if 'event_id' in activity]

        event_titles = {}
        if event_ids:
            events_cursor = mongo.db.events.find({'_id': {'$in': event_ids}}, {'title': 1})
            event_titles = {str(event['_id']): event['title'] for event in events_cursor}

        feed = []
        for activity in activities:
            activity_item = {
                'activity_id': str(activity['_id']),
                'actor_id': str(activity['actor_id']),
                'actor_name': activity['actor_name'],
                'type': activity['type'],
                'summary': activity['summary'],
                'timestamp': activity['timestamp'].isoformat()
            }
            
            if 'event_id' in activity:
                event_id_str = str(activity['event_id'])
                activity_item['event_id'] = event_id_str
                activity_item['event_title'] = event_titles.get(event_id_str, 'Event not found')

            feed.append(activity_item)
        
        return jsonify({'feed': feed}), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to fetch feed: {e}")
        return jsonify({'message': 'Failed to fetch feed'}), 500

@feed_bp.route('/organizer/events', methods=['GET'])
@jwt_required()
@organizer_required
def get_organizer_events():
    """Get all events created by the authenticated organizer"""
    try:
        if mongo.db is None:
            return jsonify({'message': 'Database not available'}), 503

        user_id = get_jwt_identity()

        # Fetch events created by this organizer
        events_cursor = mongo.db.events.find({
            'organizer_id': ObjectId(user_id)
        }).sort('date', 1)

        events = []
        for event in events_cursor:
            event['event_id'] = str(event.pop('_id'))
            event['organizer_id'] = str(event['organizer_id'])
            event['date'] = event['date'].isoformat()
            events.append(event)

        return jsonify({'events': events}), 200

    except Exception as e:
        current_app.logger.error(f"Failed to fetch organizer events: {e}")
        return jsonify({'message': 'Failed to fetch events'}), 500
