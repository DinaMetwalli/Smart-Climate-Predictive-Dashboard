from flask import Blueprint, session, jsonify

charts_bp = Blueprint("charts_bp", __name__)

@charts_bp.route("/charts/stats", methods=["GET"])
def get_continent_stats_chart():
    print("Fetching per-continent performance metrics...")

    try:
        stats = session.get("stats")
        return jsonify(stats if stats else {})
    
    except Exception as e:
        return str(e)

@charts_bp.route("/charts/preds", methods=["GET"])
def get_continent_preds_chart():
    print("Fetching per-continent predictions...")

    try:
        preds = session.get("predictions")
        return jsonify(preds if preds else {})
    
    except Exception as e:
        return str(e)

@charts_bp.route("/charts/errors", methods=["GET"])
def get_continent_errors_chart():
    print("Fetching per-continent error accumulation...")

    try:
        errors = session.get("errors")
        return jsonify(errors if errors else {})
    
    except Exception as e:
        return str(e)
