# websocket_handlers.py - WebSocket Chat Implementation
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import decode_token
from extensions import mongo
from bson import ObjectId
from datetime import datetime

def register_socketio_handlers(socketio):
    """Register WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print('Client connected')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print('Client disconnected')
    
    @socketio.on('join_chat')
    def handle_join_chat(data):
        """Join a chat room for an event"""
        try:
            token = data.get('token')
            event_id = data.get('event_id')
            
            if not token or not event_id:
                emit('error', {'message': 'Token and event_id required'})
                return
            
            # Verify JWT token
            try:
                decoded = decode_token(token)
                user_id = decoded['sub']
            except Exception as e:
                emit('error', {'message': 'Invalid token'})
                return
            
            # Verify event exists
            event = mongo.db.events.find_one({'_id': ObjectId(event_id)})
            if not event:
                emit('error', {'message': 'Event not found'})
                return
            
            # Join the room
            join_room(event_id)
            
            # Get user info
            user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            
            # Notify room
            emit('user_joined', {
                'username': user['username'],
                'message': f"{user['username']} joined the chat"
            }, room=event_id)
            
            # Send recent messages to the newly joined user
            recent_messages = mongo.db.messages.find({
                'event_id': ObjectId(event_id)
            }).sort('timestamp', -1).limit(50)
            
            messages = []
            for msg in reversed(list(recent_messages)):
                messages.append({
                    'username': msg['username'],
                    'text': msg['text'],
                    'timestamp': msg['timestamp'].isoformat()
                })
            
            emit('recent_messages', {'messages': messages})
            
        except Exception as e:
            emit('error', {'message': f'Failed to join chat: {str(e)}'})
    
    @socketio.on('leave_chat')
    def handle_leave_chat(data):
        """Leave a chat room"""
        try:
            event_id = data.get('event_id')
            username = data.get('username')
            
            if event_id:
                leave_room(event_id)
                
                # Notify room
                emit('user_left', {
                    'username': username,
                    'message': f"{username} left the chat"
                }, room=event_id)
                
        except Exception as e:
            emit('error', {'message': f'Failed to leave chat: {str(e)}'})
    
    @socketio.on('send_message')
    def handle_send_message(data):
        """Handle incoming chat message"""
        try:
            token = data.get('token')
            event_id = data.get('event_id')
            text = data.get('text')
            
            if not all([token, event_id, text]):
                emit('error', {'message': 'Token, event_id, and text required'})
                return
            
            # Verify JWT token
            try:
                decoded = decode_token(token)
                user_id = decoded['sub']
            except Exception as e:
                emit('error', {'message': 'Invalid token'})
                return
            
            # Get user info
            user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if not user:
                emit('error', {'message': 'User not found'})
                return
            
            # Save message to database
            timestamp = datetime.utcnow()
            message = {
                'event_id': ObjectId(event_id),
                'user_id': ObjectId(user_id),
                'username': user['username'],
                'text': text,
                'timestamp': timestamp
            }
            
            mongo.db.messages.insert_one(message)
            
            # Broadcast message to all clients in the room
            emit('new_message', {
                'username': user['username'],
                'text': text,
                'timestamp': timestamp.isoformat()
            }, room=event_id)
            
        except Exception as e:
            emit('error', {'message': f'Failed to send message: {str(e)}'})

    @socketio.on('join_as_organizer')
    def join_as_organizer(data):
        """Join organizer room for real-time RSVP updates"""
        try:
            organizer_id = data.get('organizer_id')

            if not organizer_id:
                emit('error', {'message': 'organizer_id required'})
                return

            # Join the organizer room
            join_room(f"organizer_{organizer_id}")

            emit('joined_organizer_room', {'message': 'Joined organizer room'})

        except Exception as e:
            emit('error', {'message': f'Failed to join organizer room: {str(e)}'})

    @socketio.on('event_created')
    def handle_event_created(data):
        """Handle event creation broadcast"""
        # This is handled in the API endpoint, but we can add logging here if needed
        pass

    @socketio.on('rsvp_update')
    def handle_rsvp_update(data):
        """Handle RSVP update broadcast"""
        # This is handled in the API endpoint, but we can add logging here if needed
        pass

    @socketio.on('feedback_created')
    def handle_feedback_created(data):
        """Handle feedback creation broadcast"""
        # This is handled in the API endpoint, but we can add logging here if needed
        pass
