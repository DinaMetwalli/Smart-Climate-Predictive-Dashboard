from data.preparation.temp_data_loader import Data_Loader
from src.models_testing.original_model.forecasting_model import ClimateForecastingModel

def main():
    
    global_loader = Data_Loader(file_added=True, file_type="csv", file_name="Africa_Data.csv")
    global_data = global_loader.load_data()
    model = ClimateForecastingModel(seq_len=60, forecast_num=36)

    model.set_dataset(global_data)

    print("TRAINING MODEL")
    model.train_model()

    model.save_model("test_lstm.pth")

    testing_loader = Data_Loader(file_added=True, file_type="csv", file_name="Asia_Data.csv")
    asia_data = testing_loader.load_data()
    
    model.predict_future(dataset=asia_data, months_to_test=36, test_future=False)

if __name__ == "__main__":
    main()