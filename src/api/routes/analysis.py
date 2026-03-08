from flask import Blueprint, request, jsonify, session
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
    history_service = current_app.config["HISTORY-SERVICE"]

    try:
        predictions = service.run_custom_analysis(files, filenames)
        
        user_id = session['user_id']
        history_service.save_custom_analysis_results(user_id, analysis_name, filenames)

        return jsonify({
            "message" : "File processed successfully.",
            "data" : predictions
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@analysis_bp.route("/live", methods=["GET"])
def analyse_live_request():
    print("User requested live analysis.")

    service = current_app.config["ANALYSIS-SERVICE"]
    regions = ['africa', 'asia', 'europe', 'northAmerica', 'southAmerica', 'oceania']

    try:
        predictions = service.run_live_analysis(regions)
        return jsonify({
            "message": "Live analysis completed successfully.",
            "data": predictions
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Temporary endpoint with dummy data to connect map with output values for testing! (will be changed later)
@analysis_bp.route('/predictions/<int:month_index>')
def get_predictions(month_index):
    predictions = {
        "month_index": month_index,
        "date": "2026-06", # Should be calculated from current + the prediction's month index
        "continents": {
            "North America": 0.45,
            "South America": 0.32,
            "Europe": 0.58,
            "Africa": 0.41,
            "Asia": 0.52,
            "Oceania": 0.38,
            "Antarctica": 0.25
        }
    }
    return jsonify(predictions)
