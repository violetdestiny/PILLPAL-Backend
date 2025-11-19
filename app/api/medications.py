from flask import Blueprint, request, jsonify
from ..db import get_db
import jwt, datetime, os
from functools import wraps

med_bp = Blueprint("medications", __name__)
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_key123")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": "Missing token"}), 401

        try:
            token = token.replace("Bearer ", "")
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            return f(data, *args, **kwargs)
        except Exception as e:
            print("Token decode failed:", e)
            return jsonify({"error": "Invalid token"}), 401

    return decorated


@med_bp.route("/api/medications", methods=["GET"])
@token_required
def get_medications(current_user):
    user_id = current_user["user_id"]

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT med_id, name, notes, start_date AS active_start_date,
               end_date AS active_end_date
        FROM medications
        WHERE user_id = %s
    """, (user_id,))
    
    medications = cur.fetchall()
    results = []

    for med in medications:
        med_id = med["med_id"]

        # schedule
        cur.execute("""
            SELECT rule_id, repeat_type, day_mask
            FROM med_schedule_rules
            WHERE med_id = %s
            LIMIT 1
        """, (med_id,))
        rule = cur.fetchone()

        # times
        if rule:
            cur.execute("""
                SELECT hhmm
                FROM med_times
                WHERE rule_id = %s
                ORDER BY sort_order
            """, (rule["rule_id"],))
            times = [row["hhmm"] for row in cur.fetchall()]
        else:
            times = []

        results.append({
            "med_id": med["med_id"],
            "name": med["name"],
            "notes": med["notes"],
            "active_start_date": str(med["active_start_date"]),
            "active_end_date": str(med["active_end_date"]) if med["active_end_date"] else None,
            "schedule": {
                "repeat_type": rule["repeat_type"] if rule else None,
                "day_mask": rule["day_mask"] if rule else None,
                "times": times,
                "custom_start": None,
                "custom_end": None
            }
        })

    cur.close()
    conn.close()

    return jsonify(results)
