import pandas as pd
import xarray as xr
import numpy as np

from src.utils.errors import InvalidFileTypeError, FileProcessingError, IncompatibleDataError, FileTypeMismatchError

class CustomDatasetRetriever:
    def __init__(self, files:list, filenames:list):
        self.files = files
        self.filenames = filenames
    
    def load_dataset_from_file(self) -> pd.DataFrame:
        file_type = self.validate_file_type()

        all_dfs = []

        for file in self.files:
            ds = self.validate_columns(file, file_type)
            self.validate_data_types(ds)
            validated_ds = self.validate_regions(ds)

            all_dfs.append(validated_ds)

        combined_df = pd.concat(all_dfs)
        
        return combined_df
    
    def validate_file_type(self) -> str:
        file_types = []

        for filename in self.filenames:
            if filename.endswith(".csv"):
                file_types.append("csv")
            elif filename.endswith(".nc"):
                file_types.append("nc")
            else:
                raise InvalidFileTypeError(f"Ivalid file type for file {filename} provided. Files must have CSV or NC extensions.")
            
        if len(set(file_types)) != 1:
            raise FileTypeMismatchError("Multi-file uploads cannot have conflicting file types. All uploaded file formats must be the same.")
        
        return file_types[0]

    def validate_columns(self, file, file_type) -> pd.DataFrame:
        try:
            if file_type == "csv":
                data = pd.read_csv(file)
            else:
                ds = xr.open_dataset(file)
                data = ds.to_dataframe().reset_index()

        except Exception:
            raise FileProcessingError(f"An error was encountered when opening the file {file}.")

        cols = ['Anomaly', 'Date', 'Region']
        
        if set(data.columns.values) != set(cols):
            raise IncompatibleDataError(
                f"The provided dataset structure in {file} is incompatible. Please ensure the fields (Date, Anomaly, Region) are present in that order."
                )
            
        return data
    
    def validate_data_types(self, data) -> None:
        # Check all input data is of the expected type
        if not np.issubdtype(data['Date'].dtype, np.integer):
            raise IncompatibleDataError("Provided column 'Date' contains non-numeric values. Expected format: YYYYMM")
        
        if not np.issubdtype(data['Anomaly'].dtype, np.number):
            raise IncompatibleDataError("Provided column 'Anomaly' contains non-numeric values.")
        
        if not pd.api.types.is_string_dtype(data['Region']):
            raise IncompatibleDataError("Provided column 'Region' contains non-text values. Allowed values: Africa, Asia," \
            " Europe, Northamerica, Southamerica, Oceania.")
    
    def validate_regions(self, ds) -> pd.DataFrame:
        valid_regions = ["africa", "asia", "europe", "northAmerica", "southAmerica", "oceania"]
        ds_regions = ds['Region'].unique()
        
        if not set(ds_regions).issubset(valid_regions):
            raise IncompatibleDataError("One or more of the given continents/regions are not recognised. Allowed values: Africa, Asia," \
            " Europe, Northamerica, Southamerica, Oceania.")
        
        if len(ds_regions) > 1:
            raise IncompatibleDataError("Only one region is allowed per file. If you would like to analyse multiple continents/regions please upload multiple files.")
        
        ds['Region'] = ds['Region'].map(lambda x: x.lower())

        return ds