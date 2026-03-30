from flask import Blueprint, render_template

pages_bp = Blueprint("pages_bp", __name__)

@pages_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@pages_bp.route("/upload", methods=["GET"])
def load_upload_page():
    return render_template("upload.html")

@pages_bp.route("/charts", methods=["GET"])
def load_charts_page():
    return render_template("charts.html")

@pages_bp.route("/history", methods=["GET"])
def load_history_page():
    return render_template("history.html")

@pages_bp.route("/about", methods=["GET"])
def load_about_page():
    return render_template("about.html")

@pages_bp.route("/login", methods=["GET"])
def load_login_page():
    return render_template("login.html")

@pages_bp.route("/register", methods=["GET"])
def load_register_page():
    return render_template("register.html")

@pages_bp.route("/account", methods=["GET"])
def load_user_account_page():
    return render_template("user.html")