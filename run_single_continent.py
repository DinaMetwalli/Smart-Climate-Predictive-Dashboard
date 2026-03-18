from data.preparation.temp_data_loader import Data_Loader
from src.models_testing.single_continent.single_continent_input_model import ClimateForecastingModel
def main():
    # Single region training
    loader = Data_Loader(True, "csv", "Asia_Data.csv")
    df = loader.load_data()

    model = ClimateForecastingModel(
        data=df,
        seq_length=60,
        forecast_steps=36
    )
    
    model.backtest(months_to_backtest=36)

if __name__ == "__main__":
    main()