from flask import Blueprint, request, jsonify
from src.db import get_db

api_events = Blueprint("api_events", __name__)


@api_events.route("/medications", methods=["GET"])
def get_medications():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT med_id, name, notes
        FROM medications
        WHERE user_id = %s
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    medications = []
    for med_id, name, notes in rows:
        medications.append({
            "med_id": med_id,
            "name": name,
            "notes": notes
        })

    return jsonify(medications), 200

@api_events.route("/calendar", methods=["GET"])
def get_calendar():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            ud.dose_id,
            ud.medication_id,
            m.name AS medication_name,
            ud.scheduled_date,
            ud.scheduled_time
        FROM upcoming_doses ud
        JOIN medications m ON ud.medication_id = m.med_id
        WHERE ud.user_id = %s
        ORDER BY ud.scheduled_date ASC, ud.scheduled_time ASC
        """,
        (user_id,)
    )

    results = cursor.fetchall()
    return jsonify(results), 200

@api_events.route("/history", methods=["GET"])
def get_history():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            de.event_id,
            de.medication_id,
            m.name AS medication_name,
            de.event_date,
            de.event_time,
            de.status
        FROM dose_events de
        JOIN medications m ON de.medication_id = m.med_id
        WHERE de.user_id = %s
        ORDER BY de.event_date DESC, de.event_time DESC
        """,
        (user_id,)
    )

    results = cursor.fetchall()
    return jsonify(results), 200

@api_events.route("/history", methods=["POST"])
def add_history():
    data = request.json

    required = ["user_id", "medication_id", "event_date", "event_time", "status"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO dose_events (user_id, medication_id, event_date, event_time, status)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            data["user_id"],
            data["medication_id"],
            data["event_date"],
            data["event_time"],
            data["status"]
        )
    )

    conn.commit()

    return jsonify({"message": "History saved"}), 201

