from flask import Blueprint, request, jsonify, session, render_template, redirect
from flask import current_app
import datetime
from dateutil.relativedelta import relativedelta

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
        predictions, stats, errors = service.run_custom_analysis(files, filenames)
        session["predictions"] = predictions
        session["stats"] = stats
        session["errors"] = errors
        session["analysis_meta"] = {
            "type": "custom",
            "name": analysis_name,
            "filenames": filenames,
            "file_count": len(filenames),
            "saved": False,
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
        predictions = session["predictions"]

        history_service = current_app.config["HISTORY-SERVICE"]
        history_service.save_custom_analysis_results(user_id, analysis_name, filenames, predictions)

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

    predictions = session.get("predictions")

    current_time = datetime.datetime.today() 
    date = current_time + relativedelta(months=month_index)
    date = date.strftime('%Y-%m')

    continent_map = {
        "North America": "northAmerica",
        "South America": "southAmerica",
        "Europe": "europe",
        "Africa": "africa",
        "Asia": "asia",
        "Oceania": "oceania"
    }

    continents = {}

    for display_name, key in continent_map.items():
        if predictions:
            preds_list = predictions.get(key)
            if preds_list and len(preds_list) > month_index:
                continents[display_name] = preds_list[month_index]
            else:
                continents[display_name] = None
        else:
            continents[display_name] = None

    response = {
        "month_index": month_index,
        "date": date,
        "continents": continents
    }
    
    return jsonify(response)
