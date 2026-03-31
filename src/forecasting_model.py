import pandas as pd
import numpy as np
import torch
import pickle
import os

import torch.nn as nn
import torch.utils.data as data
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from sktime.forecasting.model_selection import SlidingWindowSplitter

from src.utils.errors import NotEnoughDataError

class ClimateForecastingModel():
    def __init__(self, seq_len: int = 120, forecast_num: int = 60, model_file: str = None, scaler_file: str = None):
        self.dataset = None
        self.regions = ['africa', 'asia', 'europe', 'northAmerica', 'southAmerica', 'oceania']
        self.seq_len = seq_len
        self.forecast_num = forecast_num # Amount of months to predict for the future at each step
        self.num_features = 3 + len(self.regions)
        self.output_dim = forecast_num
        
        # Assign a separate scaler for each continent
        self.anomaly_scalers = {region: MinMaxScaler(feature_range=(-1, 1)) for region in self.regions}
        self.temp_scalers = {region: MinMaxScaler(feature_range=(-1, 1)) for region in self.regions}
        self.year_scaler = MinMaxScaler(feature_range=(-1, 1))
        
        self.model = LSTMModel(
            input_dim=self.num_features,
            hidden_dim=128,
            layer_dim=1,
            output_dim=self.output_dim
        )

        print("→ Initialising Climate Forecasting Model...")

        # Load the saved model and scalers if they are passed
        if model_file:
            print("→ Loading saved model...")
            if os.path.exists(model_file) and os.path.exists(scaler_file):
                self.model.load_state_dict(torch.load(model_file))
                self.model.eval()
                with open(scaler_file, "rb") as f:
                    loaded_scalers = pickle.load(f)
                    self.anomaly_scalers = loaded_scalers['anomaly']
                    self.temp_scalers = loaded_scalers['temp']
                    self.year_scaler = loaded_scalers['year']
                print("Successfully loaded trained model and scalers.")
            else:
                raise Exception("→ Error: could not load model or scalers from path!")

    def set_dataset(self, data: pd.DataFrame) -> None:
        """Sets the training dataset"""
        self.dataset = data

    def save_model(self, path: str = "my_regional_lstm.pth") -> None:
        """Saves the model file and scalers"""

        torch.save(self.model.state_dict(), path)
        print(f"→ Model saved to '{path}'.")
        with open("my_scalers.pkl", "wb") as f:
            pickle.dump({'anomaly': self.anomaly_scalers, 'temp': self.temp_scalers, 'year': self.year_scaler}, f)
            
        print("→ Scalers saved to 'scalers.pkl'.")

    def __encode_cyclical_data(self, dataset: pd.DataFrame) -> np.ndarray:
        """
        Add the year and month for contextualisation of different time periods
        This is done to help the model pick up on the upward-trend of anomaly increase and diff seasons

        Args:
            dataset (pd.DataFrame): the dataframe returned from the data loader.
        """
        df = dataset.copy()
        df['Date'] = df.index

        df_encoded = pd.get_dummies(df, columns=['Region'])

        feature_cols = ['Anomaly', 'Temperature', 'Date']
        for region in self.regions:
            feature = f'Region_{region}'
            feature_cols.append(feature)
            if feature not in df_encoded.columns:
                df_encoded[feature] = False
        
        return df_encoded[feature_cols].values.astype(np.float32)

    def __create_sequences(self, data_array, is_backtest=False):
        """Creates sequences from the given dataframe."""
        
        step = self.forecast_num if is_backtest else 1
        
        splitter = SlidingWindowSplitter(
            window_length=self.seq_len,
            fh=np.arange(1, self.forecast_num + 1),
            step_length=step
        )

        X, y = [], []
        for train_idx, test_idx in splitter.split(data_array):
            X.append(data_array[train_idx])
            y.append(data_array[test_idx, 0])

        if len(X) == 0:
            return torch.empty(0), torch.empty(0)

        return torch.tensor(np.array(X)), torch.tensor(np.array(y))
    
    def train_model(self):
        """Trains the LSTM model with regional splitting to avoid data contamination"""

        X_train_list, y_train_list = [], []
        X_test_list, y_test_list = [], []

        for region in self.regions:
            # Get each region's data
            region_df = self.dataset[self.dataset['Region'] == region]
            split_idx = int(len(region_df) * 0.8)
            
            train_part = region_df.iloc[:split_idx]
            test_part = region_df.iloc[split_idx:]

            # Encode and scale separately
            t_encoded = self.__encode_cyclical_data(train_part)
            v_encoded = self.__encode_cyclical_data(test_part)
            
            t_encoded[:, 0:1] = self.anomaly_scalers[region].fit_transform(t_encoded[:, 0:1])
            v_encoded[:, 0:1] = self.anomaly_scalers[region].transform(v_encoded[:, 0:1])
            
            t_encoded[:, 1:2] = self.temp_scalers[region].fit_transform(t_encoded[:, 1:2])
            v_encoded[:, 1:2] = self.temp_scalers[region].transform(v_encoded[:, 1:2])
            
            t_encoded[:, 2:3] = self.year_scaler.fit_transform(t_encoded[:, 2:3])
            v_encoded[:, 2:3] = self.year_scaler.transform(v_encoded[:, 2:3])
            
            X_tr, y_tr = self.__create_sequences(t_encoded)
            X_te, y_te = self.__create_sequences(v_encoded)

            X_train_list.append(X_tr)
            y_train_list.append(y_tr)
            X_test_list.append(X_te)
            y_test_list.append(y_te)

        # Combine all regions
        X_train = torch.cat(X_train_list)
        y_train = torch.cat(y_train_list)
        X_test = torch.cat(X_test_list)
        y_test = torch.cat(y_test_list)

        print(f"Train sequences: {len(X_train)} | Test sequences: {len(X_test)}")

        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.005)
        loader = data.DataLoader(data.TensorDataset(X_train, y_train), shuffle=True, batch_size=128)
        
        criterion = nn.MSELoss()

        num_epochs = 300
        best_state = None
        best_test_rmse = float('inf')
        patience = 5
        patience_counter = 0
        train_rmse_values, val_rmse_values = [], []

        print("→ Training...")
        for epoch in range(num_epochs):
            self.model.train()
            for X_batch, y_batch in loader:
                y_pred = self.model(X_batch)
                loss = criterion(y_pred, y_batch)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            
            if epoch % 10 == 0:
                self.model.eval()
                with torch.no_grad():
                    train_rmse = torch.sqrt(nn.MSELoss()(self.model(X_train), y_train)).item()
                    test_rmse = torch.sqrt(nn.MSELoss()(self.model(X_test), y_test)).item()
                    train_rmse_values.append(train_rmse)
                    val_rmse_values.append(test_rmse)

                print(f"- Epoch {epoch} → Train RMSE {train_rmse:.4f} | Test RMSE {test_rmse:.4f} -")

                if test_rmse < best_test_rmse:
                    best_test_rmse   = test_rmse
                    patience_counter = 0
                    best_state = self.model.state_dict().copy()
                else:
                    patience_counter += 1

                if patience_counter >= patience:
                    print(f"→ Early stopping at epoch {epoch}. Best Test RMSE: {best_test_rmse:.4f}")
                    self.model.load_state_dict(best_state)
                    break

        # self.__plot_training_results(train_df, test_df)
        self.__plot_model_loss(train_rmse_values, val_rmse_values)

        with torch.no_grad():
            train_pred_full = self.model(X_train)
            test_pred_full  = self.model(X_test)

        self.__print_summary_stats(y_train, train_pred_full, "Training")
        self.__print_summary_stats(y_test,  test_pred_full, "Validation")

    def __plot_training_results(self, train_df: pd.DataFrame, test_df: pd.DataFrame):
        """Plots the training vs test/validation fits against the actuals"""
        
        self.model.eval()
        fig, axes = plt.subplots(len(self.regions), 1, figsize=(15, 16), sharex=False)

        for i, region in enumerate(self.regions):
            r_train_enc = self.__encode_cyclical_data(train_df[train_df['Region'] == region])
            r_train_enc[:, 0:1] = self.anomaly_scalers[region].transform(r_train_enc[:, 0:1])
            r_train_enc[:, 1:2] = self.year_scaler.transform(r_train_enc[:, 1:2])

            r_test_enc = self.__encode_cyclical_data(test_df[test_df['Region'] == region])
            r_test_enc[:, 0:1] = self.anomaly_scalers[region].transform(r_test_enc[:, 0:1])
            r_test_enc[:, 1:2] = self.year_scaler.transform(r_test_enc[:, 1:2])

            X_r_train, _ = self.__create_sequences(r_train_enc)
            X_r_test, _ = self.__create_sequences(r_test_enc)

            with torch.no_grad():
                train_preds = self.model(X_r_train)[:, 0].numpy().reshape(-1, 1)
                test_preds  = self.model(X_r_test)[:, 0].numpy().reshape(-1, 1)

            region_df = self.dataset[self.dataset['Region'] == region]
            actuals = region_df['Anomaly'].values
            train_size = len(train_df[train_df['Region'] == region])

            train_preds = self.anomaly_scalers[region].inverse_transform(train_preds).flatten()
            test_preds = self.anomaly_scalers[region].inverse_transform(test_preds).flatten()

            ax = axes[i]
            ax.plot(actuals, label="Actual", color="black", alpha=0.3, linewidth=1)
            ax.plot(
                range(self.seq_len, self.seq_len + len(train_preds)),
                train_preds,
                label="Train Fit", color="blue", linewidth=1
            )
            ax.plot(
                range(train_size + self.seq_len, train_size + self.seq_len + len(test_preds)),
                test_preds,
                label="Test Prediction", color="green", linewidth=1
            )
            ax.axvline(train_size, linestyle="--", color="gray", alpha=0.6)
            ax.set_title(region.title())
            ax.set_ylabel("Anomaly (°C)")
            ax.legend(loc="upper left", fontsize=7)
            ax.grid(True, alpha=0.2)

        axes[-1].set_xlabel("Time (Months)")
        fig.suptitle("Training Results - All Continents", fontsize=13, y=1.001)
        plt.tight_layout()
        plt.show()

    def __plot_model_loss(self, train_rmse_values, val_rmse_values) -> None:
        """Plots the model's validation loss vs. training loss over epochs."""
        
        epochs = np.arange(len(train_rmse_values))

        plt.figure(figsize=(10, 6))
        plt.plot(epochs, train_rmse_values, label="Train Loss", color="blue")
        plt.plot(epochs, val_rmse_values, label="Validation Loss", color="orange")
        plt.xlabel("Epoch")
        plt.ylabel("RMSE Loss")
        plt.title("Training and Validation Loss")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()

    def predict_future(self, region_df: pd.DataFrame, region: str, months_to_test: int = 48, test_future: bool = True):
        """Handles both backtesting and future prediction requests."""

        encoded = self.__encode_cyclical_data(region_df)
        encoded[:, 0:1] = self.anomaly_scalers[region].transform(encoded[:, 0:1])
        encoded[:, 1:2] = self.temp_scalers[region].transform(encoded[:, 1:2])
        encoded[:, 2:3] = self.year_scaler.transform(encoded[:, 2:3])

        total_len = len(encoded)

        if not test_future:
            predict_start_idx = total_len - months_to_test
            steps_to_predict  = months_to_test
        else:
            predict_start_idx = total_len
            steps_to_predict  = months_to_test

        if predict_start_idx - self.seq_len < 0:
            raise NotEnoughDataError(
                f"Not enough history in uploaded dataset(s). Need at least {self.seq_len + months_to_test} rows, got {total_len}."
            )

        window = encoded[predict_start_idx - self.seq_len : predict_start_idx]
        input_tensor = torch.tensor(window).unsqueeze(0)

        self.model.eval()
        with torch.no_grad():
            preds_np = self.model(input_tensor).squeeze(0).numpy()

        preds_np = preds_np[:steps_to_predict]
        preds_rescaled = self.anomaly_scalers[region].inverse_transform(preds_np.reshape(-1, 1))

        # Region's actual values for plotting
        region_df_actuals = region_df[region_df['Region'] == region].copy()

        if not test_future:
            actuals = region_df_actuals['Anomaly'].values[predict_start_idx : predict_start_idx + steps_to_predict]
            # self.__print_summary_stats(actuals, preds_rescaled.flatten(), f"Backtest ({region})")
            stats = self.get_summary_stats(actuals, preds_rescaled.flatten())
            errors = self.get_horizon_errors(actuals, preds_rescaled.flatten())
            return stats, errors
        
        # self.__plot_prediction(region_df_actuals, preds_rescaled, predict_start_idx, test_future, region)
        return preds_rescaled.flatten().tolist()

    def __plot_prediction(self, region_df, forecast_values, split_idx, test_future, region):
        """Plots the backtest or future prediction results."""
        
        actuals = region_df['Anomaly'].values

        plt.figure(figsize=(14, 6))

        history_start = max(0, split_idx - 120)
        history_range = range(history_start, split_idx)
        
        plt.plot(
            history_range,
            actuals[history_range[0] : history_range[-1] + 1],
            color="gray", alpha=0.6, label="Previous Anomalies (History)"
        )

        # Plot the hidden truth if backtesting.
        if not test_future and split_idx < len(actuals):
            truth_range = range(split_idx, len(actuals))
            plt.plot(
                truth_range, actuals[split_idx:],
                color="gray", linestyle="--", alpha=0.6, label="Hidden Truth (Actuals)"
            )

        forecast_range = range(split_idx, split_idx + len(forecast_values))
        plt.plot(forecast_range, forecast_values, color="red", linewidth=2, label="Model Forecast")

        if test_future:
            plt.title(f"{region.title()} - Blind Forecast")
        else:
            plt.axvline(x=split_idx, color='blue', linestyle=':', label="Forecast Start")
            plt.title(f"{region.title()} - Backtesting: Forecast vs Actual")

        plt.xlabel("Date")
        plt.ylabel("Temperature Anomaly (°C)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def get_horizon_errors(self, actuals: torch.tensor, preds: torch.tensor) -> list:
        """
        Calculates the error at each step of the forecast.
        """
        if torch.is_tensor(actuals): actuals = actuals.numpy()
        if torch.is_tensor(preds): preds = preds.numpy()
        
        actuals = actuals.flatten()
        preds = preds.flatten()
        
        horizon_errors = []
        
        # Calculate the error at each month in the backtest
        for h in range(len(actuals)):
            step_error = abs(preds[h] - actuals[h])
            horizon_errors.append(float(step_error))
        
        return horizon_errors

    def get_summary_stats(self, y_true: torch.tensor, y_pred: torch.tensor) -> dict:
        """Returns the predictions RMSE, bias, and correlation for the dataset passed"""
        if torch.is_tensor(y_true): y_true = y_true.numpy()
        if torch.is_tensor(y_pred): y_pred = y_pred.numpy()

        y_true = y_true.flatten()
        y_pred = y_pred.flatten()

        stats = {}

        errors = y_true - y_pred
        rmse = np.sqrt(np.mean(errors**2))
        mean_bias = np.mean(errors)
        
        pearson_corr = np.corrcoef(y_true, y_pred)[0, 1]

        stats['rmse'] = float(rmse)
        stats['mean_bias'] = float(mean_bias)
        stats['pearson_corr'] = float(pearson_corr)

        return stats
    
    def __print_summary_stats(self, y_true, y_pred, dataset_name) -> None:
        """Print the predictions errors, bias, and correlation for the dataset passed"""
        if torch.is_tensor(y_true): y_true = y_true.numpy()
        if torch.is_tensor(y_pred): y_pred = y_pred.numpy()

        y_true = y_true.flatten()
        y_pred = y_pred.flatten()

        errors = y_true - y_pred
        mae = np.mean(np.abs(errors))
        rmse = np.sqrt(np.mean(errors**2))
        mean_bias = np.mean(errors)
        correlation = np.corrcoef(y_true, y_pred)[0, 1]

        print(f"\n{'='*50}")
        print(f"{dataset_name.upper()} SET PERFORMANCE")
        print(f"{'='*50}")
        print(f" RMSE:        {rmse:.4f}")
        print(f" MAE:         {mae:.4f}")
        print(f" Mean Bias:   {mean_bias:.4f}")
        print(f" Correlation: {correlation:.4f}")
        print(f" Samples:     {len(y_true)}")

class LSTMModel(nn.Module):
    """The LSTM Model class inhereting from Pytorch's nn.Module class."""
    
    def __init__(self, input_dim, hidden_dim, layer_dim, output_dim):
        super(LSTMModel, self).__init__()
        dropout = 0.2 if layer_dim > 1 else 0.0
        self.lstm = nn.LSTM(
            input_dim, 
            hidden_dim, 
            batch_first=True, 
            num_layers=layer_dim, 
            dropout=dropout
        )
        
        # Use a linear activation function for the last layer to consider negative temp. anomaly values.
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1])