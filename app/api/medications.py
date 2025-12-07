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
        AND di.scheduled_at <= NOW()
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


@med_bp.route("/api/calendar/day", methods=["GET"])
@token_required
def get_day(user_id):
    date = request.args.get("date")

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT di.instance_id, di.scheduled_at, di.status,
               m.name
        FROM dose_instances di
        JOIN medications m ON m.med_id = di.med_id
        WHERE m.user_id = %s
          AND DATE(di.scheduled_at) = %s
        ORDER BY di.scheduled_at ASC
    """, (user_id, date))

    rows = cur.fetchall()

    result = []
    for row in rows:
        result.append({
            "instance_id": row["instance_id"],
            "name": row["name"],
            "time": row["scheduled_at"].strftime("%H:%M"),
            "status": row["status"]
        })

    return jsonify(result)


@med_bp.route("/api/dose/mark_taken", methods=["POST"])
@token_required
def mark_taken(user_id):
    instance_id = request.json.get("instance_id")

    conn = get_db()
    cur = conn.cursor()

    # add event
    cur.execute("""
        INSERT INTO dose_events (instance_id, event_type, source)
        VALUES (%s, 'ack_taken', 'app')
    """, (instance_id,))

    # update dose
    cur.execute("""
        UPDATE dose_instances SET status = 'taken'
        WHERE instance_id = %s
    """, (instance_id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "taken"})


@med_bp.route("/api/dose/update", methods=["POST"])
@token_required
def update_dose(user_id):
    instance_id = request.json.get("instance_id")
    status = request.json.get("status")

    conn = get_db()
    cur = conn.cursor()

    # UPDATE first (very fast)
    cur.execute("""
        UPDATE dose_instances
        SET status = %s
        WHERE instance_id = %s
    """, (status, instance_id))

    # EVENT insert separately, no lock conflict
    try:
        cur.execute("""
            INSERT INTO dose_events (instance_id, event_type, source)
            VALUES (%s, %s, 'app')
        """, (instance_id, "ack_" + status))
    except:
        pass  # event insert is non-critical

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": status})

@med_bp.route("/api/medications", methods=["POST"])
@token_required
def create_medication(user_id):
    data = request.json

    name = data.get("name")
    notes = data.get("notes")
    schedule = data.get("schedule", {})

    repeat_type = schedule.get("repeat_type")      # daily / weekly / once / custom
    day_mask = schedule.get("day_mask")            # 7-char mask for weekly
    times = schedule.get("times", [])              # ["08:00", "20:00"]
    custom_start = schedule.get("custom_start")
    custom_end = schedule.get("custom_end")

    conn = get_db()
    cur = conn.cursor()

    # 1. Create medication
    cur.execute("""
        INSERT INTO medications (user_id, name, notes, start_date, end_date)
        VALUES (%s, %s, %s, CURDATE(), NULL)
    """, (user_id, name, notes))
    med_id = cur.lastrowid

    # 2. Create schedule rule
    cur.execute("""
        INSERT INTO med_schedule_rules (med_id, repeat_type, day_mask, custom_start, custom_end)
        VALUES (%s, %s, %s, %s, %s)
    """, (med_id, repeat_type, day_mask, custom_start, custom_end))
    rule_id = cur.lastrowid

    # 3. Add times
    for idx, t in enumerate(times):
        cur.execute("""
            INSERT INTO med_times (rule_id, hhmm, sort_order)
            VALUES (%s, %s, %s)
        """, (rule_id, t, idx))

    # 4. Generate dose instances for next 30 days
    import datetime
    today = datetime.date.today()

    def weekly_match(day):
        return day_mask and day_mask[day.weekday()] == "1"

    for i in range(30):
        day = today + datetime.timedelta(days=i)
        should = False

        if repeat_type == "daily":
            should = True
        elif repeat_type == "weekly":
            should = weekly_match(day)
        elif repeat_type == "once":
            should = (custom_start == day.isoformat())
        elif repeat_type == "custom":
            start = datetime.date.fromisoformat(custom_start)
            end = datetime.date.fromisoformat(custom_end)
            should = (start <= day <= end)

        if not should:
            continue

        for t in times:
            hour, minute = map(int, t.split(":"))
            dt = datetime.datetime.combine(day, datetime.time(hour, minute))
            cur.execute("""
                INSERT INTO dose_instances (med_id, scheduled_at, status)
                VALUES (%s, %s, 'scheduled')
            """, (med_id, dt))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "created", "med_id": med_id}), 201



@med_bp.route("/api/medications/<int:med_id>", methods=["PUT"])
@token_required
def update_medication(user_id, med_id):
    data = request.json

    name = data.get("name")
    notes = data.get("notes")
    schedule = data.get("schedule", {})

    repeat_type = schedule.get("repeat_type")      # daily / weekly / once / custom
    day_mask = schedule.get("day_mask")            # 7-char "0101000"
    times = schedule.get("times", [])              # ["10:00", "15:00"]
    custom_start = schedule.get("custom_start")
    custom_end = schedule.get("custom_end")

    conn = get_db()
    cur = conn.cursor()

    # Validate that med belongs to this user
    cur.execute("SELECT med_id FROM medications WHERE med_id = %s AND user_id = %s",
                (med_id, user_id))
    if not cur.fetchone():
        return jsonify({"error": "Medication not found"}), 404

    # Update medication table
    cur.execute("""
        UPDATE medications
        SET name = %s, notes = %s
        WHERE med_id = %s AND user_id = %s
    """, (name, notes, med_id, user_id))

    # Update schedule rule
    cur.execute("""
        UPDATE med_schedule_rules
        SET repeat_type = %s,
            day_mask = %s,
            custom_start = %s,
            custom_end = %s
        WHERE med_id = %s
    """, (repeat_type, day_mask, custom_start, custom_end, med_id))

    # Get rule_id
    cur.execute("SELECT rule_id FROM med_schedule_rules WHERE med_id = %s", (med_id,))
    rule = cur.fetchone()
    rule_id = rule[0]

    # Replace med_times
    cur.execute("DELETE FROM med_times WHERE rule_id = %s", (rule_id,))
    for idx, t in enumerate(times):
        cur.execute("""
            INSERT INTO med_times (rule_id, hhmm, sort_order)
            VALUES (%s, %s, %s)
        """, (rule_id, t, idx))

    # Regenerate future dose instances
    cur.execute("""
        DELETE FROM dose_events WHERE instance_id IN (
            SELECT instance_id FROM dose_instances
            WHERE med_id = %s AND scheduled_at >= NOW()
        )
    """, (med_id,))

    cur.execute("""
        DELETE FROM dose_instances
        WHERE med_id = %s AND scheduled_at >= NOW()
    """, (med_id,))

    import datetime
    today = datetime.date.today()

    def matches_weekly(date, mask):
        return mask[date.weekday()] == "1"

    for i in range(30):
        day = today + datetime.timedelta(days=i)
        should_create = False

        if repeat_type == "daily":
            should_create = True
        elif repeat_type == "weekly" and day_mask:
            should_create = matches_weekly(day, day_mask)
        elif repeat_type == "once" and custom_start:
            should_create = (day.isoformat() == custom_start)
        elif repeat_type == "custom" and custom_start and custom_end:
            start = datetime.date.fromisoformat(custom_start)
            end = datetime.date.fromisoformat(custom_end)
            should_create = start <= day <= end

        if not should_create:
            continue

        for t in times:
            hour, minute = map(int, t.split(":"))
            scheduled_at = datetime.datetime.combine(day, datetime.time(hour, minute))
            cur.execute("""
                INSERT INTO dose_instances (med_id, scheduled_at, status)
                VALUES (%s, %s, 'scheduled')
            """, (med_id, scheduled_at))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "updated"}), 200


@med_bp.route("/api/medications/<int:med_id>", methods=["DELETE"])
@token_required
def delete_medication(user_id, med_id):
    conn = get_db()
    cur = conn.cursor()

    # Remove dose events first
    cur.execute("""
        DELETE de FROM dose_events de
        JOIN dose_instances di ON de.instance_id = di.instance_id
        WHERE di.med_id = %s
    """, (med_id,))

    # Remove dose instances
    cur.execute("DELETE FROM dose_instances WHERE med_id = %s", (med_id,))

    # Remove med_times
    cur.execute("""
        DELETE FROM med_times
        WHERE rule_id IN (SELECT rule_id FROM med_schedule_rules WHERE med_id = %s)
    """, (med_id,))

    # Remove schedule rules
    cur.execute("DELETE FROM med_schedule_rules WHERE med_id = %s", (med_id,))

    cur.execute("DELETE FROM compartment_assignments WHERE med_id = %s", (med_id,))

    # Finally delete medication row
    cur.execute(
        "DELETE FROM medications WHERE med_id = %s AND user_id = %s",
        (med_id, user_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "deleted"}), 200
