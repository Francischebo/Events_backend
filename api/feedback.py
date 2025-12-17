# api/feedback.py - Feedback Endpoints
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import mongo, socketio
from bson import ObjectId
from datetime import datetime

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route("/submit", methods=["POST"])
@jwt_required()
def submit_feedback():
    """Submit feedback for an event"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        event_id = data["event_id"]
        rating = data["rating"]
        comment = data.get("comment", "")

        # Insert feedback into database
        mongo.db.feedbacks.insert_one({
            "event_id": event_id,
            "user_id": user_id,
            "rating": rating,
            "comment": comment,
            "timestamp": datetime.utcnow()
        })

        # Broadcast feedback creation
        socketio.emit("feedback_created", {
            "event_id": event_id,
            "rating": rating,
            "comment": comment
        }, broadcast=True)

        return jsonify({"success": True})

    except Exception as e:
        current_app.logger.error(f"Feedback submission failed: {e}")
        return jsonify({"message": "Feedback submission failed"}), 500

@feedback_bp.route("/organizer", methods=["GET"])
@jwt_required()
def get_organizer_feedbacks():
    """Get all feedbacks for events organized by the current user"""
    try:
        user_id = get_jwt_identity()

        # Find all events organized by this user
        events = mongo.db.events.find({"organizer_id": user_id}, {"_id": 1})
        event_ids = [str(event["_id"]) for event in events]

        # Get feedbacks for these events
        feedbacks = mongo.db.feedbacks.find({"event_id": {"$in": event_ids}})

        feedback_list = []
        for feedback in feedbacks:
            # Get event details
            event = mongo.db.events.find_one({"_id": ObjectId(feedback["event_id"])})
            # Get user details
            user = mongo.db.users.find_one({"_id": ObjectId(feedback["user_id"])})

            feedback_list.append({
                "event_id": feedback["event_id"],
                "event_title": event["title"] if event else "Unknown Event",
                "attendee_name": user["username"] if user else "Anonymous",
                "rating": feedback["rating"],
                "feedback": feedback["comment"],
                "timestamp": feedback["timestamp"].isoformat()
            })

        return jsonify({"feedbacks": feedback_list})

    except Exception as e:
        current_app.logger.error(f"Failed to get organizer feedbacks: {e}")
        return jsonify({"message": "Failed to get feedbacks"}), 500

@feedback_bp.route("/send-to-organizer", methods=["POST"])
@jwt_required()
def send_feedback_to_organizer():
    """Send feedback to an organizer"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        organizer_id = data["organizer_id"]
        message = data["message"]

        # Insert feedback into database
        mongo.db.feedbacks.insert_one({
            "organizer_id": organizer_id,
            "user_id": user_id,
            "message": message,
            "timestamp": datetime.utcnow()
        })

        # Broadcast feedback creation
        socketio.emit("feedback_to_organizer", {
            "organizer_id": organizer_id,
            "message": message
        }, broadcast=True)

        return jsonify({"success": True})

    except Exception as e:
        current_app.logger.error(f"Feedback to organizer failed: {e}")
        return jsonify({"message": "Feedback submission failed"}), 500

@feedback_bp.route("/chat/<string:organizer_id>", methods=["GET"])
@jwt_required()
def get_chat_messages(organizer_id):
    """Get chat messages between user and organizer"""
    try:
        user_id = get_jwt_identity()

        # Get messages where user is sender and organizer is receiver, or vice versa
        messages = mongo.db.chat_messages.find({
            "$or": [
                {"sender_id": user_id, "receiver_id": organizer_id},
                {"sender_id": organizer_id, "receiver_id": user_id}
            ]
        }).sort("timestamp", 1)

        message_list = []
        for message in messages:
            sender = mongo.db.users.find_one({"_id": ObjectId(message["sender_id"])})
            message_list.append({
                "message_id": str(message["_id"]),
                "sender_id": message["sender_id"],
                "sender_name": sender["username"] if sender else "Unknown",
                "message": message["message"],
                "timestamp": message["timestamp"].isoformat()
            })

        return jsonify({"messages": message_list})

    except Exception as e:
        current_app.logger.error(f"Failed to get chat messages: {e}")
        return jsonify({"message": "Failed to get messages"}), 500

@feedback_bp.route("/chat/send", methods=["POST"])
@jwt_required()
def send_chat_message():
    """Send a chat message"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        receiver_id = data["receiver_id"]
        message = data["message"]

        # Insert message into database
        mongo.db.chat_messages.insert_one({
            "sender_id": user_id,
            "receiver_id": receiver_id,
            "message": message,
            "timestamp": datetime.utcnow()
        })

        # Broadcast message
        socketio.emit("chat_message", {
            "sender_id": user_id,
            "receiver_id": receiver_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }, room=f"user_{receiver_id}")

        return jsonify({"success": True})

    except Exception as e:
        current_app.logger.error(f"Failed to send chat message: {e}")
        return jsonify({"message": "Failed to send message"}), 500

@feedback_bp.route("/organizer/chats", methods=["GET"])
@jwt_required()
def get_organizer_chats():
    """Get all chat conversations for an organizer"""
    try:
        user_id = get_jwt_identity()

        # Find all unique users who have chatted with this organizer
        chat_partners = mongo.db.chat_messages.distinct("sender_id", {"receiver_id": user_id})
        chat_partners.extend(mongo.db.chat_messages.distinct("receiver_id", {"sender_id": user_id}))
        chat_partners = list(set(chat_partners))  # Remove duplicates

        chats = []
        for partner_id in chat_partners:
            if partner_id == user_id:
                continue

            partner = mongo.db.users.find_one({"_id": ObjectId(partner_id)})
            if not partner:
                continue

            # Get last message
            last_message = mongo.db.chat_messages.find_one({
                "$or": [
                    {"sender_id": user_id, "receiver_id": partner_id},
                    {"sender_id": partner_id, "receiver_id": user_id}
                ]
            }, sort=[("timestamp", -1)])

            chats.append({
                "user_id": partner_id,
                "user_name": partner["username"],
                "last_message": last_message["message"] if last_message else "",
                "last_message_time": last_message["timestamp"].isoformat() if last_message else None
            })

        return jsonify({"chats": chats})

    except Exception as e:
        current_app.logger.error(f"Failed to get organizer chats: {e}")
        return jsonify({"message": "Failed to get chats"}), 500
