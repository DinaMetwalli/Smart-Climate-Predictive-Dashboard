import pandas as pd
import numpy as np
import requests
from datetime import datetime
from owid.catalog import fetch

from src.utils.errors import APIConnectionError

class DataLoader():
    def __init__(self):
        print("→ insitialized DataLoader ←")

    def load_data(self, file_data: pd.DataFrame = None) -> dict | tuple[datetime, pd.DataFrame]:
        """
        Dynamically loads the dataset depending on its type (file upload or API call)
        """
        if file_data is None:
            return self.__process_regional_api_data()
        else:
            return self.__process_file_data(file_data)

        
    def __process_file_data(self, df: pd.DataFrame) -> tuple[str, pd.DataFrame]:
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

        start_date = df.index[-1]
        date = datetime.strptime(str(start_date), "%Y%m")

        return df, date
    
    def __process_regional_api_data(self) -> dict:
        """
        Fetches and combines data from multiple regions into a single DataFrame.

        :return: the processed, combined dataset from the API call.
        :rtype: pd.DataFrame
        """
        
        all_dfs = dict()
        region_mapping = {
            'africa': 'Africa (NIAID)',
            'asia': 'Asia (NIAID)',
            'europe': 'Europe (NIAID)',
            'northAmerica': 'North America (NIAID)',
            'southAmerica': 'South America (NIAID)',
            'oceania': 'Oceania (NIAID)'
        }
        
        print("- Fetching Global Data -")
        
        # Get temperature anomaly values
        for noaa_name, owid_name in region_mapping.items():
            print(f"→ Fetching {noaa_name.title()}'s data...")

            coverage = 'land'
            if noaa_name == 'arctic' or noaa_name == 'antarctic':
                coverage = 'land_ocean'
            
            # Dynamic HTTP GET request for each region
            url = f"https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/{noaa_name}/tavg/{coverage}/1/0.json"
            
            try:
                response = requests.get(url)
                data = response.json()
                
                # Extract fetched results to DataFrame
                anomaly_df = pd.DataFrame.from_dict(data['data'], orient='index').reset_index()
                anomaly_df.columns = ['Date', 'Anomaly']
                anomaly_df['Anomaly'] = anomaly_df['Anomaly'].astype(float)
                anomaly_df['Region'] = noaa_name
                anomaly_df = anomaly_df.set_index('Date')

                # Save only rows after 1940 to match OWID's data
                anomaly_df.index = anomaly_df.index.astype(int)
                anomaly_df = anomaly_df[anomaly_df.index >= 194001]

                # Get absolute temperature values
                temp_df = fetch("average-monthly-surface-temperature")
                temp_continent = temp_df.xs(owid_name, level=0)
                
                num_rows = len(anomaly_df)
                matched_values = temp_continent['temperature_2m'].iloc[:num_rows].values
                
                # Assign the values back to the main dataframe
                anomaly_df['Temperature'] = matched_values
                
                print(f"Successfully matched {num_rows} months for {noaa_name}")
                
                # all_dfs.append(temp_df)
                all_dfs[noaa_name] = anomaly_df
                
            except Exception as e:
                print(f"Failed to fetch data for {noaa_name}: {e}")
                raise APIConnectionError("There was an issue fetching data for live analysis... Please try again later.")
                
        # Combine all regions into one list
        return all_dfs