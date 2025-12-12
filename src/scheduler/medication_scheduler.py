from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
from src.db import get_db

device_alert_state = {}  # device_id → True/False


def check_medications():
    """
    Runs every minute. Checks if a scheduled dose matches the current time.
    If yes → sets device_alert_state[device_id] = True
    """
    now_dt = datetime.now(timezone.utc)
    now_date = now_dt.date().isoformat()
    now_time = now_dt.strftime("%H:%M")

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT di.instance_id, di.med_id, di.scheduled_at, di.status,
               m.user_id,
               dp.device_id
        FROM dose_instances di
        JOIN medications m ON di.med_id = m.med_id
        JOIN device_pairings dp ON dp.user_id = m.user_id AND dp.active = 1
        WHERE di.status = 'scheduled'
          AND DATE(di.scheduled_at) = %s
          AND TIME_FORMAT(di.scheduled_at, '%%H:%%i') = %s
    """, (now_date, now_time))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    for row in rows:
        device_id = row["device_id"]
        print(f"[SCHEDULER] Triggering alert for device {device_id}")
        device_alert_state[str(device_id)] = True


def get_alert_state(device_id):
    return device_alert_state.get(str(device_id), False)


def clear_alert(device_id):
    device_alert_state[str(device_id)] = False


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_medications, "interval", minutes=1)
    scheduler.start()
    print("[SCHEDULER] started.")
