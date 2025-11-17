from flask import Blueprint, request, jsonify
from src.db import get_db
import json

api_events = Blueprint("api_events", __name__)

@api_events.route("/events", methods=["POST"])
def store_event():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()

    sql = """
        INSERT INTO device_events (device_id, event_type, event_source, meta)
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(sql, (
        data.get("device_id"),
        data.get("event_type"),
        "device",
        json.dumps(data),
    ))

    conn.commit()
    return jsonify({"status": "saved"}), 201
