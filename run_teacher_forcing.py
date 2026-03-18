from data.preparation.temp_data_loader import Data_Loader
from src.models_testing.teacher_forcing.teacher_forcing_model import MultiContinentForecastingModel

def main():
    # Multi-region training
    loader = Data_Loader(True, "csv", "global_df.csv")
    data = loader.load_data()
    
    # Initialize model
    model = MultiContinentForecastingModel(
        seq_len=60,
        forecast_num=36
    )

    model.set_dataset(data)
    
    print("TRAINING MODEL")
    model.train_model()
    
    # Save the model
    # model.save_model("my_lstm.pth")

    print("BACKTESTING")
    model.predict_future(
        dataset=data,
        months_to_test=36,
        test_future=False
    )

if __name__ == "__main__":
    main()