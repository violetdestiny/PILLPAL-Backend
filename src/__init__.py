from flask import Flask
from .db import get_db

def create_app():
    app = Flask(__name__)
    app.config["DEBUG"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = True

    @app.route("/health")
    def health():
        try:
            conn = get_db()
            conn.cursor()
            return {"db": True, "status": "ok"}
        except Exception:
            return {"db": False, "status": "db_error"}

    from .api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from .api.medications import medications_bp
    app.register_blueprint(medications_bp, url_prefix="/api")

    from .api.events import api_events
    app.register_blueprint(api_events, url_prefix="/api")


    return app
