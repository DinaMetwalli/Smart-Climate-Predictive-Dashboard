from flask import Blueprint, request, jsonify
from flask import current_app

analysis_pb = Blueprint("analysis_pb", __name__)

@analysis_pb.route("/custom", methods=["POST"])
def analyse_user_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part."}), 400
    
    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    
    print(f"User uploaded file: {file.filename}")
    service = current_app.config["ANALYSIS-SERVICE"]

    try:
        predictions = service.run_custom_analysis([file], [file.filename])

        return jsonify({
            "message" : "File processed successfully.",
            "data" : predictions
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400