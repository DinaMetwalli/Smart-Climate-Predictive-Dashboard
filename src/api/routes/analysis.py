from flask import Blueprint, request, jsonify, session, render_template, redirect
from flask import current_app

from .utils.auth import authorize

analysis_bp = Blueprint("analysis_bp", __name__)

@analysis_bp.route("/custom", methods=["POST"])
@authorize
def analyse_user_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part."}), 400
    
    analysis_name = request.form.get('analysisName')

    files = request.files.getlist("file")
    filenames = []

    if files is None:
        return jsonify({"error": "No file selected."}), 400
    
    if analysis_name is None:
        return jsonify({"error": "Please provide a name for the analysis."}), 400
    
    print(f"Processing Analysis '{analysis_name}'...")
    
    for file in files:
        print(f"User uploaded file: {file.filename}")
        filenames.append(file.filename)
    
    service = current_app.config["ANALYSIS-SERVICE"]

    try:
        predictions, stats, errors, start_date = service.run_custom_analysis(files, filenames)
        session["predictions"] = predictions
        session["stats"] = stats
        session["errors"] = errors
        session["analysis_meta"] = {
            "type": "custom",
            "name": analysis_name,
            "filenames": filenames,
            "file_count": len(filenames),
            "saved": False,
            "start_date": start_date,
        }

        saved = session["analysis_meta"]["saved"]
        print(f"saved analysis -> {saved}")

        return redirect("/")
    
    except Exception as e:
        print(str(e))
        return render_template("upload.html", error=str(e))

@analysis_bp.route("/custom/save", methods=["POST"])
@authorize
def save_custom_analysis_results():
    
    try:
        user_id = session["user_id"]
        analysis_meta = session["analysis_meta"]
        analysis_name = analysis_meta["name"]
        filenames = analysis_meta["filenames"]
        start_date = analysis_meta["start_date"]
        predictions = session["predictions"]
        stats = session["stats"]
        errors = session["errors"]

        history_service = current_app.config["HISTORY-SERVICE"]
        history_service.save_custom_analysis_results(user_id,
                                                     analysis_name,
                                                     filenames,
                                                     predictions,
                                                     stats,
                                                     errors,
                                                     start_date)

        meta = session["analysis_meta"]
        meta["saved"] = True
        session["analysis_meta"] = meta

        return redirect("/api/user/analysis/history")
    except Exception as e:
        print(str(e))
        return render_template("index.html", error=str(e))

@analysis_bp.route("/live", methods=["GET"])
def analyse_live_request():
    print("User requested live analysis.")

    service = current_app.config["ANALYSIS-SERVICE"]

    try:
        predictions, stats, errors = service.run_live_analysis()
        session["predictions"] = predictions
        session["stats"] = stats
        session["errors"] = errors
        session["analysis_meta"] = {
            "type": "live",
        }
        
        return redirect("/")
    
    except Exception as e:
        return render_template("index.html", error=str(e))

@analysis_bp.route('/predictions/<int:month_index>')
def get_predictions(month_index):

    service = current_app.config["ANALYSIS-SERVICE"]
    
    predictions = session.get("predictions")
    meta = session.get("analysis_meta")
    start_date = None
    
    if meta["type"] == "custom":
        start_date = meta["start_date"]
    
    try:
        response = service.get_analysis_results(month_index, predictions, start_date)
        return jsonify(response)
    
    except Exception as e:
        print(str(e))
        return render_template("index.html", error=str(e))