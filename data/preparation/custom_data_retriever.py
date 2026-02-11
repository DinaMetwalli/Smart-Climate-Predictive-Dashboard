import pandas as pd
import xarray as xr
from src.utils.errors import InvalidFileTypeError, FileProcessingError, IncompatibleDataError

class CustomDatasetRetriever:
    def __init__(self):
        self.dataset = None
    
    def load_dataset_from_file(self, file) -> None:
        
        file_type = self.validate_file_type(file)
        ds = self.validate_file_data(file, file_type)
        
        validated_ds = self.validate_regions(ds)

        self.dataset = validated_ds

        return validated_ds

    def get_dataset(self):
        return self.dataset
    
    def validate_file_type(self, file_name) -> str:
        if file_name.endswith(".csv"):
            return "csv"
        elif file_name.endswith(".nc"):
            return "nc"
        else:
            raise InvalidFileTypeError("Ivalid file type provided. Files must have CSV or NC extensions.")

    def validate_file_data(self, file, file_type):
        try:
            cols = ['Anomaly', 'Date', 'Region']
            
            if file_type == "csv":
                data = pd.read_csv(file)
            else:
                ds = xr.open_dataset(file)
                data = ds.to_dataframe().reset_index()

            if set(data.columns.values) != set(cols):
                raise IncompatibleDataError(
                    "The provided dataset structure is incompatible. Please ensure the fields (Date, Anomaly, Region) are present in that order."
                    )
            
            # Check all input data is of the expected type
            if not data['Date'].map(lambda x: isinstance(x, int)).all():
                raise IncompatibleDataError("Provided column 'Date' contains non-numeric values. Expected format: YYYYMM")
            
            if not data['Anomaly'].map(lambda x: isinstance(x, (int, float))).all():
                raise IncompatibleDataError("Provided column 'Anomaly' contains non-numeric values.")
            
            if not data['Region'].map(lambda x: isinstance(x, str)).all():
                raise IncompatibleDataError("Provided column 'Region' contains non-text values. Allowed values: Africa, Asia," \
                " Europe, Northamerica, Southamerica, Oceania.")
        
        except Exception:
            raise FileProcessingError("An error was encountered when opening the file.")
        
        return data
    
    def validate_regions(self, ds):
        valid_regions = ["africa", "asia", "europe", "northAmerica", "southAmerica", "oceania"]
        ds_regions = ds['Region'].unique()
        
        if ds_regions not in valid_regions:
            raise IncompatibleDataError("One or more of the given continents/regions are not recognised. Allowed values: Africa, Asia," \
            " Europe, Northamerica, Southamerica, Oceania.")
        
        validated_ds = ds['Region'].map(lambda x: x.lower())

        return validated_ds