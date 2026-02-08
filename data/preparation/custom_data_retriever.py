import pandas as pd
from src.utils.errors import InvalidFileTypeError, FileProcessingError, IncompatibleDataError

class CustomDatasetRetriever:
    def __init__(self):
        self.dataset = None
    
    def load_dataset_from_file(self, file) -> None:
        file_type = self.validate_file_type(file)

        if file_type == "csv":
            data = self.parse_csv(file)
        else:
            data = self.parse_nc(file)

        self.dataset = data

    def get_dataset(self):
        return self.dataset
    
    def validate_file_type(self, file_path) -> str:
        if file_path.endswith(".csv"):
            return "csv"
        elif file_path.endswith(".nc"):
            return "nc"
        else:
            raise InvalidFileTypeError("Ivalid file type provided. Files must have CSV or NC extensions.")

    def parse_csv(self, file):
        try:
            data = pd.read_csv(file)
            expected_cols = ['Date', 'Anomaly', 'Region']

            if list(data.columns.values) != expected_cols:
                raise IncompatibleDataError(
                    "The provided dataset structure is incompatible. Please ensure the columns (Date, Anomaly, Region) are present."
                    )
        
        except Exception:
            raise FileProcessingError("An error was encountered when opening the file.")
        
        return data

    def parse_nc(self, file):
        pass