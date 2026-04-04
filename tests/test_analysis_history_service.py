import pytest
from unittest.mock import patch, call
from collections import defaultdict
from datetime import datetime
from src.api.services.analysis_history_service import AnalysisHistoryService

@pytest.fixture
def service():
    return AnalysisHistoryService()

@patch("src.api.services.analysis_history_service.db")
def test_save_custom_analysis_results(mock_db, service):
    mock_db.execute_fetch_and_commit.return_value = ("some-analysis-uuid",)
    mock_db.execute_and_fetch_one.return_value = ("some-region-uuid",)

    result = service.save_custom_analysis_results(
        user_id="user-uuid",
        analysis_name="Test Analysis",
        filenames=["africa.csv"],
        predictions={"africa": [1.2, 0.5]},
        stats={"africa": {"rmse": 0.3, "mean_bias": 0.1, "pearson_corr": 0.9}},
        errors={"africa": [0.1, 0.2]},
        start_date=datetime(2024, 1, 1)
    )

    # Assert analysis is saved and expected DB calls were made
    assert result == True
    assert mock_db.execute_many_and_commit.call_count == 3 # Predictions, Stats and Errors

@patch("src.api.services.analysis_history_service.db")
def test_get_analysis_values(mock_db, service):
    mock_db.execute_and_fetch_all.side_effect = [
        # Predictions result
        [("africa", "pred-uuid", 1, 1.2, "analysis-uuid", "region-uuid"),
         ("africa", "pred-uuid", 2, 0.5, "analysis-uuid", "region-uuid")],
        
        # Errors result
        [("africa", "err-uuid", 1, 0.1, "analysis-uuid", "region-uuid"),
         ("africa", "err-uuid", 2, 0.2, "analysis-uuid", "region-uuid")],
        
        # Stats result
        [("africa", "stat-uuid", 0.3, 0.1, 0.9, "region-uuid")]
    ]

    mock_db.execute_and_fetch_one.return_value = (datetime(2024, 1, 1),)

    predictions, stats, errors, start_date = service.get_analysis_values("analysis-uuid")

    # Assert all expected results are present with the correct structure
    assert "africa" in predictions
    assert predictions["africa"] == [1.2, 0.5]
    assert errors["africa"] == [0.1, 0.2]
    assert stats["africa"]["rmse"] == 0.3
    assert stats["africa"]["mean_bias"] == 0.1
    assert stats["africa"]["pearson_corr"] == 0.9
    assert start_date == datetime(2024, 1, 1)

@patch("src.api.services.analysis_history_service.db")
def test_get_user_analyses(mock_db, service):

    # Simulate database execution for fetching all user analyses (using 1 analysis as an example)
    mock_db.execute_and_fetch_all.return_value = [
        ("analysis-uuid", "Test", datetime(2024, 1, 1), datetime(2024, 1, 1), "user-uuid")
    ]

    result = service.get_user_analyses("user-uuid")

    # Assert analyses are returned and DB call is made
    assert len(result) == 1
    mock_db.execute_and_fetch_all.assert_called_once()

@patch("src.api.services.analysis_history_service.db")
def test_get_user_analyses_empty(mock_db, service):
    mock_db.execute_and_fetch_all.return_value = []

    result = service.get_user_analyses("user-uuid")

    assert result == []

@patch("src.api.services.analysis_history_service.db")
def test_delete_analysis(mock_db, service):
    analysis_ids = ["analysis-uuid-1", "analysis-uuid-2"]
    service.delete_analysis(analysis_ids)

    expected_tuple = tuple(analysis_ids)

    # Assert all expected database calls were made
    mock_db.execute_and_commit.assert_any_call(
        "DELETE FROM predictions WHERE analysis_id IN %s", expected_tuple
    )
    mock_db.execute_and_commit.assert_any_call(
        "DELETE FROM analysis_errors WHERE analysis_id IN %s", expected_tuple
    )
    mock_db.execute_and_commit.assert_any_call(
        "DELETE FROM analysis_stats WHERE analysis_id IN %s", expected_tuple
    )
    mock_db.execute_and_commit.assert_any_call(
        "DELETE FROM analysis_uploads WHERE analysis_id IN %s", expected_tuple
    )
    mock_db.execute_and_commit.assert_any_call(
        "DELETE FROM analysis_history WHERE id IN %s", expected_tuple
    )
    assert mock_db.execute_and_commit.call_count == 5

@patch("src.api.services.analysis_history_service.db")
def test_delete_all_analyses(mock_db, service):
    user_id = "user-uuid"
    mock_db.execute_and_fetch_all.return_value = [
        ("analysis-uuid-1",),
        ("analysis-uuid-2",)
    ]

    service.delete_all_analyses(user_id)

    expected_tuple = ("analysis-uuid-1", "analysis-uuid-2")

    # Assert all expected database calls were made
    mock_db.execute_and_fetch_all.assert_called_once_with(
        "SELECT id FROM analysis_history WHERE user_id = %s", user_id
    )
    mock_db.execute_and_commit.assert_any_call(
        "DELETE FROM predictions WHERE analysis_id IN %s", expected_tuple
    )
    mock_db.execute_and_commit.assert_any_call(
        "DELETE FROM analysis_errors WHERE analysis_id IN %s", expected_tuple
    )
    mock_db.execute_and_commit.assert_any_call(
        "DELETE FROM analysis_stats WHERE analysis_id IN %s", expected_tuple
    )
    mock_db.execute_and_commit.assert_any_call(
        "DELETE FROM analysis_uploads WHERE analysis_id IN %s", expected_tuple
    )
    mock_db.execute_and_commit.assert_any_call(
        "DELETE FROM analysis_history WHERE id IN %s", expected_tuple
    )
    assert mock_db.execute_and_commit.call_count == 5