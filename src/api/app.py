from pathlib import Path
from flask import Flask
from .routes.pages import pages_bp
from .routes.analysis import analysis_pb
from .services.analysis_service import AnalysisService
from src.forecasting_model import ClimateForecastingModel

def main():
    app = Flask(__name__)

    BASE_DIR = Path(__file__).resolve().parent.parent
    MODELS_DIR = BASE_DIR / "models"
    
    model_path = MODELS_DIR / "regional_climate_lstm.pth"
    scaler_path = MODELS_DIR / "scaler.pkl"

    model = ClimateForecastingModel(seq_len=60, forecast_num=60, model_file=model_path, scaler_file=scaler_path)
    service = AnalysisService(model)

    app.config["MODEL"] = model
    app.config["ANALYSIS-SERVICE"] = service

    # Register Blueprints
    app.register_blueprint(pages_bp)
    app.register_blueprint(analysis_pb, url_prefix="/analysis")

    return app