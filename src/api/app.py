from pathlib import Path
from flask import Flask
from flask_session import Session
from datetime import timedelta

from .routes.pages import pages_bp
from .routes.analysis import analysis_bp
from .routes.user_sessions import user_bp
from .routes.analysis_history import user_history_bp
from .routes.analysis_charts import charts_bp
from ..utils.database_config import db

from .services.analysis_service import AnalysisService
from .services.user_manager_service import UserManagerService
from .services.analysis_history_service import AnalysisHistoryService
from src.forecasting_model import ClimateForecastingModel
from data.preparation.data_loader import DataLoader
from data.preparation.custom_data_retriever import CustomDatasetRetriever

import os

def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = 'very-secret-key'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=3) # Session expires after 3 days

    if test_config is not None:
        # Override with test config, skip all heavy initialisation
        app.config.update(test_config)
    else:

    # Only initialise real services in non-test mode
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            with app.app_context():
                db.initialise_on_start()

        BASE_DIR = Path(__file__).resolve().parent.parent
        MODELS_DIR = BASE_DIR / "models"
        
        model_path = MODELS_DIR / "regional_climate_lstm.pth"
        scaler_path = MODELS_DIR / "scaler.pkl"

        model = ClimateForecastingModel(seq_len=120, forecast_num=60, model_file=model_path, scaler_file=scaler_path)
        data_loader = DataLoader()
        custom_retriever = CustomDatasetRetriever()
        analysis_service = AnalysisService(model, data_loader, custom_retriever)
        user_manager = UserManagerService()
        analysis_history_service = AnalysisHistoryService()

        app.config["MODEL"] = model
        app.config["ANALYSIS-SERVICE"] = analysis_service
        app.config["HISTORY-SERVICE"] = analysis_history_service
        app.config["USER-MANAGER"] = user_manager
    
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_DIR"] = "./flask_sessions"
    Session(app)

    # Register Blueprints
    app.register_blueprint(pages_bp)
    app.register_blueprint(analysis_bp, url_prefix="/analysis")
    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(user_history_bp, url_prefix="/api")
    app.register_blueprint(charts_bp, url_prefix="/api")

    return app