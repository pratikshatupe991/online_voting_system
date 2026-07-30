from flask import Blueprint, request, jsonify
from app.models import Admin
from flask import render_template

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
