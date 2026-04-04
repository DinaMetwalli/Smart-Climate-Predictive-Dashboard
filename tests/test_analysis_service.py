import pytest
import os
from pathlib import Path
from src.api.services.analysis_service import AnalysisService
from unittest.mock import MagicMock
from datetime import datetime

BASE_DIR = Path.cwd().parent
FILE_PATH = BASE_DIR / "Smart-Climate-Predictive-Dashboard" / "data" / "sources" / "mock"
CORRECT_CSV_FILE = "Correct_CSV_File.csv"

@pytest.fixture
def service():
    mock_model = MagicMock()
    mock_loader = MagicMock()
    mock_custom_loader = MagicMock()
    return AnalysisService(mock_model, mock_loader, mock_custom_loader)

def test_run_custom_analysis(service):
    file = os.path.join(FILE_PATH, CORRECT_CSV_FILE)

    # Mock the custom loader's returns
    service.custom_loader.load_dataset_from_file.return_value = {
        "africa": MagicMock()
    }

    # Mock the data loader's returns
    service.loader.load_data.return_value = (MagicMock(), datetime(2024, 1, 1))

    # Mock the model's predictions
    service.model.predict_future.side_effect = [
        [1.2, 0.5, 0.8], # First call: predictions (test_future=True)
        ({"rmse": 0.3}, [0.1, 0.2]) # Second call: stats, errors (test_future=False)
    ]

    combined_preds, combined_stats, combined_errors, start_date = service.run_custom_analysis(
        custom_files=[file], filenames=[CORRECT_CSV_FILE]
    )
    
    assert isinstance(combined_preds, dict)
    assert isinstance(combined_stats, dict)
    assert isinstance(combined_errors, dict)
    assert isinstance(start_date, datetime)
    assert "africa" in combined_preds

def test_get_live_analysis_results(service):
    predictions = {"africa": [1.2, 0.5, 0.8]}
    result = service.get_analysis_results(0, predictions, start_date=None)

    # Assert the month index fetched result matches with predictions fed in
    assert result["month_index"] == 0
    assert result["continents"]["Africa"] == 1.2

def test_get_custom_analysis_results(service):
    predictions = {"africa": [1.2]}
    start = datetime(2024, 1, 1)
    result = service.get_analysis_results(0, predictions, start_date=start)

    # Assert custom analysis fetched result starts from the correct month index accroding to custom dataset
    assert result["date"] == "2024-01"