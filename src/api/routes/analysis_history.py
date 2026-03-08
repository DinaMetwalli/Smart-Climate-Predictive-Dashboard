from flask import Blueprint, request, jsonify, current_app, session, redirect, url_for, render_template

from .utils.auth import authorize

user_history_bp = Blueprint("user_history_bp", __name__)

@user_history_bp.route("/user/analysis/history")
@authorize
def analysis_history():

    user_id = session['user_id']

    history_service = current_app.config["HISTORY-SERVICE"]

    try:
        rows = history_service.get_user_analyses(user_id)
        analyses = [
            {
                "id": row[0],
                "name": row[1],
                "created_at": row[2],
                "user_id": row[3]
            }
            for row in rows
        ]
        
        return render_template("history.html", analyses=analyses)
    except Exception as e:
        return render_template("history.html", error=str(e))