from flask import Blueprint, request, jsonify
from src.db import get_db

medications_bp = Blueprint("medications_bp", __name__)

@medications_bp.route("/medications", methods=["GET"])
def get_medications():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 
            m.med_id,
            m.name,
            m.notes,
            m.active_start_date,
            s.times,
            s.repeat_type,
            s.day_mask,
            s.custom_start,
            s.custom_end
        FROM medications m
        LEFT JOIN schedules s ON m.med_id = s.med_id
        WHERE m.user_id = %s
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    meds = []
    for row in rows:
        (
            med_id,
            name,
            notes,
            active_start_date,
            times,
            repeat_type,
            day_mask,
            custom_start,
            custom_end
        ) = row

        meds.append({
            "med_id": med_id,
            "name": name,
            "notes": notes,
            "active_start_date": active_start_date,
            "schedule": {
                "times": times.split(",") if times else [],
                "repeat_type": repeat_type,
                "day_mask": day_mask,
                "custom_start": str(custom_start) if custom_start else None,
                "custom_end": str(custom_end) if custom_end else None
            }
        })

    return jsonify(meds), 200
