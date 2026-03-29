from flask import Blueprint, current_app, session, request, render_template, redirect

from .utils.auth import authorize

user_history_bp = Blueprint("user_history_bp", __name__)

@user_history_bp.route("/user/analysis/history")
@authorize
def analysis_history():

    user_id = session['user_id']
    history_service = current_app.config["HISTORY-SERVICE"]
    error = request.args.get("error")

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
        
        return render_template("history.html", analyses=analyses, error=error)
    except Exception as e:
        return render_template("history.html", error=str(e))

@user_history_bp.route("/user/analysis/history/select")
@authorize
def analysis_prediction_values():

    analysis_id = request.args.get("analysis_id")

    history_service = current_app.config["HISTORY-SERVICE"]

    try:
        predictions = history_service.get_prediction_values(analysis_id)
        session["predictions"] = dict(predictions)

        meta = session["analysis_meta"]
        meta["saved"] = True
        session["analysis_meta"] = meta
        
        return render_template("index.html")
    
    except Exception as e:
        print(str(e))
        return render_template("history.html", error=str(e))
    
@user_history_bp.route("/user/analysis/history/delete", methods=["POST"])
@authorize
def delete_analysis():

    analysis_ids = None
    history_service = current_app.config["HISTORY-SERVICE"]

    try:
        analysis_ids = request.form.getlist("analysis_id_select")

        if analysis_ids:
            history_service.delete_analysis(analysis_ids)
            return redirect("/api/user/analysis/history")
        else:
            error = "Please select an analysis to delete first."
            return redirect(f"/api/user/analysis/history?error={error}")
    
    except Exception as e:
        print(str(e))
        
        error = "There was an error deleting the selected analyses."
        return redirect(f"/api/user/analysis/history?error={error}")
    
@user_history_bp.route("/user/analysis/history/delete/all", methods=["POST"])
@authorize
def delete_all_analyses():

    user_id = session['user_id']
    history_service = current_app.config["HISTORY-SERVICE"]

    try:
        history_service.delete_all_analyses(user_id)
        return redirect("/api/user/analysis/history")
    
    except Exception as e:
        print(str(e))
        
        error = "There was an error deleting your analyses."
        return redirect(f"/api/user/analysis/history?error={error}")