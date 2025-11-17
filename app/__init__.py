from flask import Flask
from .db import get_db
from .api.device_events import device_events_bp

def create_app():
    app = Flask(__name__)

    @app.route("/health")
    def health():
        try:
            get_db()
            return {"db": True, "status": "ok"}
        except:
            return {"db": False, "status": "db_error"}

    app.register_blueprint(device_events_bp)
    return app
