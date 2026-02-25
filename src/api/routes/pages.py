from flask import Blueprint, render_template

pages_bp = Blueprint("pages_bp", __name__)

@pages_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@pages_bp.route("/live", methods=["GET"])
def load_history_page():
    return render_template("live.html")

@pages_bp.route("/about", methods=["GET"])
def load_about_page():
    return render_template("about.html")