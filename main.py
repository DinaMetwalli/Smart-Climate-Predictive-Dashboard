import matplotlib.pyplot as plt
import pickle
from data.preparation.data_loader import DataLoader
from src.forecasting_model import ClimateForecastingModel

def main():

    # Single region training
    loader = DataLoader(True, "csv", "Africa_Data.csv")
    data = loader.load_data()

    # Multi-region training
    regions=['africa', 'asia', 'europe', 
             'northAmerica', 'southAmerica', 'oceania']
    loader = DataLoader(False, regions=regions)
    data = loader.load_data()
    
    # Initialise model
    model = ClimateForecastingModel(data=data, regions=regions, seq_len=60, forecast_num=60, model_file='regional_climate_lstm.pth', scaler_file='scaler.pkl')
    
    # Complete future forecast using a testing dataframe
    testing_loader = DataLoader(True, "csv", "Africa_Data.csv")
    testing_data = testing_loader.load_data()
    
    model.predict_future(dataset=testing_data, months_to_test=60, test_future=False)
    # model.save_model()

if __name__ == "__main__":
    main()