from flask import Blueprint, request, jsonify, current_app, session, redirect, url_for, render_template

user_bp = Blueprint("user_bp", __name__)
    
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
    
    # Extract parameters from request form
    username = request.form.get('username')
    password = request.form.get('password')
    same_password = request.form.get('re-enter-password')
    
    print(f"Registering user {username}...")

    # Validate all needed parameters are present in request
    if not username or not password:
        error = "Username and password required."
        return render_template("register.html", error = error)

    user_manager = current_app.config["USER-MANAGER"]

    try:
        result = user_manager.register_user(username, password, same_password)
        if result:
            return redirect("/login")
    except Exception as e:
        return render_template("register.html", error=str(e))

@user_bp.route("/users/login", methods=["POST"])
def login_user():
    """Authenticate a user."""
    
    # Extract parameters from request form
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        error = "Username and password required."
        return render_template("login.html", error = error)

    user_manager = current_app.config["USER-MANAGER"]

    try:
        user = user_manager.login_user(username, password)
        if user:
            
            session.clear()
            
            # Store user info in session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session.permanent = True

            return redirect(url_for("pages_bp.index"))
        
        error="Invalid username or password."
        return render_template("login.html", error = error)
    
    except Exception as e:
        return render_template("login.html", error=str(e))
    
@user_bp.route("/users/logout", methods=["POST"])
def logout_user():
    """Logout user and clear session."""
    
    session.clear()
    return redirect(url_for("pages_bp.index"))
    
@user_bp.route("/user/delete", methods=["POST"])
def delete_user():
    """Deactivate a user account."""

    user_id = session["user_id"]
    
    if not user_id:
        error = "Error: no user is logged in."
        return render_template("login.html", error = error)
    
    user_manager = current_app.config["USER-MANAGER"]

    try:
        user_manager.delete_user(user_id)
        session.clear()

        return render_template("index.html")
    except Exception as e:
        return render_template("user.html", error=str(e))
    
@user_bp.route("/user/update/username", methods=["POST"])
def change_username():
    """Change the user account's username"""
    user_id = session["user_id"]
    username = request.form.get('username')
    
    # Validate all needed parameters are present in request
    if not username:
        error = "New username is required."
        return render_template("user.html", error = error)

    user_manager = current_app.config["USER-MANAGER"]

    try:
        result = user_manager.update_username(user_id, username)
        if result:
            session.clear()
            session['user_id'] = user_id
            session['username'] = username
            return render_template("user.html", success="Username updated.")
    except Exception as e:
        return render_template("user.html", error=str(e))

@user_bp.route("/user/update/password", methods=["POST"])
def change_password():
    """Change the user account's password"""
    user_id = session["user_id"]
    curr_password = request.form.get('curr-password')
    new_password = request.form.get('new-password')
    
    # Validate all needed parameters are present in request
    if not curr_password:
        error = "Current password is required."
        return render_template("user.html", error = error)
    elif not new_password:
        error = "New password is required."
        return render_template("user.html", error = error)

    user_manager = current_app.config["USER-MANAGER"]

    try:
        result = user_manager.update_password(user_id, curr_password, new_password)
        if result:
            success = "Update successful. Please login using your new password."
            return render_template("login.html", success = success)
        else:
            error = "There was an issue updating your password."
            return render_template("user.html", error = error)
    except Exception as e:
        return render_template("user.html", error = str(e))