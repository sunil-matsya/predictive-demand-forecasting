import pandas as pd
import joblib

model_path = 'models/sales_forecast_model.pkl'
data_path = 'data/api_reference_data.parquet'

model = joblib.load(model_path)
df = pd.read_parquet(data_path)

# Predict all
preds = model.predict(df)
df['prediction'] = preds

# Get the row with max pred
max_idx = df['prediction'].idxmax()
row = df.loc[max_idx]

print(f"Max shop_id: {int(row['shop_id'])}")
print(f"Max item_id: {int(row['item_id'])}")
print(f"Max prediction: {row['prediction']}")
