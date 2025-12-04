from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt, datetime, os
from ..db import get_db

auth_bp = Blueprint('auth', __name__)
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_key123")


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    birthday = data.get('birthday')

    if not email or not password or not full_name or not birthday:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        return jsonify({"error": "Email already exists"}), 409

    hashed_pw = generate_password_hash(password)

    cur.execute(
        "INSERT INTO users (email, password_hash, full_name, birthday) "
        "VALUES (%s, %s, %s, STR_TO_DATE(%s,'%d/%m/%Y'))",
        (email, hashed_pw, full_name, birthday)
    )
    conn.commit()

    new_user_id = cur.lastrowid

    cur.close()
    conn.close()

    token = jwt.encode(
        {"user_id": new_user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
        JWT_SECRET,
        algorithm="HS256"
    )

    return jsonify({"token": token}), 201



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

    cursor.close()
    conn.close()

    return jsonify({"token": token}), 201


@auth_bp.route("/api/auth/me", methods=["GET"])
def get_profile():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Missing Authorization header"}), 401

    try:
        token = token.replace("Bearer ", "")
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = decoded["user_id"]

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT user_id, email, full_name,
                   DATE_FORMAT(birthday, '%d/%m/%Y') AS birthday
            FROM users
            WHERE user_id = %s
        """, (user_id,))

        profile = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify(profile)

    except Exception as e:
        print("Token decode error:", e)
        return jsonify({"error": "Invalid token"}), 401

@auth_bp.route("/api/auth/delete", methods=["DELETE"])
def delete_account():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Missing token"}), 401

    try:
        token = token.replace("Bearer ", "")
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = decoded["user_id"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({"status": "deleted"}), 200

    except Exception as e:
        print("Delete error:", e)
        return jsonify({"error": "Invalid token"}), 401
