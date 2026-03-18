from data.preparation.temp_data_loader import Data_Loader
from src.models_testing.original_correct_splitting.modified_original_model import ClimateForecastingModel


def main():
    # Multi-region training
    loader = Data_Loader(True, "csv", "global_df.csv")
    data = loader.load_data()

    model = ClimateForecastingModel(
        seq_len=60,
        forecast_num=36
    )
    
    model.set_dataset(data)

    print("TRAINING MODEL")
    model.train_model()
    
    # Save the model
    # model.save_model("my_lstm.pth")

    print("BACKTESTING")
    model.predict_future(dataset=data, region='asia', months_to_test=36, test_future=False)
    model.predict_future(dataset=data, region='asia', months_to_test=36, test_future=True) # predict again but with test_future = true

if __name__ == "__main__":
    main()