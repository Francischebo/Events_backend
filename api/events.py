# api/events.py - Event Management Endpoints
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import mongo, socketio
from models.event import Event
from utils.decorators import organizer_required
from utils.geolocation import find_nearby_events
from utils.file_upload import upload_photo_to_cloud, allowed_file
from bson import ObjectId
from datetime import datetime
import math

event_bp = Blueprint('events', __name__)

@event_bp.route('', methods=['GET'])
def get_events():
    """Fetch list of events with optional filtering"""
    try:
        if mongo.db is None:
            # Return sample events if database is not available
            sample_events = [
                {
                    'event_id': 'sample1',
                    'title': 'Sample Event 1',
                    'description': 'This is a sample event for testing.',
                    'date': '2025-12-10T10:00:00',
                    'location_address': 'Nairobi, Kenya',
                    'location': {'coordinates': [36.817223, -1.286389]},
                    'organizer_id': 'sample_organizer',
                    'category': 'General'
                },
                {
                    'event_id': 'sample2',
                    'title': 'Sample Event 2',
                    'description': 'Another sample event.',
                    'date': '2025-12-15T14:00:00',
                    'location_address': 'New York, USA',
                    'location': {'coordinates': [-74.006, 40.7128]},
                    'organizer_id': 'sample_organizer',
                    'category': 'Tech'
                }
            ]
            return jsonify({'events': sample_events}), 200

        # Get query parameters
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        radius_km_str = request.args.get('radius_km', type=str)
        if radius_km_str and radius_km_str.lower() != 'null':
            try:
                radius_km = float(radius_km_str)
            except ValueError:
                radius_km = 10.0
        else:
            radius_km = 10.0
        search = request.args.get('search', type=str)

        query = {}

        # Text search filter
        if search:
            query['$or'] = [
                {'title': {'$regex': search, '$options': 'i'}},
                {'description': {'$regex': search, '$options': 'i'}},
                {'location_address': {'$regex': search, '$options': 'i'}}
            ]

        # Geospatial query for nearby events
        if latitude is not None and longitude is not None:
            events = find_nearby_events(latitude, longitude, radius_km, query)
        else:
            # Get all events without distance calculation
            events_cursor = mongo.db.events.find(query).sort('date', 1)
            events = []
            for event in events_cursor:
                event['event_id'] = str(event.pop('_id'))
                event['organizer_id'] = str(event['organizer_id'])
                event['date'] = event['date'].isoformat()
                event['rsvps'] = [str(oid) for oid in event.get('rsvps', [])]
                event['arrivals'] = [str(oid) for oid in event.get('arrivals', [])]
                events.append(event)

        return jsonify({'events': events}), 200

    except Exception as e:
        current_app.logger.error(f"Failed to fetch events: {e}")
        return jsonify({'message': 'Failed to fetch events'}), 500

@event_bp.route('', methods=['POST'])
@jwt_required()
@organizer_required
def create_event():
    """Create a new event (Organizer only)"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Validate required fields
        required_fields = ['title', 'description', 'date', 'location_address', 'location']
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400
        
        # Validate location format
        if 'type' not in data['location'] or 'coordinates' not in data['location']:
            return jsonify({'message': 'Invalid location format'}), 400
        
        # Create event
        event = Event(
            title=data['title'],
            description=data['description'],
            date=datetime.fromisoformat(data['date'].replace('Z', '+00:00')),
            category=data.get('category', 'General'),
            location_address=data['location_address'],
            location=data['location'],
            organizer_id=ObjectId(user_id),
            geofence_radius=data.get('geofence_radius', 200)
        )
        
        event_id = event.save()
        
        # Add to organizer's created_events
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$push': {'created_events': event_id}}
        )
        
        # Create activity
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        mongo.db.activities.insert_one({
            'actor_id': ObjectId(user_id),
            'actor_name': user['username'],
            'type': 'EVENT_CREATED',
            'event_id': event_id,
            'summary': f"{user['username']} created event '{data['title']}'",
            'timestamp': datetime.utcnow()
        })

        # Broadcast event creation
        event_data = {
            "_id": str(event_id),
            "title": data['title'],
            "description": data['description'],
            "date": data['date'],
            "location_address": data['location_address'],
            "organizer_id": str(user_id)
        }
        socketio.emit("event_created", event_data)

        return jsonify({
            'message': 'Event created successfully',
            'event_id': str(event_id)
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Failed to create event: {e}")
        return jsonify({'message': 'Failed to create event'}), 500

@event_bp.route('/<string:event_id>', methods=['PUT'])
@jwt_required()
@organizer_required
def update_event(event_id):
    """Update an existing event"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Verify event exists and user owns it
        event = mongo.db.events.find_one({'_id': ObjectId(event_id)})
        if not event:
            return jsonify({'message': 'Event not found'}), 404
        
        if str(event['organizer_id']) != user_id:
            return jsonify({'message': 'Unauthorized'}), 403
        
        # Build update document
        update_data = {}
        if 'title' in data:
            update_data['title'] = data['title']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'date' in data:
            update_data['date'] = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
        if 'location_address' in data:
            update_data['location_address'] = data['location_address']
        if 'location' in data:
            update_data['location'] = data['location']
        if 'category' in data:
            update_data['category'] = data['category']
        if 'geofence_radius' in data:
            update_data['geofence_radius'] = data['geofence_radius']
        
        # Update event
        mongo.db.events.update_one(
            {'_id': ObjectId(event_id)},
            {'$set': update_data}
        )
        
        return jsonify({'message': 'Event updated successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to update event: {e}")
        return jsonify({'message': 'Failed to update event'}), 500

@event_bp.route('/<string:event_id>', methods=['DELETE'])
@jwt_required()
@organizer_required
def delete_event(event_id):
    """Delete an event"""
    try:
        user_id = get_jwt_identity()
        
        # Verify event exists and user owns it
        event = mongo.db.events.find_one({'_id': ObjectId(event_id)})
        if not event:
            return jsonify({'message': 'Event not found'}), 404
        
        if str(event['organizer_id']) != user_id:
            return jsonify({'message': 'Unauthorized'}), 403
        
        # Delete event
        mongo.db.events.delete_one({'_id': ObjectId(event_id)})
        
        # Remove from organizer's created_events
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$pull': {'created_events': ObjectId(event_id)}}
        )
        
        # Clean up related data
        mongo.db.messages.delete_many({'event_id': ObjectId(event_id)})
        mongo.db.activities.delete_many({'event_id': ObjectId(event_id)})
        
        return jsonify({'message': 'Event deleted successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to delete event: {e}")
        return jsonify({'message': 'Failed to delete event'}), 500

@event_bp.route('/<string:event_id>/rsvp', methods=['POST'])
@jwt_required()
def rsvp_event(event_id):
    """RSVP to an event"""
    try:
        user_id = get_jwt_identity()
        
        # Verify event exists
        event = mongo.db.events.find_one({'_id': ObjectId(event_id)})
        if not event:
            return jsonify({'message': 'Event not found'}), 404
        
        # Check if already RSVP'd
        if ObjectId(user_id) in event.get('rsvps', []):
            return jsonify({'message': 'Already RSVP\'d to this event'}), 400
        
        # Add RSVP
        mongo.db.events.update_one(
            {'_id': ObjectId(event_id)},
            {'$push': {'rsvps': ObjectId(user_id)}}
        )
        
        # Add to user's rsvped_events
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$push': {'rsvped_events': ObjectId(event_id)}}
        )
        
        # Create activity
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        mongo.db.activities.insert_one({
            'actor_id': ObjectId(user_id),
            'actor_name': user['username'],
            'type': 'RSVP',
            'event_id': ObjectId(event_id),
            'summary': f"{user['username']} RSVP'd to '{event['title']}'",
            'timestamp': datetime.utcnow()
        })

        # 🔥 Notify organizer instantly
        socketio.emit(
            "rsvp_update",
            {"event_id": event_id, "count": len(event.get('rsvps', [])) + 1},
            room=f"organizer_{event['organizer_id']}"
        )

        return jsonify({'message': 'RSVP successful'}), 201
        
    except Exception as e:
        current_app.logger.error(f"RSVP failed: {e}")
        return jsonify({'message': 'RSVP failed'}), 500

@event_bp.route('/<string:event_id>/arrival', methods=['POST'])
@jwt_required()
def record_arrival(event_id):
    """Record user arrival at event"""
    try:
        user_id = get_jwt_identity()
        
        # Verify event exists
        event = mongo.db.events.find_one({'_id': ObjectId(event_id)})
        if not event:
            return jsonify({'message': 'Event not found'}), 404
        
        # Check if already recorded
        if ObjectId(user_id) in event.get('arrivals', []):
            return jsonify({'message': 'Arrival already recorded'}), 400
        
        # Record arrival
        mongo.db.events.update_one(
            {'_id': ObjectId(event_id)},
            {'$push': {'arrivals': ObjectId(user_id)}}
        )
        
        return jsonify({'message': 'Arrival recorded'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to record arrival: {e}")
        return jsonify({'message': 'Failed to record arrival'}), 500

@event_bp.route('/<string:event_id>/stats', methods=['GET'])
@jwt_required()
@organizer_required
def get_event_stats(event_id):
    """Get event statistics"""
    try:
        user_id = get_jwt_identity()

        # Verify event exists and user owns it
        event = mongo.db.events.find_one({'_id': ObjectId(event_id)})
        if not event:
            return jsonify({'message': 'Event not found'}), 404

        if str(event['organizer_id']) != user_id:
            return jsonify({'message': 'Unauthorized'}), 403

        rsvp_count = len(event.get('rsvps', []))
        arrival_count = len(event.get('arrivals', []))

        return jsonify({
            'rsvp_count': rsvp_count,
            'arrival_count': arrival_count
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get stats: {e}")
        return jsonify({'message': 'Failed to get stats'}), 500

@event_bp.route('/organizer/rsvp-stats', methods=['GET'])
@jwt_required()
@organizer_required
def get_organizer_rsvp_stats():
    """Get comprehensive RSVP statistics for organizer's events"""
    try:
        user_id = get_jwt_identity()

        # Get all events by this organizer
        events_cursor = mongo.db.events.find({'organizer_id': ObjectId(user_id)})
        events = list(events_cursor)

        total_events = len(events)
        total_rsvps = 0
        total_arrivals = 0
        event_stats = []
        category_stats = {}
        monthly_stats = {}

        for event in events:
            rsvps = len(event.get('rsvps', []))
            arrivals = len(event.get('arrivals', []))
            total_rsvps += rsvps
            total_arrivals += arrivals

            # Event-specific stats
            event_stats.append({
                'event_id': str(event['_id']),
                'title': event['title'],
                'rsvp_count': rsvps,
                'arrival_count': arrivals,
                'attendance_rate': (arrivals / rsvps * 100) if rsvps > 0 else 0,
                'date': event['date'].isoformat()
            })

            # Category stats
            category = event.get('category', 'General')
            if category not in category_stats:
                category_stats[category] = {'events': 0, 'rsvps': 0, 'arrivals': 0}
            category_stats[category]['events'] += 1
            category_stats[category]['rsvps'] += rsvps
            category_stats[category]['arrivals'] += arrivals

            # Monthly stats
            month_key = event['date'].strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {'events': 0, 'rsvps': 0, 'arrivals': 0}
            monthly_stats[month_key]['events'] += 1
            monthly_stats[month_key]['rsvps'] += rsvps
            monthly_stats[month_key]['arrivals'] += arrivals

        # Calculate averages and trends
        avg_rsvps_per_event = total_rsvps / total_events if total_events > 0 else 0
        avg_attendance_rate = (total_arrivals / total_rsvps * 100) if total_rsvps > 0 else 0

        # Sort event stats by date (most recent first)
        event_stats.sort(key=lambda x: x['date'], reverse=True)

        # Convert category stats to list
        category_list = []
        for cat, stats in category_stats.items():
            category_list.append({
                'category': cat,
                'events_count': stats['events'],
                'total_rsvps': stats['rsvps'],
                'total_arrivals': stats['arrivals'],
                'avg_rsvps_per_event': stats['rsvps'] / stats['events'] if stats['events'] > 0 else 0
            })

        # Convert monthly stats to list and sort
        monthly_list = []
        for month, stats in monthly_stats.items():
            monthly_list.append({
                'month': month,
                'events_count': stats['events'],
                'total_rsvps': stats['rsvps'],
                'total_arrivals': stats['arrivals']
            })
        monthly_list.sort(key=lambda x: x['month'], reverse=True)

        return jsonify({
            'overview': {
                'total_events': total_events,
                'total_rsvps': total_rsvps,
                'total_arrivals': total_arrivals,
                'avg_rsvps_per_event': avg_rsvps_per_event,
                'avg_attendance_rate': avg_attendance_rate
            },
            'event_stats': event_stats[:10],  # Top 10 most recent events
            'category_stats': category_list,
            'monthly_stats': monthly_list[:12]  # Last 12 months
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get organizer RSVP stats: {e}")
        return jsonify({'message': 'Failed to get RSVP stats'}), 500

@event_bp.route('/<string:event_id>/photos', methods=['GET'])
def get_event_photos(event_id):
    """Get all photos for an event"""
    try:
        event = mongo.db.events.find_one({'_id': ObjectId(event_id)})
        if not event:
            return jsonify({'message': 'Event not found'}), 404
        
        photos = event.get('photo_gallery', [])
        return jsonify({'photos': photos}), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to get photos: {e}")
        return jsonify({'message': 'Failed to get photos'}), 500

@event_bp.route('/<string:event_id>/photos', methods=['POST'])
@jwt_required()
def upload_event_photo(event_id):
    """Upload a photo for an event"""
    try:
        user_id = get_jwt_identity()
        
        # Verify event exists
        event = mongo.db.events.find_one({'_id': ObjectId(event_id)})
        if not event:
            return jsonify({'message': 'Event not found'}), 404
        
        # Check if user is attendee or organizer
        user_obj_id = ObjectId(user_id)
        is_organizer = str(event['organizer_id']) == user_id
        is_attendee = user_obj_id in event.get('rsvps', []) or user_obj_id in event.get('arrivals', [])
        
        if not (is_organizer or is_attendee):
            return jsonify({'message': 'Must be an attendee or organizer to upload photos'}), 403
        
        # Check if file was uploaded
        if 'photo' not in request.files:
            return jsonify({'message': 'No photo file provided'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'message': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'message': 'File type not allowed'}), 400
        
        # Upload to cloud storage
        photo_url = upload_photo_to_cloud(file, event_id)
        if not photo_url:
            return jsonify({'message': 'Photo upload failed'}), 500
        
        # Add photo URL to event
        mongo.db.events.update_one(
            {'_id': ObjectId(event_id)},
            {'$push': {'photo_gallery': photo_url}}
        )
        
        # Create activity
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        mongo.db.activities.insert_one({
            'actor_id': ObjectId(user_id),
            'actor_name': user['username'],
            'type': 'PHOTO_UPLOADED',
            'event_id': ObjectId(event_id),
            'summary': f"{user['username']} uploaded a photo to '{event['title']}'",
            'timestamp': datetime.utcnow()
        })
        
        return jsonify({
            'message': 'Photo uploaded successfully',
            'photo_url': photo_url
        }), 201

    except Exception as e:
        current_app.logger.error(f"Photo upload failed: {e}")
        return jsonify({'message': 'Photo upload failed'}), 500

@event_bp.route('/<string:event_id>/location/share', methods=['POST'])
@jwt_required()
def share_location(event_id):
    """Share location for an event (placeholder for real-time location sharing)"""
    try:
        data = request.json
        lat = data.get('lat')
        lon = data.get('lon')

        if not lat or not lon:
            return jsonify({'message': 'lat and lon required'}), 400

        # For now, just log the location
        current_app.logger.info(f"Location shared for event {event_id}: {lat}, {lon}")

        return jsonify({'message': 'Location shared successfully'}), 200

    except Exception as e:
        current_app.logger.error(f"Location share failed: {e}")
        return jsonify({'message': 'Location share failed'}), 500


@event_bp.route('/recommend', methods=['GET'])
@jwt_required()
def recommend_events():
    """Return recommended events for the authenticated user.
    Strategy:
    - Use collaborative filtering on RSVP signals: users who RSVP'd the same events
      often RSVP to related events. Score candidate events by co-occurrence count.
    - If latitude/longitude provided, boost nearby events.
    - Fallback to popular or nearby events when insufficient signal.
    """
    try:
        user_id = get_jwt_identity()
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        radius_km_str = request.args.get('radius_km', type=str)
        if radius_km_str and radius_km_str.lower() != 'null':
            try:
                radius_km = float(radius_km_str)
            except ValueError:
                radius_km = 20.0
        else:
            radius_km = 20.0

        # Load user and their RSVPed events
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'message': 'User not found'}), 404

        user_rsvps = user.get('rsvped_events', []) or []
        user_rsvps = [ObjectId(x) for x in user_rsvps]

        candidate_scores = {}

        if user_rsvps:
            # Find other users who RSVP'd to any of these events
            other_users = mongo.db.users.find({'rsvped_events': {'$in': user_rsvps}})
            for other in other_users:
                other_events = other.get('rsvped_events', []) or []
                for ev in other_events:
                    ev_oid = ObjectId(ev)
                    # Skip events user already RSVPed to
                    if ev_oid in user_rsvps:
                        continue
                    candidate_scores[ev_oid] = candidate_scores.get(ev_oid, 0) + 1

        # If no candidates from collaborative signal, fallback to popular events
        if not candidate_scores:
            # Popular events by rsvp count
            for e in mongo.db.events.find().sort([('rsvps', -1), ('date', 1)]).limit(50):
                candidate_scores[ObjectId(e['_id'])] = len(e.get('rsvps', []))

        # Fetch event documents for candidates and compute proximity boost
        results = []
        for ev_oid, base_score in candidate_scores.items():
            ev = mongo.db.events.find_one({'_id': ObjectId(ev_oid)})
            if not ev:
                continue
            # Compute proximity score
            proximity_boost = 0.0
            if latitude is not None and longitude is not None and ev.get('location'):
                try:
                    ev_lon, ev_lat = ev['location']['coordinates'][0], ev['location']['coordinates'][1]
                    dist = _haversine_km(latitude, longitude, ev_lat, ev_lon)
                    if dist <= radius_km:
                        proximity_boost = (1 - (dist / radius_km)) * 2.0
                except Exception:
                    proximity_boost = 0.0

            score = float(base_score) + proximity_boost
            ev['event_id'] = str(ev.pop('_id'))
            ev['organizer_id'] = str(ev['organizer_id'])
            ev['date'] = ev['date'].isoformat() if isinstance(ev.get('date'), datetime) else ev.get('date')
            ev['rsvps'] = [str(oid) for oid in ev.get('rsvps', [])]
            ev['arrivals'] = [str(oid) for oid in ev.get('arrivals', [])]
            results.append({'event': ev, 'score': score})

        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        events_out = [r['event'] for r in results[:20]]
        return jsonify({'events': events_out}), 200

    except Exception as e:
        current_app.logger.error(f"Failed to compute recommendations: {e}")
        return jsonify({'message': 'Failed to compute recommendations'}), 500


def _haversine_km(lat1, lon1, lat2, lon2):
    # Returns distance in kilometers between two lat/lon pairs
    r = 6371.0
    lat1r, lon1r, lat2r, lon2r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = math.sin(dlat/2)**2 + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return r * c
