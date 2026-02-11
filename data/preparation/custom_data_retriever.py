import pandas as pd
import xarray as xr
import numpy as np

from src.utils.errors import InvalidFileTypeError, FileProcessingError, IncompatibleDataError

class CustomDatasetRetriever:
    def __init__(self, file, filename):
        self.file = file
        self.filename = filename
    
    def load_dataset_from_file(self) -> None:
        
        file_type = self.validate_file_type()
        ds = self.validate_columns(file_type)
        self.validate_data_types(ds)
        
        validated_ds = self.validate_regions(ds)

        self.dataset = validated_ds

        return validated_ds
    
    def validate_file_type(self) -> str:
        if self.filename.endswith(".csv"):
            return "csv"
        elif self.filename.endswith(".nc"):
            return "nc"
        else:
            raise InvalidFileTypeError("Ivalid file type provided. Files must have CSV or NC extensions.")

    def validate_columns(self, file_type):
        try:    
            if file_type == "csv":
                data = pd.read_csv(self.file)
            else:
                ds = xr.open_dataset(self.file)
                data = ds.to_dataframe().reset_index()

        except Exception:
            raise FileProcessingError("An error was encountered when opening the file.")

        cols = ['Anomaly', 'Date', 'Region']
        
        if set(data.columns.values) != set(cols):
            raise IncompatibleDataError(
                "The provided dataset structure is incompatible. Please ensure the fields (Date, Anomaly, Region) are present in that order."
                )
        
        return data
    
    def validate_data_types(self, data):
        # Check all input data is of the expected type
        if not np.issubdtype(data['Date'].dtype, np.integer):
            raise IncompatibleDataError("Provided column 'Date' contains non-numeric values. Expected format: YYYYMM")
        
        if not np.issubdtype(data['Anomaly'].dtype, np.number):
            raise IncompatibleDataError("Provided column 'Anomaly' contains non-numeric values.")
        
        if not pd.api.types.is_string_dtype(data['Region']):
            raise IncompatibleDataError("Provided column 'Region' contains non-text values. Allowed values: Africa, Asia," \
            " Europe, Northamerica, Southamerica, Oceania.")
    
    def validate_regions(self, ds):
        valid_regions = ["africa", "asia", "europe", "northAmerica", "southAmerica", "oceania"]
        ds_regions = ds['Region'].unique()
        
        if list(ds_regions) not in valid_regions:
            raise IncompatibleDataError("One or more of the given continents/regions are not recognised. Allowed values: Africa, Asia," \
            " Europe, Northamerica, Southamerica, Oceania.")
        
        validated_ds = ds['Region'].map(lambda x: x.lower())

        return validated_ds