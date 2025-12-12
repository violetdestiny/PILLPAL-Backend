from flask import Blueprint, request, jsonify
from src.db import get_db
from datetime import datetime, timedelta
import pytz

device_alert_bp = Blueprint("device_alert", __name__)


def get_user_for_device(device_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT user_id FROM device_pairings
        WHERE device_id = %s AND active = 1
        LIMIT 1
    """, (device_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["user_id"] if row else None



@device_alert_bp.route("/api/device/alert_status", methods=["GET"])
def get_alert_status():
    device_id = request.args.get("device_id", type=int)

    if not device_id:
        return jsonify({"error": "missing device_id"}), 400

    user_id = get_user_for_device(device_id)
    if not user_id:
        return jsonify({"should_alert": False}), 200

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    
    cur.execute("""
        SELECT instance_id, med_id, scheduled_at, status
        FROM dose_instances
        WHERE med_id IN (SELECT med_id FROM medications WHERE user_id = %s)
        ORDER BY scheduled_at ASC
        LIMIT 1
    """, (user_id,))

    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return jsonify({
            "should_alert": False,
            "led": False,
            "sound": False,
            "vibration": False
        })

    scheduled_time = row["scheduled_at"]
    now = datetime.now()

    
    should_alert = (
        row["status"] == "scheduled" and
        scheduled_time <= now
    )

    cur.close()
    conn.close()

    return jsonify({
        "should_alert": should_alert,
        "instance_id": row["instance_id"],
        "scheduled_at": scheduled_time.isoformat(),
        "led": should_alert,
        "sound": should_alert,
        "vibration": should_alert
    })



@device_alert_bp.route("/api/device/stop_alert", methods=["POST"])
def stop_alert():
    instance_id = request.json.get("instance_id")

    if not instance_id:
        return jsonify({"error": "missing instance_id"}), 400

    conn = get_db()
    cur = conn.cursor()

  
    cur.execute("""
        UPDATE dose_instances
        SET status = 'missed'
        WHERE instance_id = %s
    """, (instance_id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "alert_stopped"}), 200


@device_alert_bp.route("/api/device/ack_open", methods=["POST"])
def ack_open():
    instance_id = request.json.get("instance_id")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE dose_instances
        SET status = 'taken'
        WHERE instance_id = %s
    """, (instance_id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "taken"}), 200
