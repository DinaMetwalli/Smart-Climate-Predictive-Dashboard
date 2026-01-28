import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.utils.data as data
import matplotlib.pyplot as plt
import pickle
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import OneHotEncoder
from pathlib import Path
import os

class ClimateForecastingModel():
    def __init__(self, data: pd.DataFrame, regions: list, seq_len:int = 36, forecast_num:int = 12, model_file: str = None, scaler_file: str = None):
        self.dataset = data
        self.regions = regions
        self.seq_len = seq_len
        self.forecast_num = forecast_num # Amount of months to predict for the future at each step
        self.num_features = 3 + len(regions)
        self.output_dim = forecast_num
        self.scaler = MinMaxScaler(feature_range=(-1, 1))
        self.model = LSTMModel(input_dim=self.num_features,
                               hidden_dim=128,
                               layer_dim=1,
                               output_dim=self.output_dim)
        
        print("→ Initialising Climate Forecasting Model... ←")

        if model_file:
                print("→ Loading saved model... ←")
                BASE_DIR = Path.cwd().parent
                path = BASE_DIR / "Smart-Climate-Predictive-Dashboard"
                model_path = os.path.join(path, model_file)
                scaler_path = os.path.join(path, scaler_file)

                print(model_path)
                print(scaler_path)

                if os.path.exists(model_path):
                    self.model.load_state_dict(torch.load(model_path))
                    self.model.eval()

                    with open(scaler_path, "rb") as f:
                        self.scaler = pickle.load(f)

                    print(f"→ Successfully loaded trained model and scaler from regional_climate_lstm.pth and scaler.pkl")

                else:
                    raise Exception("! Failed: Could not load model from path . . . !")
        else:
            print("→ No saved model found, initiating model training... ←")
            self.__train_model()

    def save_model(self, path:str = "regional_climate_lstm.pth") -> None:
        """
        Saves the trained model as a pth file.
        
        Args:
            path (str): name of the file to be saved.
        """
        torch.save(self.model.state_dict(), path)
        print(f"→ Model saved to '{path};.")

        with open("scaler.pkl", "wb") as f:
            pickle.dump(self.scaler, f)

        print(f"→ Scaler saved to 'scaler.pkl'.")
    
    def __encode_cyclical_data(self, dataset) -> None:
        """
        Adds Sine/Cosine seasonality and a time trend for contextualisation of different time periods
        This is done to help the model pick up on the upward-trend of anomaly increase and diff seasons
        reference: https://www.kaggle.com/code/avanwyk/encoding-cyclical-features-for-deep-learning)

        Args:
            df (pd.DataFrame): the dataframe returned from the data loader.
        """
        df = dataset.copy()

        df['Month_Idx'] = np.arange(len(df)) % 12
        df['Month_Sin'] = np.sin(2 * np.pi * df['Month_Idx'] / 12)
        df['Month_Cos'] = np.cos(2 * np.pi * df['Month_Idx'] / 12)

        # Use One-Hot Encoding to add the region as a feature
        df_encoded = pd.get_dummies(df, columns=['Region'])

        feature_cols = ['Anomaly', 'Month_Sin', 'Month_Cos']
        for region in self.regions:
            feature = "Region_" + region
            feature_cols.append(feature)
            if feature in df_encoded.columns:
                continue
            else:
                df_encoded[feature] = False

        print(df_encoded[feature_cols].head())
        
        return df_encoded[feature_cols].values.astype(np.float32)

    def __create_sequences(self, data):
        """Creates sequences from the given dataframe."""
        X, y = [], []

        for i in range(len(data) - self.seq_len - self.forecast_num + 1):
            X.append(data[i : i + self.seq_len])
            y.append(data[i + self.seq_len : i + self.seq_len + self.forecast_num, 0])
        return torch.tensor(np.array(X)), torch.tensor(np.array(y))
    
    def __train_model(self):
        TRAIN_SPLIT = 0.8
        encoded_data = self.__encode_cyclical_data(self.dataset)
        encoded_data[:, 0:1] = self.scaler.fit_transform(encoded_data[:, 0:1])

        split_idx = int(len(encoded_data) * TRAIN_SPLIT)
        train_data = encoded_data[:split_idx]
        test_data = encoded_data[split_idx - self.seq_len:]
        
        X_train, y_train = self.__create_sequences(train_data)
        X_test, y_test = self.__create_sequences(test_data)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        loader = data.DataLoader(data.TensorDataset(X_train, y_train), shuffle=True, batch_size=128)
        criterion = nn.MSELoss()
        
        num_epochs = 300

        # Define parameters for early stopping
        best_state = None
        best_test_rmse = float('inf')
        patience = 5
        patience_counter = 0

        print("→ Training...")
        for epoch in range(num_epochs):
            self.model.train()
            for X_batch, y_batch in loader:
                y_pred = self.model(X_batch)
                loss = criterion(y_pred, y_batch)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            
            if epoch % 20 == 0:
                self.model.eval()
                with torch.no_grad():
                    # Reference for train vs test RMSE:
                    # https://discuss.pytorch.org/t/rmse-loss-function/16540
                    train_pred = self.model(X_train)
                    train_rmse = torch.sqrt(criterion(train_pred, y_train)).item()
                    
                    test_pred = self.model(X_test)
                    test_rmse = torch.sqrt(criterion(test_pred, y_test)).item()
                
                print(f"Epoch {epoch}: Train RMSE {train_rmse:.4f}, Test RMSE {test_rmse:.4f}")

                # Trigger early stopping if test RMSE starts to increase again
                if test_rmse < best_test_rmse:
                    best_test_rmse = test_rmse
                    patience_counter = 0
                    best_state = self.model.state_dict().copy()
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    print(f"→ Early stopping triggered at epoch {epoch}. Best Test RMSE: {best_test_rmse:.4f}")
                    self.model.load_state_dict(best_state)
                    break

        self.__plot_training_results(X_train, X_test, split_idx)

    def __plot_training_results(self, X_train, X_test, split_idx):
        self.model.eval()
        with torch.no_grad():
            # Extract only the first month from each predictions output for plotting later
            train_preds = self.model(X_train)[:, 0].numpy().reshape(-1, 1)
            test_preds = self.model(X_test)[:, 0].numpy().reshape(-1, 1)
        
        # Convert back to actual anomalies for plotting
        train_preds = self.scaler.inverse_transform(train_preds)
        test_preds = self.scaler.inverse_transform(test_preds)
        actuals = self.dataset['Anomaly'].values

        # Plot the training results
        plt.figure(figsize=(14, 5))
        plt.plot(actuals, label="Actual Anomaly", color="black", alpha=0.3)
        plt.plot(range(self.seq_len, split_idx - self.forecast_num + 1), train_preds, label="Train Fit", color="blue")
        plt.plot(range(split_idx, split_idx + len(test_preds)), test_preds, label="Test Prediction", color="green")
        plt.legend()
        plt.show()

    def predict_future(self, dataset:pd.DataFrame, months_to_test:int = 48, test_future:bool = True):
        """
        Performs a prediction either through backtesting to evaluate the model or a blind future forecast.

        Args:
            months_to_test (int): the amount of months hidden from the model from current time to complete backtesting on.
            test_future (bool): if set to True, the model will do a blind forecast instead of backtesting/evaluation.

        References:
            https://stackoverflow.com/questions/69785891/how-to-use-the-lstm-model-for-multi-step-forecasting
            https://machinelearningmastery.com/how-to-develop-lstm-models-for-multi-step-time-series-forecasting-of-household-power-consumption/
        """
        
        # Encode and transform the given prediction dataset
        encoded_data = self.__encode_cyclical_data(dataset)
        encoded_data[:, 0:1] = self.scaler.transform(encoded_data[:, 0:1])

        total_len = len(encoded_data)
        if test_future == False:
            # Start at the index in the dataset before the number of months to test
            predict_start_idx = total_len - months_to_test

            # The number of months to predict will be set to the same number of months to perform backtesting on
            steps_to_predict = months_to_test
        else:
            # Otherwise, predict into the future (starting from the very end of the given dataset)
            predict_start_idx = total_len

        # Check if there is enough history/data in the provided dataset to predict
        if predict_start_idx - self.seq_len < 0:
            raise ValueError("Not enough history to start prediction at this index.")
        
        current_window = encoded_data[predict_start_idx - self.seq_len : predict_start_idx]
        input_tensor = torch.tensor(current_window).unsqueeze(0)

        preds = []
        
        # Perform the prediction
        self.model.eval()
        with torch.no_grad():
            prediction_vector = self.model(input_tensor)
            preds_np = prediction_vector.squeeze(0).numpy()
            
            for pred in preds_np.flatten():
                preds.append(float(pred))

        preds = preds[:steps_to_predict]
        
        # Convert back to actual temperature anomalies and plot
        blind_preds_rescaled = self.scaler.inverse_transform(np.array(preds).reshape(-1, 1))
        self.__plot_prediction(dataset, blind_preds_rescaled, predict_start_idx, test_future)

    def __plot_prediction(self, actual_df, forecast_values, split_idx, test_future):
        actuals = actual_df['Anomaly'].values
        
        plt.figure(figsize=(14, 6))
        
        # Plot the history/previous anomalies
        history_range = range(split_idx - 120, split_idx + 1)
        plt.plot(history_range, actuals[history_range[0]:history_range[-1]+1], 
                 color="gray", alpha=0.6, label="Previous Anomalies (History)")

        # Plot the actual anomalies (if performing backtesting)
        if not test_future:
            if split_idx < len(actuals):
                truth_range = range(split_idx, len(actuals))
                plt.plot(truth_range, actuals[split_idx:], color="gray",
                         linestyle="--", alpha=0.6, label="Hidden Truth (Actuals)")

        # Plot the model's forecast outputs
        forecast_range = range(split_idx, split_idx + len(forecast_values))
        
        plt.plot(forecast_range, forecast_values, 
                 color="red", linewidth=2, label="Model Forecast")

        if test_future:
            plt.title("Model Temperature Anomaly Predictions (Blind Forecast)")
        else:
            plt.axvline(x=split_idx, color='blue', linestyle=':', label="Forecast Start")
            plt.title("Model Temperature Anomaly Predictions vs Hidden Truth (Back Testing)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()

class LSTMModel(nn.Module):
    """Class for defining the LSTM Module from PyTorch"""
    
    def __init__(self, input_dim, hidden_dim, layer_dim, output_dim):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True, num_layers=layer_dim)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1])