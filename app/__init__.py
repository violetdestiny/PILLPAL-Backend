from flask import Flask
from .db import get_db
from .api.device_events import device_events_bp
from .api.auth import auth_bp
from .api.medications import med_bp

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


    return app
