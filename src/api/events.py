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
