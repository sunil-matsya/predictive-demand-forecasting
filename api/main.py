import os
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Sales Forecast API", description="Predictive Demand Forecasting Engine")

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Mount static folder
static_path = os.path.join(BASE_DIR, "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Globals to hold our model and reference data
MODEL = None
REFERENCE_DATA = None

class ForecastRequest(BaseModel):
    shop_id: int
    item_id: int
    month_block: int = 34

class TopForecastRequest(BaseModel):
    month_block: int = 34

class HistoryRequest(BaseModel):
    shop_id: int
    item_id: int

@app.on_event("startup")
def load_assets():
    global MODEL, REFERENCE_DATA
    try:
        model_path = os.path.join(BASE_DIR, 'models', 'sales_forecast_model.pkl')
        MODEL = joblib.load(model_path)
    except Exception as e:
        print(f"Error loading model: {e}")

    try:
        data_path = os.path.join(BASE_DIR, 'data', 'processed_data.parquet')
        REFERENCE_DATA = pd.read_parquet(data_path)
    except Exception as e:
        print(f"Error loading reference data: {e}")

@app.get("/health")
def health_check():
    if MODEL is None or REFERENCE_DATA is None:
        return {"status": "unhealthy", "message": "Model or data failed to load"}
    return {"status": "healthy"}

@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(static_path, "index.html"))

@app.get("/months")
def get_months():
    if REFERENCE_DATA is None:
        raise HTTPException(status_code=503, detail="Data is not loaded")
    months = sorted([int(m) for m in REFERENCE_DATA['date_block_num'].unique().tolist()], reverse=True)
    return {"months": months}

@app.post("/predict")
def predict_forecast(req: ForecastRequest):
    if MODEL is None or REFERENCE_DATA is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    
    # Query reference data
    subset = REFERENCE_DATA[
        (REFERENCE_DATA['shop_id'] == req.shop_id) & 
        (REFERENCE_DATA['item_id'] == req.item_id) & 
        (REFERENCE_DATA['date_block_num'] == req.month_block)
    ]
    
    if subset.empty:
        return {"shop_id": req.shop_id, "item_id": req.item_id, "forecast_30_days": 0.0, "message": "No data found, defaulting to 0"}
    
    X = subset.drop(columns=['item_cnt_month'], errors='ignore')
    pred = MODEL.predict(X)[0]
    pred = max(0.0, min(20.0, float(pred)))
    
    return {
        "shop_id": req.shop_id,
        "item_id": req.item_id,
        "forecast_30_days": round(pred, 4)
    }

@app.post("/top_predictions")
def top_predictions(req: TopForecastRequest):
    if MODEL is None or REFERENCE_DATA is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")
        
    subset = REFERENCE_DATA[REFERENCE_DATA['date_block_num'] == req.month_block].copy()
    if subset.empty:
        return {"top_predictions": []}
        
    X = subset.drop(columns=['item_cnt_month'], errors='ignore')
    preds = MODEL.predict(X)
    
    # Clip predictions just like single predict
    import numpy as np
    preds = np.clip(preds, 0.0, 20.0)
    
    subset['forecast'] = preds
    
    # Sort and get top 100
    top_100 = subset.sort_values(by='forecast', ascending=False).head(100)
    
    results = []
    for _, row in top_100.iterrows():
        results.append({
            "shop_id": int(row['shop_id']),
            "item_id": int(row['item_id']),
            "forecast_30_days": round(float(row['forecast']), 4)
        })
        
    return {"top_predictions": results}

@app.post("/history")
def get_history(req: HistoryRequest):
    if REFERENCE_DATA is None:
        raise HTTPException(status_code=503, detail="Data is not loaded")
        
    subset = REFERENCE_DATA[
        (REFERENCE_DATA['shop_id'] == req.shop_id) & 
        (REFERENCE_DATA['item_id'] == req.item_id)
    ]
    
    if subset.empty:
        return {"shop_id": req.shop_id, "item_id": req.item_id, "history": []}
    
    # Sort by month to ensure chronological order
    subset = subset.sort_values(by='date_block_num')
    
    # Extract only the necessary data points
    history_data = []
    import numpy as np
    
    for _, row in subset.iterrows():
        # Handle nan values that might come from parquet
        cnt = float(row['item_cnt_month'])
        if np.isnan(cnt):
            cnt = 0.0
            
        history_data.append({
            "month": int(row['date_block_num']),
            "item_cnt": cnt
        })
        
    return {
        "shop_id": req.shop_id,
        "item_id": req.item_id,
        "history": history_data
    }
