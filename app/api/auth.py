from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt, datetime, os
from ..db import get_db

auth_bp = Blueprint('auth', __name__)

JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_key123")

@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()

        hashed = generate_password_hash(password)

        cursor.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (email, hashed))
        conn.commit()

        return jsonify({"message": "User created"}), 201

    except Exception as e:
        print("DB Error:", e)
        return jsonify({"error": "Email may already exist"}), 400


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode(
        {"user_id": user["user_id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
        JWT_SECRET,
        algorithm="HS256"
    )

    return jsonify({"token": token})
