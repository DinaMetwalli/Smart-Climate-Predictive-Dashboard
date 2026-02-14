import pandas as pd

from data.preparation.custom_data_retriever import CustomDatasetRetriever
from data.preparation.data_loader import DataLoader
from src.forecasting_model import ClimateForecastingModel

class AnalysisService():
    def __init__(self, model: ClimateForecastingModel):
        print("Initialising Analysis Service...")
        self.model = model
        self.loader = DataLoader()
        self.custom_loader = CustomDatasetRetriever()
    
    def run_custom_analysis(self, custom_files: list, filenames: list) -> pd.DataFrame:
        data, regions = self.custom_loader.load_dataset_from_file(custom_files,
                                                                  filenames)
        
        processed_ds = self.loader.load_data(regions, data)
        
        predictions = self.model.predict_future(dataset=processed_ds,
                                                months_to_test=60,
                                                test_future=False)

        return predictions