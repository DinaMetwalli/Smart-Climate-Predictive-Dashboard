from data.preparation.custom_data_retriever import CustomDatasetRetriever
from data.preparation.data_loader import DataLoader
from src.forecasting_model import ClimateForecastingModel

from datetime import datetime
from dateutil.relativedelta import relativedelta

class AnalysisService():
    def __init__(self, model: ClimateForecastingModel, loader: DataLoader, custom_loader: CustomDatasetRetriever):
        print("Initialising Analysis Service...")
        self.model = model
        self.loader = loader
        self.custom_loader = custom_loader
    
    def run_custom_analysis(self, custom_files: list, filenames: list) -> dict:
        datasets = self.custom_loader.load_dataset_from_file(custom_files,
                                                                  filenames)
        
        combined_preds = {}
        combined_stats = {}
        combined_errors = {}
        
        for region, data in datasets.items():
            processed_ds, start_date = self.loader.load_data(data)
        
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

        return combined_preds, combined_stats, combined_errors, start_date
    
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
    
    def get_analysis_results(self, month_index: int, predictions: dict, start_date: datetime) -> dict:
        if start_date:
            date = start_date + relativedelta(months=month_index)
            date = date.strftime('%Y-%m')
        else:
            current_time = datetime.today()
            date = current_time + relativedelta(months=month_index)
            date = date.strftime('%Y-%m')

        continent_map = {
            "North America": "northAmerica",
            "South America": "southAmerica",
            "Europe": "europe",
            "Africa": "africa",
            "Asia": "asia",
            "Oceania": "oceania"
        }

        continents = {}

        for display_name, key in continent_map.items():
            if predictions:
                preds_list = predictions.get(key)
                if preds_list and len(preds_list) > month_index:
                    continents[display_name] = preds_list[month_index]
                else:
                    continents[display_name] = None
            else:
                continents[display_name] = None

        response = {
            "month_index": month_index,
            "date": date,
            "continents": continents
        }

        return response