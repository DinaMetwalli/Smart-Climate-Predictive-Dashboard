# old data loader for model testing.

import pandas as pd
import numpy as np
import requests
import os
import xarray as xr
from pathlib import Path

class Data_Loader():
    def __init__(self, file_added: bool = True, file_type: str = None, file_name: str = None, regions:list = None):
        self.file_added = file_added
        self.file_type = file_type # To handle both NC and CSV/XLSX formats
        self.file_name = file_name
        self.regions_list = regions
        
        print("→ insitialized DataLoader ←")

    def load_data(self) -> None:
        """
        Dynamically loads the dataset depending on its type (File or API call)
        """
        if self.file_added:
            BASE_DIR = Path.cwd().parent
            file_path = BASE_DIR / "Smart-Climate-Predictive-Dashboard" / "data" / "sources" / "Datasets" / "NOAAGLOBALTEMP"
            file = os.path.join(file_path, self.file_name)
            print(file)

            if os.path.exists(file):
                if self.file_type == "nc":
                    print("→ NC file type ←")
                    df = xr.open_dataset(file)
                    # To be done later...

                elif self.file_type == "csv":
                    print("→ CSV/XLSX file type ←")
                    data = pd.read_csv(file)
                    
                    # Replace empty fields in csv with None
                    data = data.replace(np.nan, None)
                    return self.__process_file_data(data)
            else:
                raise Exception(f"'{self.file_name}' file was not found.")
        else:
            return self.__process_regional_api_data()

        
    def __process_file_data(self, df) -> pd.DataFrame:
        """
        Processes a dataset opened from the file type.

        Args:
            df (pd.DataFrame): the dataset's dataframe.

        Returns:
            pd.DataFrame: the processed dataset.
        """
        # Only works with CSV for now, will be modified later to support NC as well.
        df.columns = ['Date', 'Anomaly', 'Region', 'Temperature']
        df['Anomaly'] = df['Anomaly'].astype(float)
        df = df.set_index('Date')

        print(df.head())

        return df
    
    def __process_regional_api_data(self) -> pd.DataFrame:
        """
        Fetches and combines data from multiple regions into a single DataFrame.

        Returns:
            pd.DataFrame: the processed, combined dataset from the API call.
        """
        
        all_dfs = []
        
        print("→ Fetching Global Data... ←")
        
        for region in self.regions_list:
            print(f"→ Fetching {region.title()}'s data...")

            coverage = 'land'
            if region == 'arctic' or region == 'antarctic':
                coverage = 'land_ocean'
            
            # Dynamic HTTP GET request for each region
            url = f"https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/{region}/tavg/{coverage}/1/0.json"
            
            try:
                response = requests.get(url)
                data = response.json()
                
                # Extract fetched results to DataFrame
                temp_df = pd.DataFrame.from_dict(data['data'], orient='index').reset_index()
                temp_df.columns = ['Year', 'Anomaly']
                temp_df['Anomaly'] = temp_df['Anomaly'].astype(float)
                
                temp_df['Region'] = region
                temp_df = temp_df.set_index('Year')
                
                all_dfs.append(temp_df)
                
            except Exception as e:
                print(f"Failed to fetch data for {region}: {e}")

        # Combine all regions into one list
        if all_dfs:
            global_df = pd.concat(all_dfs)
            print(f"→ Global Data Loaded. Total rows: {len(global_df)} ←")
            global_df.to_csv("global_df.csv")
            return global_df
        else:
            raise Exception("→ No data was found for any of the regions provided.")
            