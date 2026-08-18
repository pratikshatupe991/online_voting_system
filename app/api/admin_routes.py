from flask import Blueprint, request, jsonify
from app.models import Admin
from flask import render_template
from app.utils import generate_jwt_token_admin, admin_login_required, verify_password
from app.models import Voter


admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/api/signup', methods=['POST'])
def admin_signup():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
        if not data.get('username'):
            return jsonify({"status": "error", "message": "Missing required field: Username."}), 400
        if not data.get('email'):
            return jsonify({"status": "error", "message": "Missing required field: Email."}), 400
        if not data.get('password'):
            return jsonify({"status": "error", "message": "Missing required field: Password."}), 400

        admin: Admin = Admin.get_by_email(data['email'])
        if admin:
            return jsonify({"status": "error", "message": "Email is already registered, Please Login."}), 409

        new_admin = Admin.add(data['username'], data['email'], data['password'])
        if not new_admin:
            return jsonify({"status": "error", "message": "An error occurred while saving to the database"}), 500

        return jsonify({"status": "success","message": f"Admin created successfully with username: {data['username']}",
                        "data": {"admin_id": new_admin.id, "username": new_admin.username}}), 200

    except Exception as ex:
        error = f"Exception occurred while adding the admin, ex: {ex}"
        print(error)
        return jsonify({"status": "error", "message": error}), 500


@admin_bp.route('/admin/ui/signup', methods=['GET'])
def admin_signup_page():
    return render_template('admin/signup.html')


@admin_bp.route('/admin/api/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"status": "error", "message": "Missing email or password."}), 400
        admin: Admin = Admin.get_by_email(data['email'])
        if not admin:
            return jsonify({"status": "error", "message": "Email is Not registered, Please Sign Up."}), 409

        if not verify_password(admin.password_hash, data['password']):
            return jsonify({"status": "error", "message": "Invalid password."}), 401
        token = generate_jwt_token_admin(admin.id, admin.email)
        return jsonify({"status": "success", "message": "Login successful", "data": {"admin_id": admin.id,
                        "username": admin.username, "token": token}}), 200
    except Exception as ex:
        error = f"Exception occurred during login, ex: {ex}"
        print(error)
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500


@admin_bp.route('/admin/ui/login', methods=['GET'])
def admin_login_page():
    return render_template('admin/login.html')


@admin_bp.route('/admin/api/get_voters', methods=['GET'])
@admin_login_required
def get_all_voters(admin_id: int):
    try:
        admin = Admin.get_by_id(admin_id)
        if not admin:
            return jsonify({"status": "error", "message": "Authorization error. Invalid admin token."}), 400
        voter_data = Voter.get_all_voters()
        return jsonify({"status": "success", "message": "Voters fetched successfully",  "data": voter_data}), 200
    except Exception as ex:
        print(f"Fetch voters error: {ex}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500


@admin_bp.route('/admin/ui/dashboard', methods=['GET'])
def admin_dashboard_page():
    return render_template('admin/dashboard.html')
