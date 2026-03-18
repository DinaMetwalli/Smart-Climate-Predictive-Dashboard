""" A Multi-step STATEFUL model. Takes in multiple continents and produces a prediction for each."""

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.utils.data as data
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

class MultistepLSTM():
    def __init__(self, seq_len: int, forecast_num:int):
        self.regions = ['africa', 'asia', 'europe', 'northAmerica', 'southAmerica', 'oceania']
        self.dataset = None
        self.num_regions = len(self.regions)
        self.seq_len = seq_len
        self.forecast_num = forecast_num # Amount of months to predict for the future at each step        
        self.num_features = self.num_regions + 2
        self.output_dim = self.forecast_num * self.num_regions
        self.scaler = MinMaxScaler(feature_range=(-1, 1))

        hidden_dim = 128
        layer_dim = 1

        self.model = LSTMModel(
            self.num_features,
            hidden_dim,
            layer_dim,
            self.output_dim,
            dropout = 0.3
            )
        
        print("Initialising multivariate stateful LSTM model.")
        print(f"Input features: {self.num_features} (6 continents + 2 cyclical)")
        print(f"Output: {self.forecast_num} months × {self.num_regions} continents = {self.output_dim} values")

    def set_dataset(self, data: pd.DataFrame) -> None:
        self.dataset = data

    def __prepare_wide_dataset(self, dataset) -> pd.DataFrame:
        """
        Convert long format df (stacked continents) to wide format (continents as columns).
        This allows multiple input features with one for each continent.
        """

        df = dataset.copy()
        
        # Pivot to wide format
        wide_df = df.pivot(columns='Region', values='Anomaly')
        wide_df = wide_df.sort_index()
        
        # Ensure all regions are present
        for region in self.regions:
            if region not in wide_df.columns:
                raise ValueError(f"Missing region '{region}' in dataset!")
        
        # Reorder columns to match self.regions order
        wide_df = wide_df[self.regions]
        
        print("Converted to wide format:")
        print(wide_df.head())
        
        return wide_df

    def __encode_features(self, wide_df: pd.DataFrame, fit=False) -> np.ndarray:
        """
        Add cyclical time/seasonal features.
        """
        df = wide_df.copy()
        
        # Add cyclical monthly encoding
        df['Month_Idx'] = np.arange(len(df)) % 12
        df['Month_Sin'] = np.sin(2 * np.pi * df['Month_Idx'] / 12)
        df['Month_Cos'] = np.cos(2 * np.pi * df['Month_Idx'] / 12)

        if fit:
            # Scale everything except the cyclical columns
            df[self.regions] = self.scaler.fit_transform(df[self.regions])
        else:
            # transform only to avoid data leakage?
            df[self.regions] = self.scaler.transform(df[self.regions])
        
        # Final feature order: [ africa, asia, europe, northAm, southAm, oceania, sin, cos ]
        feature_cols = self.regions + ['Month_Sin', 'Month_Cos']

        # show what the data looks like
        print(df.head())
        
        return df[feature_cols].values.astype(np.float32)
    
    def __create_sequences(self, data):
        """
        input: (seq_len, 8)
        output: (forecast_num, 6)
        
        X shape: (samples, seq_len, 8)
        y shape: (samples, forecast_num, 6)
        """
        X, y = [], []

        for i in range(len(data) - self.seq_len - self.forecast_num + 1):
            X.append(data[i : i + self.seq_len])
            y.append(data[i + self.seq_len : i + self.seq_len + self.forecast_num, :self.num_regions])
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"Created -> {len(X)} sequences.")
        print(f"X shape: {X.shape}")
        print(f"y shape: {y.shape}")
        
        return torch.tensor(X), torch.tensor(y)
    
    def __inverse_scale(self, data):
        """
        Helper function to inverse transform scaled predictions or expected actuals back to original values

        (Reshapes 3D data into 2D for passing through the scaler then restores to original shape)
        """
        original_shape = data.shape
        reshaped = data.reshape(-1, self.num_regions)
        inv = self.scaler.inverse_transform(reshaped)
        return inv.reshape(original_shape)
    
    def train_model(self):
        """
        The current training loop looks like:
            
            Batch -> forward -> loss -> backward -> update -> evaluate RMSE
            ...
            which repeats every epoch
        """

        TRAIN_SPLIT = 0.8

        wide_df = self.__prepare_wide_dataset(self.dataset)
        encoded_data = self.__encode_features(wide_df, fit=True)

        split_idx = int(len(encoded_data) * TRAIN_SPLIT)

        train_data = encoded_data[:split_idx]
        test_data = encoded_data[split_idx - self.seq_len:]

        # Create sequences for both the training data and testing data after split
        X_train, y_train = self.__create_sequences(train_data)
        X_test, y_test = self.__create_sequences(test_data)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.0005, weight_decay=1e-4)

        # Split data into mini batches using data loader
        # Each batch will contain: x -> input sequences, y -> target values for those sequences
        loader = data.DataLoader(data.TensorDataset(X_train, y_train), shuffle=False, batch_size=64, drop_last=True)

        # MSE loss for evaluation/backpropagation
        criterion = nn.MSELoss()

        num_epochs = 200
        best_state = None
        best_val_rmse = float('inf')
        patience = 60
        patience_counter = 0

        train_rmse_values = []
        val_rmse_values = []

        print("Training...")
        for epoch in range(num_epochs):
            self.model.train()
            # Reset the hidden state at the start of each epoch, otherwise the model will try to
            # Carry memory across epochs which will make training unstable
            self.model.hidden = None

            for X_batch, y_batch in loader:
                y_pred = self.model(X_batch)
                y_pred = y_pred.view(-1, self.forecast_num, self.num_regions)
                loss = criterion(y_pred, y_batch)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                # Detach the hidden state in each batch
                # Otherwise, backpropagation would happen every batch since training started
                if self.model.hidden is not None:
                    self.model.hidden = tuple(h.detach() for h in self.model.hidden)
            
            # Evaluate every epoch:

            self.model.eval()
            with torch.no_grad():

                self.model.hidden = None
                train_pred = self.model(X_train)
                train_pred = train_pred.view(-1, self.forecast_num, self.num_regions)

                train_rmse = torch.sqrt(criterion(train_pred, y_train)).item()
                
                self.model.hidden = None
                test_pred = self.model(X_test)
                test_pred = test_pred.view(-1, self.forecast_num, self.num_regions)
                
                val_rmse = torch.sqrt(criterion(test_pred, y_test)).item()

                train_rmse_values.append(train_rmse)
                val_rmse_values.append(val_rmse)
            
            print(f"Epoch {epoch}: Train RMSE {train_rmse:.4f}, Val RMSE {val_rmse:.4f}")

            if val_rmse < best_val_rmse:
                best_val_rmse = val_rmse
                patience_counter = 0
                best_state = self.model.state_dict().copy()
            else:
                patience_counter += 1
            
            if patience_counter >= patience:
                print(f"-> Early stopping at epoch {epoch}. Best Val RMSE: {best_val_rmse:.4f}")
                self.model.load_state_dict(best_state)
                break

        print("\n" + "="*60)
        print("TRAINING COMPLETE - DETAILED PERFORMANCE METRICS")
        print("="*60)
        
        # Final evaluation with best model
        self.model.eval()
        with torch.no_grad():
            self.model.hidden = None
            final_train_pred = self.model(X_train).view(-1, self.forecast_num, self.num_regions)
            
            self.model.hidden = None
            final_test_pred = self.model(X_test).view(-1, self.forecast_num, self.num_regions)
        
        # Inverse scale
        final_train_pred_inv = self.__inverse_scale(final_train_pred.numpy())
        final_test_pred_inv = self.__inverse_scale(final_test_pred.numpy())
        y_train_inv = self.__inverse_scale(y_train.numpy())
        y_test_inv = self.__inverse_scale(y_test.numpy())
        
        # Print stats for both training and test sets
        self.__print_summary_stats(y_train_inv, final_train_pred_inv, dataset_name="Train")
        self.__print_summary_stats(y_test_inv, final_test_pred_inv, dataset_name="Validation")

        self.__plot_training_results(X_train, X_test, split_idx, wide_df)
        self.__plot_model_loss(train_rmse_values, val_rmse_values)
        self.__plot_forecast_horizon_error(X_test, y_test)

    def __plot_training_results(self, X_train, X_test, split_idx, wide_df):

        self.model.eval()

        with torch.no_grad():

            # Predict training data
            self.model.hidden = None
            train_pred = self.model(X_train)
            train_pred = train_pred.view(-1, self.forecast_num, self.num_regions)

            # Predict test data
            self.model.hidden = None
            test_pred = self.model(X_test)
            test_pred = test_pred.view(-1, self.forecast_num, self.num_regions)

        # Convert to numpy
        train_pred = train_pred.numpy()
        test_pred = test_pred.numpy()

        # Only use first forecast step for alignment
        train_pred = train_pred[:,0,:]
        test_pred = test_pred[:,0,:]

        # Inverse scale
        train_pred = self.scaler.inverse_transform(train_pred)
        test_pred = self.scaler.inverse_transform(test_pred)

        # Get the actual data for comparison
        actual = wide_df[self.regions].values

        fig, axes = plt.subplots(self.num_regions, 1, figsize=(15, 16), sharex=True)

        for i, region in enumerate(self.regions):

            ax = axes[i]

            # Plot actual anomalies
            ax.plot(actual[:,i], label="Actual", color="black", alpha=0.3)

            # Training predictions
            train_range = range(self.seq_len, self.seq_len + len(train_pred))
            ax.plot(train_range, train_pred[:,i], label="Train Prediction", color="blue")

            # Testing predictions
            test_start = split_idx - self.forecast_num
            test_range = range(test_start, test_start + len(test_pred))
            ax.plot(test_range, test_pred[:,i], label="Test Prediction", color="red")

            # Train/test split
            ax.axvline(test_start, linestyle="--", color="gray")

            ax.set_title(region)
            ax.set_ylabel("Temperature anomaly (°C)")
            ax.legend()

        axes[-1].set_xlabel("Time (Months)")

        plt.tight_layout()
        plt.show()
    
    def __plot_model_loss(self, train_rmse_values, val_rmse_values) -> None:
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

    def plot_backtest(self, preds, wide_df, predict_start_idx):

        import matplotlib.pyplot as plt

        n_regions = self.num_regions
        fig, axes = plt.subplots(n_regions, 1, figsize=(12, 14), sharex=True)
        actual_full = wide_df[self.regions].values
        actual = actual_full[predict_start_idx : predict_start_idx + self.forecast_num]

        for i, region in enumerate(self.regions):
            ax = axes[i]

            # Get the forecast_num values for the one shot prediction
            pred_series = preds[0,:,i]

            ax.plot(actual[:,i], label="Actual", alpha=0.3, linewidth=1, color='black')
            ax.plot(pred_series, label="Predicted", linewidth=1, color='blue')

            ax.set_title(region)
            ax.set_ylabel("Anomaly (°C)")

            ax.legend()

        axes[-1].set_xlabel("Time (Months)")

        plt.tight_layout()
        plt.show()

    def __plot_forecast_horizon_error(self, X_test, y_test):
        """
        Plots the increase in error over the forecast_num months predicted.
        E.g. if predicting 36 months for each step, the error would be the lowest
        on month 1 prediction and the highest on month 36 prediction.
        """
        self.model.eval()

        with torch.no_grad():

            self.model.hidden = None
            preds = self.model(X_test)
            preds = preds.view(-1, self.forecast_num, self.num_regions)

        preds = preds.numpy()
        actual = y_test.numpy()

        # Inverse scale
        preds = self.__inverse_scale(preds)
        actual = self.__inverse_scale(actual)

        horizon_rmse = []

        # Compute RMSE for each forecast step
        for h in range(self.forecast_num):

            pred_step = preds[:, h, :]
            actual_step = actual[:, h, :]

            rmse = np.sqrt(np.mean((pred_step - actual_step) ** 2))

            horizon_rmse.append(rmse)

        plt.figure(figsize=(10,6))

        plt.plot(range(1, self.forecast_num + 1), horizon_rmse)

        plt.title("Forecast Error vs Prediction Horizon")
        plt.xlabel("Forecast Month Ahead")
        plt.ylabel("RMSE (°C anomaly)")

        plt.grid(True)

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

        # Flatten for correlation
        y_true_flat = y_true.flatten()
        y_pred_flat = y_pred.flatten()
        
        # Calculate overall metrics (across all regions)
        errors = y_true - y_pred
        mae = np.mean(np.abs(errors))
        rmse = np.sqrt(np.mean(errors**2))
        mean_bias = np.mean(errors)
        correlation = np.corrcoef(y_true_flat, y_pred_flat)[0, 1]        
        
        print(f"\n{'='*50}")
        print(f"OVERALL {dataset_name.upper()} SET PERFORMANCE")
        print(f"{'='*50}")
        print(f" RMSE:        {rmse:.4f} °C")
        print(f" MAE:         {mae:.4f} °C")
        print(f" Mean Bias:   {mean_bias:.4f} °C")
        print(f" Correlation: {correlation:.4f}")
        print(f" Samples:     {y_true.shape[0]}")
        
        # Per-region performance statistics:
        print(f"\nPer-Region Performance:")
        print(f" {'Region':<15} {'RMSE':<10} {'MAE':<10} {'Correlation':<12}")
        print(f" {'-'*50}")
        
        for i, region in enumerate(self.regions):
            region_true = y_true[:, :, i].flatten()
            region_pred = y_pred[:, :, i].flatten()
            
            region_rmse = np.sqrt(np.mean((region_true - region_pred)**2))
            region_mae = np.mean(np.abs(region_true - region_pred))
            region_corr = np.corrcoef(region_true, region_pred)[0, 1]
            
            print(f" {region:<15} {region_rmse:<10.4f} {region_mae:<10.4f} {region_corr:<12.4f}")
    
    def backtest(self, months_to_backtest:int, dataset: pd.DataFrame):

        if self.dataset is None:
            raise ValueError("Model has not been trained yet!")

        # Prepare dataset in the same way as training to make sure inference matches training
        wide_df = self.__prepare_wide_dataset(dataset)
        encoded = self.__encode_features(wide_df, fit=False)

        total_len = len(encoded)
        predict_start_idx = total_len - months_to_backtest

        # Raise an error if the history input window won't be enough
        if predict_start_idx - self.seq_len < 0:
            raise ValueError("Not enough history to start prediction.")
        
        input_window = encoded[predict_start_idx - self.seq_len: predict_start_idx]
        input_tensor = torch.tensor(input_window).unsqueeze(0)

        self.model.eval()
        preds = []
        with torch.no_grad():
            self.model.hidden = None
            pred = self.model(input_tensor)

            print(f"Shape of input tensor -> {input_tensor.shape}")
            print(f"Shape of model prediction -> {pred.shape}")

            pred = pred.view(self.forecast_num, self.num_regions)
            preds.append(pred.squeeze(0).numpy())

            # Detach hidden state
            if self.model.hidden is not None:
                self.model.hidden = tuple(h.detach() for h in self.model.hidden)

        preds = np.array(preds)

        # Inverse scaling
        preds = self.__inverse_scale(preds)

        # Get actual values for comparison
        actual_full = wide_df[self.regions].values
        actual = actual_full[predict_start_idx : predict_start_idx + self.forecast_num]
        
        # Reshape actual to match preds shape (1, forecast_num, num_regions)
        actual_reshaped = actual.reshape(1, self.forecast_num, self.num_regions)
        
        # Print performance stats
        self.__print_summary_stats(actual_reshaped, preds, dataset_name="Backtest")
    
        self.plot_backtest(preds, wide_df, predict_start_idx)

class LSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, layer_dim, output_dim, dropout):
        super(LSTMModel, self).__init__()

        self.lstm = nn.LSTM(
                input_dim,
                hidden_dim,
                batch_first=True,
                num_layers=layer_dim,
                dropout=dropout if layer_dim > 1 else 0
            )

        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, output_dim)

        # A placeholder for the hidden state to be preserved later.
        self.hidden = None

    def forward(self, x):
        out, self.hidden = self.lstm(x, self.hidden)
        out = out[:, -1]
        out = self.dropout(out)
        out = self.fc(out)
        return out