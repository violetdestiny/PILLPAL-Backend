from flask import Flask
from .db import get_db
from .api.device_events import device_events_bp
from .api.auth import auth_bp
from .api.medications import med_bp
from .api.settings import settings_bp
from .api.device_poll import device_poll_bp
from src.api.alarm import alarm_bp
from src.scheduler.medication_scheduler import start_scheduler
from src.api.device_alert import device_alert_bp


def create_app():
    app = Flask(__name__)

    @app.route("/health")
    def health():
        try:
            get_db()
            return {"db": True, "status": "ok"}
        except:
            return {"db": False, "status": "db_error"}

    # Registering blueprints
    app.register_blueprint(device_events_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(med_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(device_poll_bp)
    app.register_blueprint(alarm_bp)
    start_scheduler()
    app.register_blueprint(device_alert_bp, url_prefix="/api")


    return app
