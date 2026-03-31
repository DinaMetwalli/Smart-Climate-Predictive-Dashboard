import pandas as pd
import xarray as xr
import numpy as np
import io

from src.utils.errors import InvalidFileTypeError, FileProcessingError, IncompatibleDataError, FileTypeMismatchError

class CustomDatasetRetriever:
    def __init__(self):
        print("→ insitialized Custom Data Retriever ←")
    
    def load_dataset_from_file(self, files:list, filenames: list) -> dict:
        """
        Calls all needed validation checks for single or multi-file uploads.
        Multi-file uploads are concatenated into a single DF to be returned.
        
        :return: combined_df as the combined dataframe.
        :rtype: pd.DataFrame
        """
        file_type = self.validate_file_type(filenames)

        all_dfs = dict()

        for file in files:
            ds = self.validate_columns(file, file_type)
            self.validate_data_types(ds)
            validated_ds, region = self.validate_regions(ds)

            all_dfs[region] = validated_ds


        print(all_dfs)
        
        return all_dfs
    
    def validate_file_type(self, filenames: list) -> str:
        """
        Validates file type formats to be supported files only.
        
        :return: the type of the files uploaded.
        :rtype: str
        
        :raises InvalidFileTypeError: if the uploaded file isn't supported.
        :raises FileTypeMismatchError: if multiple files are uploaded with different types.
        """
        file_types = []

        for filename in filenames:
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
        """
        Validates file structure to ensure columns match with the model's required inputs.
        
        :param file: the file to be processed.
        :param file_type: the type of the file to be processed.
        :return: the data of the file.
        :rtype: DataFrame

        :raises FileProcessingError: for any exceptions that occur when opening the file.
        :raises IncompatibleDataError: if the file doesn't have the expected columns.
        """
        try:
            if file_type == "csv":
                data = pd.read_csv(file)
            else: # netcdf upload
                if hasattr(file, "read"):  # Flask upload
                    ds = xr.open_dataset(io.BytesIO(file.read()))
                else:  # File path
                    ds = xr.open_dataset(file)

                data = ds.to_dataframe().reset_index(drop=True)

        except Exception:
            raise FileProcessingError(f"An error was encountered when opening the file {file}.")

        cols = ['Date', 'Anomaly', 'Region', 'Temperature']
        
        if set(data.columns.values) != set(cols):
            raise IncompatibleDataError(
                f"The provided dataset structure in {file} is incompatible. Please ensure the fields (Date, Anomaly, Region, Temperature) are present in that order."
                )
            
        return data
    
    def validate_data_types(self, ds: pd.DataFrame) -> None:
        """
        Validates the data types of the file's fields to match those expected by the model.
        
        :param ds: the data of the file to be processed.

        :raises IncompatibleDataError: if there is an incorrect data type found (depending on the column).
        """
        # Check all input data is of the expected type
        if not np.issubdtype(ds['Date'].dtype, np.integer):
            raise IncompatibleDataError("Provided column 'Date' contains non-numeric values. Expected format: YYYYMM")
        
        if not np.issubdtype(ds['Anomaly'].dtype, np.number):
            raise IncompatibleDataError("Provided column 'Anomaly' contains non-numeric values.")
        
        if not pd.api.types.is_string_dtype(ds['Region']):
            raise IncompatibleDataError("Provided column 'Region' contains non-text values. Allowed values: Africa, Asia," \
            " Europe, Northamerica, Southamerica, Oceania.")
            
        if not np.issubdtype(ds['Temperature'].dtype, np.number):
            raise IncompatibleDataError("Provided column 'Temperature' contains non-numeric values.")
    
    def validate_regions(self, ds) -> tuple[pd.DataFrame, str]:
        """
        Validates the regions in the data to match those expected by the model.
        
        :param ds: the data of the file to be processed.
        :return: the validated dataset with the regions in lowercase to be as the model expects.
        :rtype: DataFrame

        :raises IncompatibleDataError: if the regions in the file are unsupported or if multiple regions are found in the same file.
        """
        valid_regions = ["africa", "asia", "europe", "northAmerica", "southAmerica", "oceania"]
        ds_region = ds['Region'].unique()
        
        if not set(ds_region).issubset(valid_regions):
            raise IncompatibleDataError("One or more of the given continents/regions are not recognised. Allowed values: Africa, Asia," \
            " Europe, Northamerica, Southamerica, Oceania.")
        
        if len(ds_region) > 1:
            raise IncompatibleDataError("Only one region is allowed per file. If you would like to analyse multiple continents/regions please upload multiple files.")
        
        ds['Region'] = ds['Region'].map(lambda x: x.lower())

        return ds, ds_region[0]