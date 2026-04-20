import os
import gc
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import root_mean_squared_error
import joblib

def main():
    data_dir = 'data'
    model_dir = 'models'
    os.makedirs(model_dir, exist_ok=True)
    
    print("Loading processed data...")
    data = pd.read_parquet(os.path.join(data_dir, 'processed_data.parquet'))
    
    # Train validation split
    # Since test data is month 34, we use month 33 for validation
    X_train = data[data.date_block_num < 33].drop(['item_cnt_month'], axis=1)
    Y_train = data[data.date_block_num < 33]['item_cnt_month']
    
    X_valid = data[data.date_block_num == 33].drop(['item_cnt_month'], axis=1)
    Y_valid = data[data.date_block_num == 33]['item_cnt_month']
    
    X_test = data[data.date_block_num == 34].drop(['item_cnt_month'], axis=1)
    
    print(f"X_train shape: {X_train.shape}")
    print(f"X_valid shape: {X_valid.shape}")
    
    print("Training LightGBM model...")
    model = lgb.LGBMRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=8,
        colsample_bytree=0.8,
        subsample=0.8,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(
        X_train, 
        Y_train, 
        eval_set=[(X_train, Y_train), (X_valid, Y_valid)], 
        callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(50)]
    )
    
    print("Evaluating...")
    Y_pred = model.predict(X_valid).clip(0, 20)
    rmse = root_mean_squared_error(Y_valid, Y_pred)
    print(f"Validation RMSE: {rmse:.4f}")
    
    print("Saving model...")
    joblib.dump(model, os.path.join(model_dir, 'sales_forecast_model.pkl'))
    
    print("Saving reference data for API...")
    # Saving features for month 34 to easily simulate API lookup
    X_test.to_parquet(os.path.join(data_dir, 'api_reference_data.parquet'), index=False)
    
    print("Model training complete.")

if __name__ == '__main__':
    main()
