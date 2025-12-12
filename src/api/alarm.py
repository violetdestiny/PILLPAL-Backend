from flask import Blueprint, request, jsonify
from src.db import get_db

alarm_bp = Blueprint("alarm", __name__)

@alarm_bp.route("/api/device/alert_status", methods=["GET"])
def get_alert_status():
    device_id = request.args.get("device_id")

    if not device_id:
        return jsonify({"error": "Missing device_id"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT should_alert, sound_enabled, vibration_enabled, led_enabled
        FROM device_state
        WHERE device_id = %s
    """, (device_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    # If no row exists, return defaults
    if not row:
        return jsonify({
            "should_alert": False,
            "sound": True,
            "vibration": True,
            "led": True
        })

    should_alert, sound, vibration, led = row

    return jsonify({
        "should_alert": bool(should_alert),
        "sound": bool(sound),
        "vibration": bool(vibration),
        "led": bool(led)
    })

