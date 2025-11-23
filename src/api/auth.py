from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from src.db import get_db

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    full_name = data.get("full_name")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    timezone = data.get("timezone", "UTC")
    birth_date = data.get("birth_date")

    if not (full_name and username and email and password):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        return jsonify({"error": "Email already registered"}), 400

    hashed_pw = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
        (email, hashed_pw)
    )
    conn.commit()

    user_id = cursor.lastrowid

    cursor.execute(
        """INSERT INTO user_profiles (user_id, full_name, username, timezone, birth_date)
           VALUES (%s, %s, %s, %s, %s)""",
        (user_id, full_name, username, timezone, birth_date)
    )
    conn.commit()

    return jsonify({
        "user_id": user_id,
        "email": email,
        "full_name": full_name,
        "username": username,
        "timezone": timezone
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """SELECT users.user_id, users.password_hash, user_profiles.full_name,
                  user_profiles.username, user_profiles.timezone
           FROM users
           JOIN user_profiles ON users.user_id = user_profiles.user_id
           WHERE email=%s""",
        (email,)
    )
    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    user_id, password_hash, full_name, username, timezone = user

    if not check_password_hash(password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "user_id": user_id,
        "email": email,
        "full_name": full_name,
        "username": username,
        "timezone": timezone
    }), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    return jsonify({"error": "Not implemented (JWT removed)"}), 200
