"""
A multiple continent input model with teacher forcing applied. Predicts one timestep
into the future for each continent and loops to forecast the desired number of months.
"""

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.utils.data as data
import matplotlib.pyplot as plt
import pickle
from sklearn.preprocessing import MinMaxScaler
from pathlib import Path
import os

class MultiContinentForecastingModel():
    """
    Input shape: (seq_len, num_features) where features = [africa, asia, europe, northAm, southAm, oceania, month_sin, month_cos]
    Output shape: (forecast_num, num_regions) - separate predictions for each continent
    """
    
    def __init__(self, regions=None, seq_len:int = 36, forecast_num:int = 12, model_file: str = None, scaler_file: str = None):
        self.dataset = None
        self.regions = regions if regions else ['africa', 'asia', 'europe', 'northAmerica', 'southAmerica', 'oceania']
        self.num_regions = len(self.regions)
        self.seq_len = seq_len
        self.forecast_num = forecast_num
        
        self.num_features = self.num_regions + 2
        
        # The model outputs 1 step at a time (num_regions) and loops inside the forward pass
        self.output_dim = self.num_regions
        
        # Assign a separate scaler for each continent
        self.scalers = {region: MinMaxScaler(feature_range=(-1, 1)) for region in self.regions}
        
        self.model = MultiOutputLSTM(
            input_dim=self.num_features,
            hidden_dim=64,
            layer_dim=1,
            output_dim=self.output_dim,
            num_regions=self.num_regions,
            dropout=0.4
        )
        
        print("Initialising Multi-Continent Forecasting Model...")
        print(f"Input features: {self.num_features} (6 continents + 2 cyclical)")
        print(f"Output: {self.forecast_num} months × {self.num_regions} continents")

        if model_file and os.path.exists(model_file):
            self.model.load_state_dict(torch.load(model_file))
            self.model.eval()
            with open(scaler_file, "rb") as f:
                self.scalers = pickle.load(f)
            print(f"Successfully loaded trained model and scalers")

    def set_dataset(self, data: pd.DataFrame) -> None:
        self.dataset = data

    def save_model(self, path:str = "multi_continent_lstm.pth") -> None:
        torch.save(self.model.state_dict(), path)
        print(f"Model saved to '{path}'.")

        with open("scalers.pkl", "wb") as f:
            pickle.dump(self.scalers, f)
        print(f"Scalers saved to 'scalers.pkl'.")
    
    def __prepare_wide_format(self, dataset) -> pd.DataFrame:
        """
        Convert long format (stacked continents) to wide format (continents as columns).
        """
        df = dataset.copy()
        wide_df = df.pivot(columns='Region', values='Anomaly')
        
        for region in self.regions:
            if region not in wide_df.columns:
                raise ValueError(f"Missing region '{region}' in dataset!")
        
        wide_df = wide_df[self.regions]
        print("Converted to wide format:")
        print(wide_df.head())
        
        return wide_df
    
    def __encode_features(self, wide_df: pd.DataFrame) -> np.ndarray:
        """
        Add cyclical features and scale data.
        Returns: numpy array of shape (time_steps, num_features)
        """
        df = wide_df.copy()
        
        df['Month_Idx'] = np.arange(len(df)) % 12
        df['Month_Sin'] = np.sin(2 * np.pi * df['Month_Idx'] / 12)
        df['Month_Cos'] = np.cos(2 * np.pi * df['Month_Idx'] / 12)
        
        for i, region in enumerate(self.regions):
            df[region] = self.scalers[region].fit_transform(df[[region]])
        
        feature_cols = self.regions + ['Month_Sin', 'Month_Cos']
        return df[feature_cols].values.astype(np.float32)

    def __create_sequences(self, data):
        """
        Creates sequences for multi-output prediction.
        Returns history (X), actual future targets (y), and future time features (time).
        """
        X, y, future_time = [], [], []

        for i in range(len(data) - self.seq_len - self.forecast_num + 1):
            X.append(data[i : i + self.seq_len])
            y.append(data[i + self.seq_len : i + self.seq_len + self.forecast_num, :self.num_regions])
            
            # Future time features: the future sin/cos to feed into the autoregressive loop
            future_time.append(data[i + self.seq_len : i + self.seq_len + self.forecast_num, self.num_regions:])
        
        print(f"Created {len(X)} sequences")
        return torch.tensor(np.array(X)), torch.tensor(np.array(y)), torch.tensor(np.array(future_time))
    
    def train_model(self):
        TRAIN_SPLIT = 0.8
        
        wide_df = self.__prepare_wide_format(self.dataset)
        encoded_data = self.__encode_features(wide_df)

        split_idx = int(len(encoded_data) * TRAIN_SPLIT)
        train_data = encoded_data[:split_idx]
        test_data = encoded_data[split_idx:]
        
        X_train, y_train, time_train = self.__create_sequences(train_data)
        X_test, y_test, time_test = self.__create_sequences(test_data)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001, weight_decay=1e-5)
        
        loader = data.DataLoader(
            data.TensorDataset(X_train, y_train, time_train),
            shuffle=False,
            batch_size=128
        )
        criterion = nn.MSELoss()
        
        num_epochs = 200
        best_state = None
        best_test_rmse = float('inf')
        patience = 15
        patience_counter = 0

        train_rmse_values = []
        val_rmse_values = []

        print("Training...")
        for epoch in range(num_epochs):
            
            # Linearly decay teacher forcing from 1.0 to 0.0 over 75% of epochs
            tf_ratio = max(0.0, 1.0 - (epoch / (num_epochs * 0.75)))
            
            self.model.train()
            for X_batch, y_batch, time_batch in loader:
                y_pred = self.model(X_batch, future_steps=self.forecast_num, 
                                    future_time_features=time_batch, 
                                    y_true=y_batch, teacher_forcing_ratio=tf_ratio)
                loss = criterion(y_pred, y_batch)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            
            self.model.eval()
            with torch.no_grad():
                
                # Inference during evaluation with teacher_forcing_ratio = 0.0
                train_pred = self.model(X_train, future_steps=self.forecast_num, future_time_features=time_train, teacher_forcing_ratio=0.0)
                train_rmse = torch.sqrt(criterion(train_pred, y_train)).item()
                
                test_pred = self.model(X_test, future_steps=self.forecast_num, future_time_features=time_test, teacher_forcing_ratio=0.0)
                test_rmse = torch.sqrt(criterion(test_pred, y_test)).item()

                train_rmse_values.append(train_rmse)
                val_rmse_values.append(test_rmse)
            
            # if epoch % 5 == 0:
            print(f"Epoch {epoch}: Train RMSE {train_rmse:.4f}, Val RMSE {test_rmse:.4f} | TF Ratio: {tf_ratio:.2f}")

            if test_rmse < best_test_rmse:
                best_test_rmse = test_rmse
                patience_counter = 0
                best_state = self.model.state_dict().copy()
            else:
                patience_counter += 1
            
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch}. Best Val RMSE: {best_test_rmse:.4f}")
                self.model.load_state_dict(best_state)
                break

        self.__plot_training_results(X_train, X_test, time_train, time_test, split_idx, wide_df)
        self.__plot_model_loss(train_rmse_values, val_rmse_values)

        with torch.no_grad():
            train_pred_full = self.model(X_train, future_steps=self.forecast_num, future_time_features=time_train, teacher_forcing_ratio=0.0)
            test_pred_full  = self.model(X_test,  future_steps=self.forecast_num, future_time_features=time_test,  teacher_forcing_ratio=0.0)

        self.__print_summary_stats(y_train.reshape(-1, self.num_regions), train_pred_full.reshape(-1, self.num_regions), "Training")
        self.__print_summary_stats(y_test.reshape(-1, self.num_regions),  test_pred_full.reshape(-1, self.num_regions),  "Validation")

    def __plot_training_results(self, X_train, X_test, time_train, time_test, split_idx, wide_df):
        self.model.eval()
        with torch.no_grad():
            train_pred = self.model(X_train, future_steps=self.forecast_num, future_time_features=time_train)
            test_pred = self.model(X_test, future_steps=self.forecast_num, future_time_features=time_test)

        train_pred = train_pred.numpy()
        test_pred = test_pred.numpy()

        # Only use first forecast step for alignment
        train_pred = train_pred[:, 0, :]
        test_pred = test_pred[:, 0, :]

        actual = wide_df[self.regions].values

        fig, axes = plt.subplots(self.num_regions, 1, figsize=(15, 16), sharex=True)

        for i, region in enumerate(self.regions):
            train_pred_rescaled = self.scalers[region].inverse_transform(
                train_pred[:, i].reshape(-1, 1)
            ).flatten()

            test_pred_rescaled = self.scalers[region].inverse_transform(
                test_pred[:, i].reshape(-1, 1)
            ).flatten()

            ax = axes[i]
            ax.plot(actual[:,i], label="Actual", color="black", alpha=0.3)

            train_range = range(self.seq_len, self.seq_len + len(train_pred_rescaled))
            ax.plot(train_range, train_pred_rescaled, label="Train Prediction", color="blue")

            test_range = range(split_idx + self.seq_len, split_idx + self.seq_len + len(test_pred_rescaled))
            ax.plot(test_range, test_pred_rescaled, label="Test Prediction", color="red")

            ax.axvline(split_idx, linestyle="--", color="gray")

            ax.set_title(region)
            ax.set_ylabel("Temperature anomaly (°C)")
            ax.legend()

        axes[-1].set_xlabel("Time (Months)")
        plt.tight_layout()
        plt.show()

    def __plot_model_loss(self, train_rmse_values, val_rmse_values) -> None:
        plt.figure(figsize=(10, 6))
        epochs = np.arange(len(train_rmse_values))
        plt.plot(epochs, train_rmse_values, label="Train Loss", color="blue", marker='o', markersize=3)
        plt.plot(epochs, val_rmse_values, label="Validation Loss", color="orange", marker='o', markersize=3)
        
        plt.xlabel("Epoch")
        plt.ylabel("RMSE Loss")
        plt.title("Training and Validation Loss")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()

    def predict_future(self, dataset:pd.DataFrame, months_to_test:int = 48, test_future:bool = True):
        wide_df = self.__prepare_wide_format(dataset)
        
        df = wide_df.copy()
        df['Month_Idx'] = np.arange(len(df)) % 12
        df['Month_Sin'] = np.sin(2 * np.pi * df['Month_Idx'] / 12)
        df['Month_Cos'] = np.cos(2 * np.pi * df['Month_Idx'] / 12)
        
        for i, region in enumerate(self.regions):
            df[region] = self.scalers[region].transform(df[[region]])
        
        feature_cols = self.regions + ['Month_Sin', 'Month_Cos']
        encoded_data = df[feature_cols].values.astype(np.float32)

        total_len = len(encoded_data)
        if not test_future:
            predict_start_idx = total_len - months_to_test
            steps_to_predict = months_to_test
        else:
            predict_start_idx = total_len
            steps_to_predict = months_to_test

        if predict_start_idx - self.seq_len < 0:
            raise ValueError("Not enough history to start prediction at this index.")
        
        current_window = encoded_data[predict_start_idx - self.seq_len : predict_start_idx]
        input_tensor = torch.tensor(current_window).unsqueeze(0)

        # Generate future time features so the model knows what month it is predicting
        future_indices = np.arange(predict_start_idx, predict_start_idx + steps_to_predict) % 12
        future_sin = np.sin(2 * np.pi * future_indices / 12)
        future_cos = np.cos(2 * np.pi * future_indices / 12)
        future_time = np.column_stack((future_sin, future_cos))
        future_time_tensor = torch.tensor(future_time, dtype=torch.float32).unsqueeze(0)

        self.model.eval()
        with torch.no_grad():
            # teacher_forcing is 0.0 by default, auto-feeding its own predictions
            prediction = self.model(input_tensor, future_steps=steps_to_predict, future_time_features=future_time_tensor)
            preds_np = prediction.squeeze(0).numpy()
        
        preds_np = preds_np[:steps_to_predict, :]
        
        predictions_rescaled = {}
        for i, region in enumerate(self.regions):
            predictions_rescaled[region] = self.scalers[region].inverse_transform(
                preds_np[:, i].reshape(-1, 1)
            ).flatten()

        if not test_future:
            actual = wide_df[self.regions].values[predict_start_idx : predict_start_idx + steps_to_predict]
            pred = np.zeros((steps_to_predict, self.num_regions))
            for i, region in enumerate(self.regions):
                pred[:, i] = predictions_rescaled[region]
            self.__print_summary_stats(actual, pred, "Backtest")
        
        self.__plot_prediction(wide_df, predictions_rescaled, predict_start_idx, test_future)
        return predictions_rescaled

    def __plot_prediction(self, actual_df, forecast_dict, split_idx, test_future):
        n_regions = len(self.regions)
        fig, axes = plt.subplots(n_regions, 1, figsize=(14, 16), sharex=True)
        
        for i, region in enumerate(self.regions):
            ax = axes[i]
            actuals = actual_df[region].values
            forecast = forecast_dict[region]
            
            history_start = max(0, split_idx - 120)
            
            if not test_future and split_idx < len(actuals):
                full_end = min(len(actuals), split_idx + len(forecast))
                full_range = range(history_start, full_end)
                ax.plot(full_range, actuals[history_start:full_end], 
                        color='black', alpha=0.3, linewidth=2, label="Actual")
            else:
                history_range = range(history_start, split_idx)
                ax.plot(history_range, actuals[history_start:split_idx], 
                        color='black', alpha=0.3, linewidth=2, label="Historical")
            
            forecast_range = range(split_idx, split_idx + len(forecast))
            ax.plot(forecast_range, forecast, color='blue', linewidth=2, label="Forecast")
            
            ax.axvline(x=split_idx, color='red', linestyle=':', alpha=0.5, label="Forecast Start" if i == 0 else None)
            
            ax.set_title(region.title())
            ax.set_ylabel("Anomaly (°C)")
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
        
        axes[-1].set_xlabel("Time (Months)")
        
        if test_future:
            fig.suptitle("Multi-Continent Blind Forecast", fontsize=14, y=0.995)
        else:
            fig.suptitle("Multi-Continent Backtesting: Forecast vs Actual", fontsize=14, y=0.995)
        
        plt.tight_layout()
        plt.show()

    def __print_summary_stats(self, y_true, y_pred, dataset_name="Test"):
        """
        Print performance statistics.
        
        Args:
            y_true: Ground truth
            y_pred: Predictions
            dataset_name: Name for the dataset
        """
        # Ensure numpy arrays
        if torch.is_tensor(y_true):
            y_true = y_true.numpy()
        if torch.is_tensor(y_pred):
            y_pred = y_pred.numpy()

        # Calculate overall metrics (across all regions)
        errors = y_true - y_pred
        mae = np.mean(np.abs(errors))
        rmse = np.sqrt(np.mean(errors**2))
        mean_bias = np.mean(errors)
        correlation = np.corrcoef(y_true.flatten(), y_pred.flatten())[0, 1]

        print(f"\n{'='*50}")
        print(f"OVERALL {dataset_name.upper()} SET PERFORMANCE")
        print(f"{'='*50}")
        print(f" RMSE:        {rmse:.4f}")
        print(f" MAE:         {mae:.4f}")
        print(f" Mean Bias:   {mean_bias:.4f}")
        print(f" Correlation: {correlation:.4f}")

        # Per-region performance statistics:
        print(f"\nPer-Region Performance:")
        print(f" {'Region':<15} {'RMSE':<10} {'MAE':<10} {'Correlation':<12}")
        print(f" {'-'*50}")

        for i, region in enumerate(self.regions):
            region_true = y_true[:, i]
            region_pred = y_pred[:, i]

            region_rmse = np.sqrt(np.mean((region_true - region_pred)**2))
            region_mae  = np.mean(np.abs(region_true - region_pred))
            region_corr = np.corrcoef(region_true, region_pred)[0, 1]

            print(f" {region:<15} {region_rmse:<10.4f} {region_mae:<10.4f} {region_corr:<12.4f}")

class MultiOutputLSTM(nn.Module):
    """
    LSTM that uses Teacher Forcing.
    Predicts one month, loops the prediction back into the sequence, and continues.
    """
    
    def __init__(self, input_dim, hidden_dim, layer_dim, output_dim, num_regions, dropout=0.2):
        super(MultiOutputLSTM, self).__init__()
        
        self.num_regions = num_regions
        
        self.lstm = nn.LSTM(
            input_dim, 
            hidden_dim, 
            batch_first=True, 
            num_layers=layer_dim,
            dropout=dropout if layer_dim > 1 else 0
        )
        
        self.dropout = nn.Dropout(dropout)
        
        # Output dim is the number of regions (predicting 1 month only for each)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x, future_steps, future_time_features, y_true=None, teacher_forcing_ratio=0.0):
        out, (h, c) = self.lstm(x)
        predictions = []
        current_out = out[:, -1, :] 
        
        pred = self.fc(self.dropout(current_out)) # Predict all 6 regions
        predictions.append(pred)
        
        # Autoregressive Loop for the remaining steps
        for t in range(1, future_steps):
            
            # Decide whether to use actual data (Teacher Forcing) or model's own prediction
            if y_true is not None and torch.rand(1).item() < teacher_forcing_ratio:
                # Use ground truth from the previous step
                prev_regions = y_true[:, t-1, :]
            else:
                # Use model's prediction from the previous step
                prev_regions = pred
                
            # Grab the time features (sin/cos) for the step we are currently predicting
            # and add them onto the input to match the 8-feature input size
            time_feats = future_time_features[:, t-1, :]
            next_input = torch.cat((prev_regions, time_feats), dim=1).unsqueeze(1)
            
            # Feed it forward into the LSTM along with the hidden state
            out_step, (h, c) = self.lstm(next_input, (h, c))
            
            # Predict the next month and store it
            pred = self.fc(self.dropout(out_step.squeeze(1)))
            predictions.append(pred)
            
        # Stack all predictions into a (batch, forecast_num, num_regions) tensor
        return torch.stack(predictions, dim=1)