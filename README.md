# Predictive Demand Forecasting System

![Python Integration](https://img.shields.io/badge/Python-3.x-blue?style=flat&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-00a393?style=flat&logo=fastapi)
![LightGBM](https://img.shields.io/badge/LightGBM-Gradient_Boosting-fb542b?style=flat)
![Pandas](https://img.shields.io/badge/Pandas-Data_Processing-150458?style=flat&logo=pandas)

This project is an end-to-end Predictive Demand Forecasting microservice. It consumes historical sales data, engineers time-series features, trains a highly accurate Gradient Boosting model (LightGBM), and serves predictions in real-time through a scalable FastAPI backend alongside an integrated interactive dashboard.

## Overview

The core objective is to accurately forecast the total sales of a specific item at a specific shop for the upcoming month (30 days). This enables business operations to optimize inventory, minimize overstocking, and prevent out-of-stock scenarios.

### Project Structure
- `api/`: Contains the FastAPI application, serving predictions and hosting the interactive dashboard.
- `src/`: Core data science logic code (Data Processing, Feature Engineering, Model Training).
- `data/`: Datasets and processed `.parquet` feature tables.
- `models/`: Saved `joblib` LightGBM binaries (`.pkl`).
- `static/`: Frontend dashboard assets (HTML, CSS, JS).

---

## How The Model Predicts Demand (In-Depth)

The predictive prowess of this system leverages time-series cross-validation and extensive feature engineering based on the "Predict Future Sales" dataset parameters. 

Here is the step-by-step breakdown of how the system processes data and generates forecasts:

### 1. Data Cleaning & Matrix Construction
Raw daily sales data is ingested first. The system filters out extreme anomalies (e.g., negative item counts, erratic item prices). It then constructs a comprehensive grid matrix representing **every possible combination** of active `shop_id` and `item_id` for every temporal month (`date_block_num`). This ensures the model learns not only about items that sell but also explicitly learns about items that remain unsold (zero-sales).

### 2. Time-Series Feature Engineering (Lags)
The secret to the model's high accuracy lies in its **Lag Features**. Forecasting is mostly reliant on historical context. The script aggregates daily sales into total monthly sales (`item_cnt_month`). 
It then computes historical "lookbacks" (lags) for:
- **Raw Item/Shop Sales Lags**: What were the exact sales for this item in this shop exactly 1, 2, and 3 months ago?
- **Item Mean Encoding Lags**: What was the average popularity/sales of this specific item across *all shops* in the previous 1, 2, and 3 months?
- **Shop Mean Encoding Lags**: What was the average throughput of this specific shop across *all items* in the previous 1, 2, and 3 months?

### 3. LightGBM Gradient Boosting
The system uses **LightGBM (LGBMRegressor)**, a tree-based learning algorithm optimized for speed and accuracy. 
- Why LightGBM? It builds trees leaf-wise (rather than level-wise) which reduces loss much more efficiently on complex tabular data.
- The model is trained on data up to Month 32, validated carefully on Month 33, and then predicts Month 34 (the future). A custom learning rate (0.05) combined with early stopping prevents the model from overfitting.

### 4. Real-time Inference via FastAPI
When a user requests a forecast (via the dashboard or API endpoint `/predict`):
1. **Feature Lookup**: The API fetches the pre-calculated, engineered feature row for the requested `shop_id` and `item_id` in the target month from a highly optimized in-memory `.parquet` table.
2. **Prediction**: The fast LightGBM model processes this feature array and instantaneously outputs the forecasted numeric value.
3. **Clipping Constraint**: Finally, the system automatically clips outputs between `[0, 20]`. This enforces realistic bounded predictions and minimizes extreme variance in downstream supply chain operations.

---

## How to Run Locally

### Requirements
Ensure you have Python 3.8+ installed. All dependencies are listed in `requirements.txt`.

### Startup Instructions

You can start the fully integrated API Server and UI Dashboard with a single script:

**Windows (PowerShell)**:
```powershell
.\run_api.ps1
```

Once running, access the user-facing Predictive Dashboard at:
**http://localhost:8000**

### API Endpoints
- `GET /health` : Verify system status 
- `POST /predict` : Fetch the exact next 30-day forecasted quantity for a Shop/Item pair.
- `POST /top_predictions` : Fetch the top 100 highest forecasted items for the incoming month.
- `POST /history` : Track the monthly sales history of an item to chart on the dashboard.
