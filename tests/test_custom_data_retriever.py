import pytest
import os
from pathlib import Path
from data.preparation.custom_data_retriever import CustomDatasetRetriever

BASE_DIR = Path.cwd().parent
FILE_PATH = BASE_DIR / "Smart-Climate-Predictive-Dashboard" / "data" / "sources" / "mock"

INVALID_FILES = [
    ("Incorrect_File_Type.txt", "InvalidFileTypeError"),
    ("Missing_Columns.csv", "IncompatibleDataError"),
    ("Incorrect_Anomaly_Type.csv", "IncompatibleDataError"),
    ("Incorrect_Region_Type.csv", "IncompatibleDataError"),
    ("Incorrect_Date_Type.csv", "IncompatibleDataError"),
    ("Unsupported_Regions.csv", "IncompatibleDataError"),
]
CORRECT_CSV_FILE = "Correct_CSV_File.csv"
CORRECT_NC_FILE = "Correct_NC_File.nc"


def test_upload_csv_file():
    file = os.path.join(FILE_PATH, CORRECT_CSV_FILE)
    retriever = CustomDatasetRetriever(file=file, filename=CORRECT_CSV_FILE)

    dataset = retriever.load_dataset_from_file()
    
    assert dataset is not None

    assert "Date" in dataset.columns
    assert "Anomaly" in dataset.columns
    assert "Region" in dataset.columns

def test_upload_nc_file():
    file = os.path.join(FILE_PATH, CORRECT_NC_FILE)
    retriever = CustomDatasetRetriever(file=file, filename=CORRECT_NC_FILE)

    dataset = retriever.load_dataset_from_file()
    
    assert dataset is not None

    assert "Date" in dataset.columns
    assert "Anomaly" in dataset.columns
    assert "Region" in dataset.columns

@pytest.mark.parametrize("filename, expected_exception", INVALID_FILES)
def test_invalid_uploads(filename, expected_exception):
    file_path = os.path.join(FILE_PATH, filename)
    retriever = CustomDatasetRetriever(file=file_path, filename=filename)

    exception_class = getattr(__import__("src.utils.errors", fromlist=[expected_exception]), expected_exception)

    with pytest.raises(exception_class):
        retriever.load_dataset_from_file()