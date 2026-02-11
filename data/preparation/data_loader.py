import pandas as pd
import numpy as np
import requests

class DataLoader():
    def __init__(self, regions:list):
        self.regions_list = regions
        
        print("→ insitialized DataLoader ←")

    def load_data(self, file = None) -> None:
        """
        Dynamically loads the dataset depending on its type (file upload or API call)
        """
        if not file:
            return self.__process_regional_api_data()
        else:
            return self.__process_file_data(file)

        
    def __process_file_data(self, df) -> pd.DataFrame:
        """
        Processes a dataset opened from the file type.

        Args:
            df (pd.DataFrame): the dataset's dataframe.

        Returns:
            pd.DataFrame: the processed dataset.
        """
        
        df = df.replace(np.nan, None)

        df.columns = ['Date', 'Anomaly']
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
                temp_df.columns = ['Date', 'Anomaly']
                temp_df['Anomaly'] = temp_df['Anomaly'].astype(float)
                
                temp_df['Region'] = region
                temp_df = temp_df.set_index('Date')
                
                all_dfs.append(temp_df)
                
            except Exception as e:
                print(f"Failed to fetch data for {region}: {e}")

        # Combine all regions into one list
        if all_dfs:
            global_df = pd.concat(all_dfs)
            print(f"→ Global Data Loaded. Total rows: {len(global_df)} ←")
            return global_df
        else:
            raise Exception("→ No data was found for any of the regions provided.")
            