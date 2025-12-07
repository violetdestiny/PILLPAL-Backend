from flask import Blueprint, request, jsonify
from ..db import get_db
import jwt, datetime, os
from functools import wraps

med_bp = Blueprint("medications", __name__)
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_key123")


# ---------------------------------------
# Helper function to clean datetime values
# ---------------------------------------
def clean(value):
    import datetime
    if isinstance(value, (datetime.timedelta, datetime.datetime, datetime.date, datetime.time)):
        return str(value)
    return value


# ---------------------------------------
# TOKEN DECORATOR
# ---------------------------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": "Missing token"}), 401

        try:
            token = token.replace("Bearer ", "")
            decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = decoded["user_id"]
        except Exception as e:
            print("Token decode failed:", e)
            return jsonify({"error": "Invalid token"}), 401

        return f(user_id, *args, **kwargs)

    return decorated


# ---------------------------------------
# GET ALL MEDICATIONS
# ---------------------------------------
@med_bp.route("/api/medications", methods=["GET"])
@token_required
def get_medications(user_id):

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT med_id, name, notes, 
               start_date AS active_start_date,
               end_date AS active_end_date
        FROM medications
        WHERE user_id = %s
    """, (user_id,))
    
    medications = cur.fetchall()
    results = []

    for med in medications:
        med_id = med["med_id"]

        # Get schedule rule
        cur.execute("""
            SELECT rule_id, repeat_type, day_mask, lead_minutes
            FROM med_schedule_rules
            WHERE med_id = %s
            LIMIT 1
        """, (med_id,))
        rule = cur.fetchone()

        # Get times
        times = []
        lead_minutes = 0

        if rule:
            lead_minutes = int(rule.get("lead_minutes", 0))

            cur.execute("""
                SELECT hhmm
                FROM med_times
                WHERE rule_id = %s
                ORDER BY sort_order
            """, (rule["rule_id"],))
            times = [clean(row["hhmm"]) for row in cur.fetchall()]

        results.append({
            "med_id": med["med_id"],
            "name": med["name"],
            "notes": med["notes"],
            "active_start_date": clean(med["active_start_date"]),
            "active_end_date": clean(med["active_end_date"]),
            "schedule": {
                "repeat_type": rule["repeat_type"] if rule else None,
                "day_mask": rule["day_mask"] if rule else None,
                "times": times,
                "custom_start": None,
                "custom_end": None,
                "lead_minutes": lead_minutes
            }
        })

    cur.close()
    conn.close()

    return jsonify(results)


# ---------------------------------------
# GET MEDICATION BY ID
# ---------------------------------------
@med_bp.route("/api/medications/<int:med_id>", methods=["GET"])
@token_required
def get_medication_by_id(user_id, med_id):

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT med_id, name, notes,
               start_date AS active_start_date,
               end_date AS active_end_date
        FROM medications
        WHERE med_id = %s AND user_id = %s
    """, (med_id, user_id))

    med = cur.fetchone()
    if not med:
        return jsonify({"error": "Medication not found"}), 404

    cur.execute("""
        SELECT rule_id, repeat_type, day_mask, lead_minutes
        FROM med_schedule_rules
        WHERE med_id = %s
        LIMIT 1
    """, (med_id,))
    rule = cur.fetchone()

    times = []
    lead_minutes = 0

    if rule:
        lead_minutes = int(rule.get("lead_minutes", 0))

        cur.execute("""
            SELECT hhmm FROM med_times
            WHERE rule_id = %s
            ORDER BY sort_order
        """, (rule["rule_id"],))
        times = [clean(row["hhmm"]) for row in cur.fetchall()]

    result = {
        "med_id": med["med_id"],
        "name": med["name"],
        "notes": med["notes"],
        "active_start_date": clean(med["active_start_date"]),
        "active_end_date": clean(med["active_end_date"]),
        "schedule": {
            "repeat_type": rule["repeat_type"] if rule else None,
            "day_mask": rule["day_mask"] if rule else None,
            "times": times,
            "custom_start": None,
            "custom_end": None,
            "lead_minutes": lead_minutes
        }
    }

    cur.close()
    conn.close()
    return jsonify(result)


# ---------------------------------------
# GET MEDICATION HISTORY
# ---------------------------------------
@med_bp.route("/api/medications/history", methods=["GET"])
@token_required
def get_history(user_id):

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT di.instance_id, di.scheduled_at, di.status,
               m.med_id, m.name,
               DATE(di.scheduled_at) as day
        FROM dose_instances di
        JOIN medications m ON m.med_id = di.med_id
        WHERE m.user_id = %s
        ORDER BY di.scheduled_at DESC
    """, (user_id,))

    rows = cur.fetchall()

    history = {}
    for row in rows:
        day = clean(row["day"])
        if day not in history:
            history[day] = []

        history[day].append({
            "id": row["med_id"],
            "name": row["name"],
            "scheduledTime": clean(row["scheduled_at"].strftime("%H:%M")),
            "status": row["status"]
        })

    result = [{"date": day, "medications": meds} for day, meds in history.items()]

    cur.close()
    conn.close()
    return jsonify(result)
