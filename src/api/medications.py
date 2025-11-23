from flask import Blueprint, request, jsonify
from src.db import get_db
from datetime import date

medications_bp = Blueprint("medications_bp", __name__)


@medications_bp.route("/medications", methods=["GET"])
def get_medications():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Traemos meds + regla + tiempos en una sola query
    cursor.execute(
        """
        SELECT
            m.med_id,
            m.user_id,
            m.name,
            m.notes,
            m.start_date,
            m.end_date,
            r.rule_id,
            r.repeat_type,
            r.day_mask,
            r.lead_minutes,
            t.time_id,
            t.hhmm,
            t.sort_order
        FROM medications m
        LEFT JOIN med_schedule_rules r ON r.med_id = m.med_id
        LEFT JOIN med_times t ON t.rule_id = r.rule_id
        WHERE m.user_id = %s
        ORDER BY m.med_id, t.sort_order, t.time_id
        """,
        (user_id,),
    )

    rows = cursor.fetchall()

    meds = {}

    for row in rows:
        med_id = row["med_id"]

        if med_id not in meds:
            meds[med_id] = {
                "med_id": med_id,
                "name": row["name"],
                "notes": row["notes"],
                "active_start_date": str(row["start_date"]) if row["start_date"] else None,
                "active_end_date": str(row["end_date"]) if row["end_date"] else None,
                "schedule": {
                    "repeat_type": row["repeat_type"],
                    "day_mask": row["day_mask"],
                    "lead_minutes": row["lead_minutes"] if row["lead_minutes"] is not None else 0,
                    "times": [],
                },
            }

        # Agregamos horas si existen
        hhmm = row["hhmm"]
        if hhmm is not None:
            # hhmm puede venir como datetime.time o como string "HH:MM:SS"
            if hasattr(hhmm, "strftime"):
                time_str = hhmm.strftime("%H:%M")
            else:
                time_str = str(hhmm)[:5]
            meds[med_id]["schedule"]["times"].append(time_str)

    # Si no hay filas, devolvemos lista vacía
    return jsonify(list(meds.values())), 200


@medications_bp.route("/medications", methods=["POST"])
def add_medication():
    data = request.get_json() or {}

    # Campos obligatorios
    required = ["user_id", "name", "times", "repeat_type", "day_mask"]
    if not all(field in data for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    user_id = data["user_id"]
    name = data["name"]
    notes = data.get("notes")

    # Si no mandan start_date, ponemos HOY para evitar el NOT NULL
    start_date = data.get("start_date")
    if not start_date:
        start_date = date.today().isoformat()

    end_date = data.get("end_date")

    # lista de strings "HH:MM"
    times = data.get("times") or []
    if not isinstance(times, list) or len(times) == 0:
        return jsonify({"error": "times must be a non-empty list"}), 400

    repeat_type = data["repeat_type"]
    day_mask = data["day_mask"]
    lead_minutes = int(data.get("lead_minutes", 0))

    conn = get_db()
    cursor = conn.cursor()

    try:
        # 1) Insert en medications
        cursor.execute(
            """
            INSERT INTO medications (user_id, name, notes, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, name, notes, start_date, end_date),
        )
        med_id = cursor.lastrowid

        # 2) Insert en med_schedule_rules
        cursor.execute(
            """
            INSERT INTO med_schedule_rules (med_id, repeat_type, day_mask, lead_minutes)
            VALUES (%s, %s, %s, %s)
            """,
            (med_id, repeat_type, day_mask, lead_minutes),
        )
        rule_id = cursor.lastrowid

        # 3) Insert en med_times (usamos rule_id, NO med_id)
        sort_order = 1
        for t in times:
            cursor.execute(
                """
                INSERT INTO med_times (rule_id, hhmm, sort_order)
                VALUES (%s, %s, %s)
                """,
                (rule_id, t, sort_order),
            )
            sort_order += 1

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("ERROR in add_medication:", e)
        return jsonify({"error": "db_error", "details": str(e)}), 500

    return jsonify({"message": "Medication created", "med_id": med_id}), 201
