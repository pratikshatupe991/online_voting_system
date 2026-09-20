import json
import os
from flask import Blueprint, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import config
from app.models import Voter, Election, Candidate, Vote
from app.utils import admin_login_required, hash_password, verify_password, generate_jwt_token_voter
from config import allowed_file

voter_bp = Blueprint('voter', __name__)


@voter_bp.route('/voter/api/voter_sign_up', methods=['POST'])
def voter_sign_up():
    try:
        prn = request.form.get('prn')
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')

        if not all([prn, email, name, password]):
            return jsonify({"status": "error", "message": "PRN, Email, Password and Name are required."}), 400

        if 'profile_img' not in request.files:
            return jsonify({"status": "error", "message": "No image file uploaded."}), 400

        file = request.files['profile_img']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No selected file."}), 400

        if not allowed_file(file.filename):
            return jsonify(
                {"status": "error", "message": "Invalid image format. Only JPG, JPEG, and PNG are allowed."}), 400

        file_path = os.path.join(os.getcwd(), 'master_prn_data.json')
        with open(file_path, 'r') as file_obj:
            master_list = json.load(file_obj)

        if prn not in master_list:
            return jsonify({"status": "error", "message": "Invalid PRN. You are not authorized."}), 403

        if master_list[prn] != email:
            return jsonify({"status": "error", "message": "Email does not match the registered PRN."}), 403

        if Voter.get_by_prn(prn):
            return jsonify({"status": "error", "message": "User with this PRN is already registered."}), 409

        filename = secure_filename(f"{prn}_{file.filename}")
        os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)  # Creates the folder if it doesn't exist
        save_path = os.path.join(config.UPLOAD_FOLDER, filename)
        file.save(save_path)

        db_image_path = f"/static/uploads/voters/{filename}"
        hashed_password = hash_password(password)
        new_voter: Voter = Voter.add(prn, name, email, hashed_password, db_image_path)
        data = {"id": new_voter.id, "name": new_voter.name, "email": new_voter.email, "prn": prn}
        return jsonify({"status": "success", "message": "Voter registered successfully!", "data": data}), 200
    except Exception as ex:
        print(f"Signup error: {ex}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500


@voter_bp.route('/voter/ui/signup', methods=['GET'])
def voter_signup_page():
    return render_template('voter/signup.html')


@voter_bp.route('/voter/api/login', methods=['POST'])
def voter_login():
    try:
        data = request.get_json()
        if not data or not data.get('prn') or not data.get('password'):
            return jsonify({"status": "error", "message": "Missing email or password."}), 400
        voter: Voter = Voter.get_by_prn(data['prn'])
        if not voter:
            return jsonify({"status": "error", "message": "PRN is Not registered, Please Sign Up."}), 409

        if not verify_password(voter.password_hash, data['password']):
            return jsonify({"status": "error", "message": "Invalid password."}), 401
        token = generate_jwt_token_voter(voter.id, voter.prn)
        return jsonify({"status": "success", "message": "Login successful", "data": {"voter_id": voter.id,
                        "username": voter.name, "token": token}}), 200
    except Exception as ex:
        error = f"Exception occurred during login, ex: {ex}"
        print(error)
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500


@voter_bp.route('/voter/ui/login', methods=['GET'])
def voter_login_page():
    return render_template('voter/login.html')


@voter_bp.route('/voter/ui/dashboard', methods=['GET'])
def voter_dashboard_page():
    return render_template('voter/dashboard.html')


@voter_bp.route('/voter/api/get_participant_image/<prn>', methods=['GET'])
def get_participant_image(prn: str):
    try:
        voter: Voter = Voter.get_by_prn(prn)
        if not voter:
            return jsonify({"status": "error", "message": f"Voter/Participant does not exist with PRN: {prn}."}), 404
        cwd_path = os.getcwd()
        relative_path = voter.image_path.lstrip('/\\')
        img_path = os.path.normpath(os.path.join(cwd_path, relative_path))
        if not os.path.exists(img_path):
            return jsonify({"status": "error", "message": "Image not found on server."}), 404
        return send_file(img_path)
    except Exception as ex:
        print(f"Fetch participant image error: {ex}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500


@voter_bp.route('/voter/ui/candidates_listing', methods=['GET'])
def candidates_listing_page():
    return render_template('voter/candidates_listing.html')


@voter_bp.route('/voter/api/cast_vote', methods=['POST'])
def cast_vote():
    try:
        data = request.get_json()
        if not data or not data.get('voter_id') or not data.get('election_id'):
            return jsonify({"status": "error", "message": "Missing email or password."}), 400
        if "candidate_id" not in data.keys():
            return jsonify({"status": "error", "message": "Required parameter candidate id missing."}), 400
        voter: Voter = Voter.get_by_id(data['voter_id'])
        if not voter:
            return jsonify({"status": "error", "message": "PRN is Not registered, Please Sign Up."}), 409

        election: Election = Election.get_by_id(data['election_id'])
        if not election:
            return jsonify({"status": "error", "message": f"Election does not exist with id:"
                                                          f" {data['election_id']}."}), 404

        if not election.is_active():
            return jsonify({"status": "error", "message": f"Election is not active election id: {election.id}."}), 404

        if data['candidate_id']:
            candidate = Candidate.get_by_candidate_election_id(data['candidate_id'], election.id)
            if not candidate:
                return jsonify({"status": "error", "message": f"Candidate does not exist with candidate id:"
                                                              f" {data['candidate_id']}."}), 404

        already_voted_candidate = Vote.get_by_voter_and_election(voter.id, election.id)
        if already_voted_candidate:
            return jsonify({"status": "error", "message": f"Voter has already casted vote."}), 404
        Vote.add(voter.id, data['candidate_id'], election.id)
        return jsonify({"status": "success", "message": "Vote Casted successful"}), 200
    except Exception as ex:
        print(f"Fetch participant image error: {ex}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500
