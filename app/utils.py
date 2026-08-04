from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app


def generate_jwt_token(admin_id, email):
    """
    Generates a 24-hour JWT token for the authenticated admin.
    """
    # Using timezone-aware UTC datetime
    now = datetime.datetime.now(datetime.timezone.utc)

    payload = {
        'admin_id': admin_id,
        'email': email,
        'exp': now + datetime.timedelta(hours=24)
    }
    # Create the token using the app's secret key
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token


def admin_login_required(f):
    """
    Decorator to protect routes. Extracts the token from the request header,
    verifies it, and passes the current_admin_id to the route function.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check for token in the Authorization header (Format: "Bearer <token>")
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"status": "error", "message": "Token is missing. Please log in."}), 401

        try:
            # Decode the token
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_admin_id = data['admin_id']

        except jwt.ExpiredSignatureError:
            return jsonify({"status": "error", "message": "Token has expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"status": "error", "message": "Invalid token. Please log in again."}), 401

        # Pass the extracted ID to the wrapped route
        return f(current_admin_id, *args, **kwargs)

    return decorated


def hash_password(password):
    """
    Hashes a plain-text password using a secure algorithm (default is scrypt).
    """
    return generate_password_hash(password)


def verify_password(password_hash, password):
    """
    Checks a plain-text password against the stored hash.
    Returns True if they match, False otherwise.
    """
    return check_password_hash(password_hash, password)
