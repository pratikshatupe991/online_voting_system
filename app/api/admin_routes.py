from flask import Blueprint, request, jsonify

import config
from app.models import Admin, Election, Candidate
from flask import render_template
from app.utils import generate_jwt_token_admin, admin_login_required, verify_password
from app.models import Voter
import datetime

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


@admin_bp.route('/admin/ui/dashboard/voters', methods=['GET'])
def admin_voters_page():
    return render_template('admin/voters.html')


@admin_bp.route('/admin/api/add_election', methods=['POST'])
@admin_login_required
def add_election(admin_id: int):
    try:
        admin = Admin.get_by_id(admin_id)
        if not admin:
            return jsonify({"status": "error", "message": "Authorization error. Invalid admin token."}), 400

        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid request. No data provided."}), 400

        title = data.get('title')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')

        if not all([title, start_time_str, end_time_str]):
            return jsonify({"status": "error", "message": "title, start_time_str, end_time_str are required."}), 400

        start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
        end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')

        if end_time <= start_time:
            return jsonify({"status": "error", "message": "End time must be after the start time."}), 400

        existing_election = Election.get_by_title(title)
        if existing_election:
            return jsonify({"status": "error", "message": f"Election already exist with name: {title}."}), 404

        election = Election.add(title, start_time, end_time)
        if not election:
            return jsonify({"status": "error", "message": f"Currently unable to add election: {title}."}), 404

        return jsonify({"status": "success",  "message": "Election created successfully."}), 201
    except Exception as ex:
        print(f"Fetch voters error: {ex}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500


@admin_bp.route('/admin/ui/dashboard/elections', methods=['GET'])
def elections_page():
    return render_template('admin/elections.html')


@admin_bp.route('/admin/api/get_elections', methods=['GET'])
@admin_login_required
def get_elections(admin_id: int):
    try:
        admin = Admin.get_by_id(admin_id)
        if not admin:
            return jsonify({"status": "error", "message": "Authorization error. Invalid admin token."}), 400
        elections = Election.get_all()

        if elections is None:
            return jsonify({"status": "error", "message": "Failed to fetch elections."}), 404

        election_list = []
        now = datetime.datetime.now()
        for election in elections:
            if now < election.start_ts:
                current_status = "Upcoming"
            elif election.start_ts <= now <= election.end_ts:
                current_status = "Live"
            else:
                current_status = "Completed"

            election_list.append({"id": election.id, "title": election.title,
                                  "start_time": election.start_ts.strftime('%Y-%m-%dT%H:%M'),
                                  "end_time": election.end_ts.strftime('%Y-%m-%dT%H:%M'), "status": current_status})
        return jsonify({"status": "success", "data": election_list}), 200
    except Exception as ex:
        print(f"Fetch elections error: {ex}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500


@admin_bp.route('/admin/api/add_candidate', methods=['POST'])
@admin_login_required
def add_candidate(admin_id: int):
    try:
        admin = Admin.get_by_id(admin_id)
        if not admin:
            return jsonify({"status": "error", "message": "Authorization error. Invalid admin token."}), 400

        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid request. No data provided."}), 400

        election_id = data.get('election_id')
        prn = data.get('prn')

        if not all([election_id, prn]):
            return jsonify({"status": "error", "message": "election_id, prn are required."}), 400

        if not Voter.get_by_prn(prn):
            return jsonify({"status": "error", "message": "Invalid PRN."}), 400

        existing_election = Election.get_by_id(election_id)
        if not existing_election:
            return jsonify({"status": "error", "message": f"Election does not exist with id: {election_id}."}), 404

        existing_candidate = Candidate.get_by_prn_and_election_id(prn, election_id)
        if existing_candidate:
            return jsonify({"status": "error", "message": f"Candidate already exist with prn: {prn}."}), 404

        candidate = Candidate.add(prn, election_id)
        if not candidate:
            return jsonify({"status": "error", "message": f"Currently unable to add candidate with prn: {prn}."}), 404

        return jsonify({"status": "success",  "message": "Election created successfully."}), 201
    except Exception as ex:
        print(f"Fetch voters error: {ex}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500


@admin_bp.route('/admin/api/get_candidates/<election_id>', methods=['GET'])
@admin_login_required
def get_candidates(admin_id: int, election_id: int):
    try:
        admin = Admin.get_by_id(admin_id)
        if not admin:
            return jsonify({"status": "error", "message": "Authorization error. Invalid admin token."}), 400

        existing_election = Election.get_by_id(election_id)
        if not existing_election:
            return jsonify({"status": "error", "message": f"Election does not exist with id: {election_id}."}), 404

        candidates: list[Candidate] = Candidate.get_by_election(election_id)
        res_data = []
        for candidate in candidates:
            voter: Voter = Voter.get_by_prn(candidate.prn)
            voter_img_url = f"{config.BASE_URL}//voter/api/get_participant_image/{candidate.prn}"
            res_data.append({"prn": candidate.prn, "name": voter.name, "voter_img_url": voter_img_url})
        return jsonify({"status": "success", "data": res_data}), 200
    except Exception as ex:
        print(f"Fetch elections error: {ex}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500

