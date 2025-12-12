from flask import Blueprint, request, jsonify
from src.scheduler.medication_scheduler import clear_alert

ack_bp = Blueprint("ack", __name__)

@ack_bp.route("/api/device/ack", methods=["POST"])
def ack():
    data = request.json
    device_id = data.get("device_id")
    clear_alert(device_id)
    return jsonify({"status": "cleared"})
