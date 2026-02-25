from flask import Blueprint, request, jsonify, current_app
from src.utils.database_config import db

user_bp = Blueprint("user_bp", __name__)

@user_bp.route("/users", methods=["GET"])
def get_all_users():
    """
    Get all active users.
    """
    print("Fetching all users...")

    user_manager = current_app.config["USER-MANAGER"]

    try:
        users = user_manager.get_all_users()
        if users:
            return jsonify({"success": True, 'users': users}), 200
        return jsonify({"success": False, "error": "No users registered."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@user_bp.route("/users/<username>", methods=["POST"])
def get_user(username):
    """Get a specific user from the database."""

    print(f"Fetching user {username}...")

    user_manager = current_app.config["USER-MANAGER"]

    try:
        user = user_manager.get_user(username)
        if user:
            return jsonify({"success": True, 'user': user}), 200
        return jsonify({"success": False, "error": "User not found."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@user_bp.route("/users/register", methods=["POST"])
def register_user():
    """Register a user and commit to the database."""
    
    # Extract parameters from request body
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    print(f"Registering user {username}...")

    # Validate all needed parameters are present in request
    if not username or not password:
        return jsonify({"success": False, "error": "Username and password required"}), 400

    user_manager = current_app.config["USER-MANAGER"]

    try:
        result = user_manager.register_user(username, password)
        if result:
            return jsonify({"success": True, "message": "User registered"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@user_bp.route("/users/login", methods=["POST"])
def login_user():
    """Authenticate a user."""
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"success": False, "error": "Username and password required"}), 400

    user_manager = current_app.config["USER-MANAGER"]

    try:
        user = user_manager.login_user(username, password)
        if user:
            return jsonify({"success": True, "user": user}), 200
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@user_bp.route("/users/delete", methods=["POST"])
def delete_user():
    """Deactivate a user account."""

    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "User ID required in request"}), 400
    
    user_manager = current_app.config["USER-MANAGER"]

    try:
        user_manager.delete_user(user_id)
        return jsonify({"success": True, "message": "Deleted user successfully."}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500