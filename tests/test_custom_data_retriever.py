import pytest
import os
import pandas as pd
from pathlib import Path
from data.preparation.custom_data_retriever import CustomDatasetRetriever
from src.utils.errors import FileTypeMismatchError

BASE_DIR = Path.cwd().parent
FILE_PATH = BASE_DIR / "Smart-Climate-Predictive-Dashboard" / "data" / "sources" / "mock"

INVALID_FILES = [
    ("Incorrect_File_Type.txt", "InvalidFileTypeError"),
    ("Missing_Columns.csv", "IncompatibleDataError"),
    ("Incorrect_Anomaly_Type.csv", "IncompatibleDataError"),
    ("Incorrect_Region_Type.csv", "IncompatibleDataError"),
    ("Incorrect_Date_Type.csv", "IncompatibleDataError"),
    ("Unsupported_Regions.csv", "IncompatibleDataError"),
    ("Too_Many_Regions.csv", "IncompatibleDataError")
]
CORRECT_CSV_FILE = "Correct_CSV_File.csv"
CORRECT_NC_FILE = "Correct_NC_File.nc"


def test_upload_csv_file():
    file = os.path.join(FILE_PATH, CORRECT_CSV_FILE)
    retriever = CustomDatasetRetriever(files=[file], filenames=[CORRECT_CSV_FILE])

    dataset, regions_list = retriever.load_dataset_from_file()
    
    assert dataset is not None
    assert regions_list is not None

    assert type(dataset) == pd.DataFrame
    assert type(regions_list) == list

    assert "Date" in dataset.columns
    assert "Anomaly" in dataset.columns
    assert "Region" in dataset.columns

def test_upload_nc_file():
    file = os.path.join(FILE_PATH, CORRECT_NC_FILE)
    retriever = CustomDatasetRetriever(files=[file], filenames=[CORRECT_NC_FILE])

    dataset, regions_list = retriever.load_dataset_from_file()
    
    assert dataset is not None
    assert regions_list is not None

    assert type(dataset) == pd.DataFrame
    assert type(regions_list) == list

    assert "Date" in dataset.columns
    assert "Anomaly" in dataset.columns
    assert "Region" in dataset.columns

def test_cant_upload_different_file_types():
    csv_file = os.path.join(FILE_PATH, CORRECT_CSV_FILE)
    nc_file = os.path.join(FILE_PATH, CORRECT_NC_FILE)
    retriever = CustomDatasetRetriever(files=[csv_file, nc_file], filenames=[CORRECT_CSV_FILE, CORRECT_NC_FILE])

    with pytest.raises(FileTypeMismatchError):
        retriever.load_dataset_from_file()

@pytest.mark.parametrize("filename, expected_exception", INVALID_FILES)
def test_invalid_uploads(filename, expected_exception):
    file_path = os.path.join(FILE_PATH, filename)
    retriever = CustomDatasetRetriever(files=[file_path], filenames=[filename])

    exception_class = getattr(__import__("src.utils.errors", fromlist=[expected_exception]), expected_exception)

    with pytest.raises(exception_class):
        retriever.load_dataset_from_file()