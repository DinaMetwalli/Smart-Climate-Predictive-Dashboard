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
    
    def run_custom_analysis(self, custom_files: list, filenames: list) -> dict:
        datasets = self.custom_loader.load_dataset_from_file(custom_files,
                                                                  filenames)
        
        combined_preds = {}
        combined_stats = {}
        combined_errors = {}
        
        for region, data in datasets.items():
            processed_ds = self.loader.load_data(data)
        
            predictions = self.model.predict_future(region_df=processed_ds,
                                                    region=region,
                                                    months_to_test=60,
                                                    test_future=True)
            
            stats, errors = self.model.predict_future(region_df=processed_ds,
                                                    region=region,
                                                    months_to_test=60,
                                                    test_future=False)
            
            combined_preds[region] = predictions
            combined_stats[region] = stats
            combined_errors[region] = errors

        return combined_preds, combined_stats, combined_errors
    
    def run_live_analysis(self) -> dict:
        processed_ds = self.loader.load_data()

        combined_preds = {}
        combined_stats = {}
        combined_errors = {}
        
        for region, ds in processed_ds.items():
            predictions = self.model.predict_future(region_df=ds,
                                                    region=region,
                                                    months_to_test=60,
                                                    test_future=True)
            
            stats, errors = self.model.predict_future(region_df=ds,
                                                    region=region,
                                                    months_to_test=60,
                                                    test_future=False)
            
            combined_preds[region] = predictions
            combined_stats[region] = stats
            combined_errors[region] = errors
        
        return combined_preds, combined_stats, combined_errors