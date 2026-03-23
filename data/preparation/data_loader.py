import pandas as pd
import numpy as np
import requests

class DataLoader():
    def __init__(self):
        print("→ insitialized DataLoader ←")

    def load_data(self, regions_list: list, file_data: pd.DataFrame = None) -> dict | pd.DataFrame:
        """
        Dynamically loads the dataset depending on its type (file upload or API call)
        """
        if file_data is None:
            return self.__process_regional_api_data(regions_list)
        else:
            return self.__process_file_data(file_data)

        
    def __process_file_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processes a dataset opened from the file type.

        :param df: the dataset's dataframe.

        :return: the processed dataset.
        :rtype: pd.DataFrame
        """
        
        df = df.replace(np.nan, None)

        df.columns = ['Date', 'Anomaly', 'Region', 'Temperature']
        df['Anomaly'] = df['Anomaly'].astype(float)
        df = df.set_index('Date')

        print(df.head())

        return df
    
    def __process_regional_api_data(self, regions_list: list) -> pd.DataFrame:
        """
        Fetches and combines data from multiple regions into a single DataFrame.

        :return: the processed, combined dataset from the API call.
        :rtype: pd.DataFrame
        """
        
        all_dfs = dict()
        
        print("→ Fetching Global Data... ←")
        
        for region in regions_list:
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
                
                # all_dfs.append(temp_df)
                all_dfs[region] = temp_df
                
            except Exception as e:
                print(f"Failed to fetch data for {region}: {e}")

        # Combine all regions into one list
        return all_dfs