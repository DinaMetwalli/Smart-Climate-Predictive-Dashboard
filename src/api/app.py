from pathlib import Path
from flask import Flask
from datetime import timedelta

from .routes.pages import pages_bp
from .routes.analysis import analysis_bp
from .routes.user_sessions import user_bp
from ..utils.database_config import db

from .services.analysis_service import AnalysisService
from .services.user_manager_service import UserManagerService
# from src.forecasting_model import ClimateForecastingModel
from src.temp_model import ClimateForecastingModel

import os

def main():
    app = Flask(__name__)
    app.secret_key = 'very-secret-key'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=3) # Session expires after 3 days

    # Initialise the database once only in the child process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        with app.app_context():
            db.initialise_on_start()

    BASE_DIR = Path(__file__).resolve().parent.parent
    MODELS_DIR = BASE_DIR / "models"
    
    model_path = MODELS_DIR / "regional_climate_lstm.pth"
    scaler_path = MODELS_DIR / "scaler.pkl"

    model = ClimateForecastingModel(seq_len=60, forecast_num=60, model_file=model_path, scaler_file=scaler_path)
    analysis_service = AnalysisService(model)
    user_manager = UserManagerService()

    app.config["MODEL"] = model
    app.config["ANALYSIS-SERVICE"] = analysis_service
    app.config["USER-MANAGER"] = user_manager

    # Register Blueprints
    app.register_blueprint(pages_bp)
    app.register_blueprint(analysis_bp, url_prefix="/analysis")
    app.register_blueprint(user_bp, url_prefix="/api")

    return app