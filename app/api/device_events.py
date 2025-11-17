from flask import Blueprint, request, jsonify
from app.db import get_db

device_events_bp = Blueprint('device_events', __name__)

@device_events_bp.route("/api/device/event", methods=["POST"])
def device_event():
    data = request.json

    device_id = data.get("device_id")
    event_type = data.get("event_type")
    source = data.get("source", "device")

    if not device_id or not event_type:
        return jsonify({"error": "Missing fields"}), 400

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO device_events (device_id, event_type, source)
            VALUES (%s, %s, %s)
        """, (device_id, event_type, source))

        db.commit()
        cursor.close()

        return jsonify({"status": "ok", "message": "Event logged"}), 201

    except Exception as e:
        print("DB Error:", e)
        return jsonify({"status": "db_error"}), 500
