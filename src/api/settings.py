from flask import Blueprint, request, jsonify
from src.db import get_db
import jwt
import os
from functools import wraps
import paho.mqtt.publish as publish

settings_bp = Blueprint("settings", __name__)
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_key123")

MQTT_BROKER = "172.20.10.3"
MQTT_TOPIC = "pillpal/device/commands"


def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Missing token"}), 401

        try:
            token = token.replace("Bearer ", "")
            decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = decoded["user_id"]
        except Exception:
            return jsonify({"error": "Invalid token"}), 401

        return f(user_id, *args, **kwargs)

    return wrapper


@settings_bp.route("/api/settings/update", methods=["POST"])
@token_required
def update_settings(user_id):
    data = request.json or {}

    print("SETTINGS RECEIVED:", data)

    # Accept BOTH naming formats
    sound = data.get("sound_enabled", data.get("sound", False))
    vibration = data.get("vibration_enabled", data.get("vibration", False))
    led = data.get("led_enabled", data.get("device_notifications", False))

    # Force boolean (never None)
    sound = bool(sound)
    vibration = bool(vibration)
    led = bool(led)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT setting_id FROM notification_settings WHERE user_id = %s", (user_id,))
    exists = cur.fetchone()

    if exists:
        cur.execute("""
            UPDATE notification_settings
            SET sound_enabled=%s, vibration_enabled=%s, led_enabled=%s
            WHERE user_id=%s
        """, (sound, vibration, led, user_id))
    else:
        cur.execute("""
            INSERT INTO notification_settings (user_id, sound_enabled, vibration_enabled, led_enabled)
            VALUES (%s, %s, %s, %s)
        """, (user_id, sound, vibration, led))

    conn.commit()
    cur.close()
    conn.close()

    # Send MQTT updates
    try:
        publish.single(
            MQTT_TOPIC,
            payload="SET_PREF_SOUND_" + ("ON" if sound else "OFF"),
            hostname=MQTT_BROKER
        )

        publish.single(
            MQTT_TOPIC,
            payload="SET_PREF_VIB_" + ("ON" if vibration else "OFF"),
            hostname=MQTT_BROKER
        )

        publish.single(
            MQTT_TOPIC,
            payload="SET_PREF_LED_" + ("ON" if led else "OFF"),
            hostname=MQTT_BROKER
        )

    except Exception as e:
        print("MQTT publish error:", e)

    return jsonify({"status": "updated"})
