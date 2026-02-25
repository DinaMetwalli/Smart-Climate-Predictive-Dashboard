from flask import Blueprint, request, jsonify
from flask import current_app

from .utils.auth import authorize

analysis_bp = Blueprint("analysis_bp", __name__)

@analysis_bp.route("/custom", methods=["POST"])
@authorize
def analyse_user_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part."}), 400
    
    files = request.files.getlist("file")
    filenames = []

    if files is None:
        return jsonify({"error": "No file selected."}), 400
    
    for file in files:
        print(f"User uploaded file: {file.filename}")
        filenames.append(file.filename)
    
    service = current_app.config["ANALYSIS-SERVICE"]

    try:
        predictions = service.run_custom_analysis(files, filenames)

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