from flask import Blueprint, request, jsonify
from src.db import get_db
from src.scheduler.medication_scheduler import get_alert_state

device_poll_bp = Blueprint("device_poll", __name__)

@device_poll_bp.route("/api/device/poll", methods=["GET"])
def poll_device():
    device_id = request.args.get("device_id")

    if not device_id:
        return jsonify({"error": "Missing device_id"}), 400

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM notification_settings WHERE user_id = %s", (device_id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "No settings for device"}), 404

    return jsonify({
        "led": row["led_enabled"],
        "sound": row["sound_enabled"],
        "vibration": row["vibration_enabled"],
        "alert": get_alert_state(int(device_id))
    })

