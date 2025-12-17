# api/ai.py - AI-Powered Recommendations
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import mongo
from bson import ObjectId
import openai
import os

ai_bp = Blueprint('ai', __name__)

@ai_bp.route("/recommend", methods=["POST"])
@jwt_required()
def recommend_events():
    """Recommend events using LLM"""
    try:
        user_id = get_jwt_identity()

        # Get user's RSVPs
        user_rsvps = list(mongo.db.rsvps.find({"user_id": user_id}))
        events = list(mongo.db.events.find({}))

        # Prepare prompt
        prompt = f"""
        User RSVPs: {user_rsvps}
        All Events: {events}

        Recommend 5 events this user is most likely to RSVP next.
        Return list of event IDs only.
        """

        # Call OpenAI API
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return jsonify({
            "recommended_event_ids": response.choices[0].message.content
        })

    except Exception as e:
        current_app.logger.error(f"AI recommendation failed: {e}")
        return jsonify({"message": "AI recommendation failed"}), 500
