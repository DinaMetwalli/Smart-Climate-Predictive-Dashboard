from data.preparation.temp_data_loader import Data_Loader
from src.models_testing.multi_step_stateful.multistep_stateful import MultistepLSTM

def main():
    seq_len = 60
    horizon = 36
    
    loader = Data_Loader(True, "csv", "global_df.csv")
    data = loader.load_data()

    model = MultistepLSTM(seq_len, horizon)
    model.set_dataset(data)

    print("TRAINING MODEL")
    model.train_model()

    test_loader = Data_Loader(True, "csv", "global_df.csv")
    test_dataframe = test_loader.load_data()

    print("BACKTESTING")
    model.backtest(
            months_to_backtest=horizon,
            dataset=test_dataframe
        )

if __name__ == "__main__":
    main()