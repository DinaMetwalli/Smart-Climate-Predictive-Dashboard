"""
A simple model that trains on a single continent input, and produces a single continent output.

Note: does not use months encoding. Takes in and outputs only the temperature anomaly value.
"""

import torch
import torch.nn as nn
import torch.utils.data as data
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import os

class ClimateForecastingModel():
    def __init__(self, data: pd.DataFrame, seq_length:int = 60, forecast_steps:int = 12, model_path:str = None):
        self.dataset = data
        self.seq_length = seq_length
        self.forecast_steps = forecast_steps  # How many steps ahead to predict
        self.num_features = 1 # Only one input feature, being the anomaly value.

        self.scaler = MinMaxScaler(feature_range=(-1, 1))
        
        # Get rid of the regions column as it is unused in this model.
        self.dataset = self.dataset.drop(columns=['Region'])

        # Scale the data
        self.scaled_values = self.scaler.fit_transform(self.dataset.values)
        
        # Model predicts forecast_steps into the future
        self.model = LSTMModel(
            input_dim=self.num_features, 
            hidden_dim=128,
            layer_dim=1,
            output_dim=self.forecast_steps,  # Predict multiple steps at once
            dropout=0
        )
        
        print("==> Initialising Climate Forecasting Model... <==")
        print(f"Sequence length: {seq_length}")
        print(f"Forecast horizon: {forecast_steps}")

        if model_path and os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path))
            self.model.eval()
            print(f"==> Successfully loaded trained model from {model_path} <==")
        else:
            self.__train_model()

    def __create_sequences(self, data):
        """
        X: [t-seq_length : t] -> input sequence
        y: [t+1 : t+1+forecast_steps] -> target future values
        """
        X, y = [], []
        
        for i in range(len(data) - self.seq_length - self.forecast_steps + 1):
            X.append(data[i : i + self.seq_length])
            y.append(data[i + self.seq_length : i + self.seq_length + self.forecast_steps])
            
        return torch.tensor(np.array(X), dtype=torch.float32), torch.tensor(np.array(y), dtype=torch.float32)
    
    def __train_model(self):
        
        TRAIN_SPLIT = 0.8
        split_idx = int(len(self.scaled_values) * TRAIN_SPLIT)
        train_data = self.scaled_values[:split_idx]
        test_data = self.scaled_values[split_idx - self.seq_length:]

        X_train, y_train = self.__create_sequences(train_data)
        X_test, y_test = self.__create_sequences(test_data)
        
        print(f"Training data: X={X_train.shape}, y={y_train.shape}")
        print(f"Test data: X={X_test.shape}, y={y_test.shape}")

        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.0005, weight_decay=1e-4)
        loader = data.DataLoader(data.TensorDataset(X_train, y_train), shuffle=False, batch_size=64)
        
        patience = 20
        best_test_rmse = float('inf')
        best_epoch = 0
        patience_counter = 0
        best_model_state = None

        train_rmse_values = []
        val_rmse_values = []

        num_epochs = 450
        print("-> Training...")
        for epoch in range(num_epochs):
            self.model.train()
            for X_batch, y_batch in loader:
                y_pred = self.model(X_batch)
                loss = criterion(y_pred, y_batch.squeeze(-1))
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            # if epoch % 5 == 0:
            self.model.eval()
            with torch.no_grad():
                train_pred = self.model(X_train)
                train_rmse = torch.sqrt(criterion(train_pred, y_train.squeeze(-1))).item()
                
                test_pred = self.model(X_test)
                test_rmse = torch.sqrt(criterion(test_pred, y_test.squeeze(-1))).item()

                train_rmse_values.append(train_rmse)
                val_rmse_values.append(test_rmse)

            print(f"Epoch {epoch}: Train RMSE {train_rmse:.4f}, Val RMSE {test_rmse:.4f}")

            if test_rmse < best_test_rmse:
                best_test_rmse = test_rmse
                patience_counter = 0
                best_epoch = epoch
                best_model_state = self.model.state_dict().copy()
            else:
                patience_counter += 1
                
            if patience_counter >= patience:
                print(f"Early stopping at epoch {best_epoch}. Best Val RMSE: {best_test_rmse:.4f}")
                self.model.load_state_dict(best_model_state)
                break
        
        print("\n" + "="*60)
        print("TRAINING COMPLETE - DETAILED PERFORMANCE METRICS")
        print("="*60)
        
        # Final evaluation with best model
        self.model.eval()
        with torch.no_grad():
            final_train_pred = self.model(X_train)
            final_test_pred = self.model(X_test)

        # Plot training results
        self.__plot_training_results(X_train, X_test)
        self.__plot_model_loss(train_rmse_values, val_rmse_values)
        
        # Print stats for both training and validation sets
        self.__print_summary_stats(y_train, final_train_pred, dataset_name="Train")
        self.__print_summary_stats(y_test, final_test_pred, dataset_name="Validation")

    def __plot_training_results(self, X_train, X_test):
        """
        Plot predictions vs actuals for training and test sets.
        """
        self.model.eval()
        with torch.no_grad():
            # Get predictions - shape: (num_sequences, forecast_steps)
            train_preds = self.model(X_train).numpy()
            test_preds = self.model(X_test).numpy()
            print(f"\ntrain_preds shape -> {train_preds.shape}")
            print(f"test_preds shape -> {test_preds.shape}")
        
        # For plotting, use only the first prediction from each sequence (1-step ahead)
        train_preds_first = train_preds[:, 0]
        test_preds_first = test_preds[:, 0]

        print(f"\ntrain_preds_first shape -> {train_preds_first.shape}")
        print(f"test_preds_first shape -> {test_preds_first.shape}")
        
        # Create arrays for plotting
        train_plot = np.ones(len(self.scaled_values)) * np.nan
        test_plot = np.ones(len(self.scaled_values)) * np.nan
        
        # CALCULATE SPLIT_IDX (same as in train_model)
        TRAIN_SPLIT = 0.8
        split_idx = int(len(self.scaled_values) * TRAIN_SPLIT)
        
        # Fill in train predictions (start at seq_length)
        train_plot[self.seq_length : self.seq_length + len(train_preds_first)] = train_preds_first
        
        # Fill in test predictions (start at ACTUAL split point)
        test_plot[split_idx : split_idx + len(test_preds_first)] = test_preds_first
        
        plt.figure(figsize=(14, 6))
        plt.plot(self.scaled_values, label="Actual Data", color='black', alpha=0.3, linewidth=1)
        plt.plot(train_plot, label="Train Predictions (1-step)", color='blue', linestyle='--', alpha=0.7)
        plt.plot(test_plot, label="Test Predictions (1-step)", color='green', linewidth=2)
        plt.axvline(x=split_idx, color='red', linestyle=':', alpha=0.5, label="Train/Test Split")
        plt.legend()
        plt.title("Climate Anomaly Forecasting: Train vs Test")
        plt.xlabel("Time Step")
        plt.ylabel("Scaled Anomaly")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def __plot_model_loss(self, train_rmse_values, val_rmse_values):
        """Plot training and validation loss over epochs."""

        plt.figure(figsize=(10, 6))
        
        epochs = np.arange(len(train_rmse_values))
        
        plt.plot(epochs, train_rmse_values, label="Train Loss", color="blue")
        plt.plot(epochs, val_rmse_values, label="Validation Loss", color="orange")
        
        plt.xlabel("Epoch")
        plt.ylabel("RMSE Loss")
        plt.title("Training and Validation Loss")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()

    def __print_summary_stats(self, y_true, y_pred, dataset_name: str):
        """
        Print performance statistics.
        
        Args:
            y_true: Ground truth
            y_pred: Predictions
            dataset_name: Name for the dataset
        """
        # Ensure numpy arrays
        if torch.is_tensor(y_true):
            y_test_np = y_true.numpy()
        if torch.is_tensor(y_pred):
            test_preds_np = y_pred.detach().numpy()

        # Inverse transform (flattened)
        y_test_flat = y_test_np.reshape(-1, 1)
        actuals_all = self.scaler.inverse_transform(y_test_flat).flatten()

        test_preds_flat = test_preds_np.reshape(-1, 1)
        preds_all = self.scaler.inverse_transform(test_preds_flat).flatten()
        
        # Calculate overall performance metrics
        errors = actuals_all - preds_all
        mean_bias = np.mean(errors)
        mae = np.mean(np.abs(errors))
        rmse = np.sqrt(np.mean(errors**2))
        correlation = np.corrcoef(actuals_all, preds_all)[0, 1]
        
        print(f"\n{'='*50}")
        print(f"OVERALL {dataset_name.upper()} SET PERFORMANCE")
        print(f"{'='*50}")
        print(f" RMSE:        {rmse:.4f} °C")
        print(f" MAE:         {mae:.4f} °C")
        print(f" Mean Bias:   {mean_bias:.4f} °C")
        print(f" Correlation: {correlation:.4f}")
        print(f" Samples:     {y_true.shape[0]}")

    def backtest(self, months_to_backtest: int):
        """
        One-shot backtest: Use seq_length history to predict forecast_steps months.
        This matches the training setup.
        """
        
        print(f"\nRunning one-shot backtest for {self.forecast_steps} months...")

        total_len = len(self.scaled_values)
        predict_start_idx = total_len - months_to_backtest

        # Validate enough history
        if predict_start_idx - self.seq_length < 0:
            raise ValueError("Not enough history to start prediction.")
        
        # Get input window (last seq_length months before backtest period)
        input_window = self.scaled_values[predict_start_idx - self.seq_length: predict_start_idx]
        input_tensor = torch.tensor(input_window, dtype=torch.float32).unsqueeze(0)

        # Perform prediction
        self.model.eval()
        with torch.no_grad():
            forecast = self.model(input_tensor)
            
            print(f"\nPrediction input tensor -> {input_tensor.shape}")
            print(f"Forecast shape -> {forecast.shape}")

        # Get actual values (SCALED - stats function will inverse transform)
        actual_values_scaled = self.scaled_values[predict_start_idx : predict_start_idx + self.forecast_steps]
        
        # Convert to tensor with batch dimension for stats function
        y_true = torch.tensor(actual_values_scaled, dtype=torch.float32).unsqueeze(0)
        y_pred = forecast
        
        # Make sure values are unscaled for plotting
        predictions_unscaled = self.scaler.inverse_transform(
            forecast.numpy().reshape(-1, 1)
        ).flatten()
        
        actual_values_unscaled = self.scaler.inverse_transform(
            actual_values_scaled.reshape(-1, 1)
        ).flatten()
        
        self.__plot_backtest(predictions_unscaled, actual_values_unscaled, predict_start_idx)
        self.__print_summary_stats(y_true, y_pred, dataset_name="Backtest")

    def __plot_backtest(self, predictions, actuals, start_idx):
        """Plot backtest forecast."""
        plt.figure(figsize=(14, 6))
        
        # Show continuous actual data from history through backtest period
        history_start = max(0, start_idx - self.seq_length)
        full_range = range(history_start, start_idx + len(predictions))
        
        # Actual data (history + backtest period)
        full_actuals = self.dataset.values[history_start:start_idx + len(predictions)].flatten()
        plt.plot(full_range, full_actuals, 
                color="black", alpha=0.3, linewidth=2, label="Actual Data")
        
        # Overlay backtest predictions
        backtest_range = range(start_idx, start_idx + len(predictions))
        plt.plot(backtest_range, predictions, color="blue", linewidth=2.5, 
                label="One-Shot Prediction")
        
        plt.axvline(x=start_idx, color='red', linestyle=':', alpha=0.5, 
                    label="Backtest Start")
        plt.title(f"One-Shot Backtest: {len(predictions)} Months")
        plt.xlabel("Time Step (Months)")
        plt.ylabel("Temperature Anomaly (°C)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def save_model(self, path="single_continent_lstm.pth"):
        """Save the trained model."""
        torch.save(self.model.state_dict(), path)
        print(f"Model saved to '{path}'")

class LSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, layer_dim, output_dim, dropout=0.2):
        super(LSTMModel, self).__init__()
        self.hidden_dim = hidden_dim
        self.layer_dim = layer_dim
        
        self.lstm = nn.LSTM(
            input_dim, 
            hidden_dim, 
            layer_dim, 
            batch_first=True, 
            dropout=dropout if layer_dim > 1 else 0
        )
        
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, output_dim)
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        last_step = lstm_out[:, -1, :]
        
        out = self.dropout(last_step)
        out = self.fc(out)
        
        return out