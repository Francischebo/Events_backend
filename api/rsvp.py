# api/rsvp.py - RSVP Endpoints
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import mongo, socketio
from bson import ObjectId
from datetime import datetime

rsvp_bp = Blueprint('rsvp', __name__)

@rsvp_bp.route("/submit", methods=["POST"])
@jwt_required()
def submit_rsvp():
    """Submit RSVP for an event"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        event_id = data["event_id"]

        # Insert RSVP into database
        mongo.db.rsvps.update_one(
            {"event_id": event_id, "user_id": user_id},
            {"$set": {"status": "going", "timestamp": datetime.utcnow()}},
            upsert=True
        )

        # Get total RSVPs
        stats = mongo.db.rsvps.count_documents({"event_id": event_id})

        # Notify organizer
        event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
        if event:
            socketio.emit("rsvp_update", {
                "event_id": event_id,
                "total_rsvps": stats
            }, broadcast=True)

        return jsonify({"success": True, "total_rsvps": stats})

    except Exception as e:
        current_app.logger.error(f"RSVP submission failed: {e}")
        return jsonify({"message": "RSVP submission failed"}), 500
