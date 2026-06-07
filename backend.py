from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
import numpy as np
import joblib
import os

app = FastAPI(title="Turbofan Engine Predictive Maintenance API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model, classifier, and scaler
try:
    regressor = joblib.load("rul_regressor.joblib")
    classifier = joblib.load("rul_classifier.joblib")
    scaler = joblib.load("scaler.joblib")
    print("Models loaded successfully.")
except Exception as e:
    print(f"Error loading models: {e}")
    regressor = None
    classifier = None
    scaler = None

# Pre-load data
data_path = "RUL_DATA.csv"
if os.path.exists(data_path):
    df_raw = pd.read_csv(data_path)
    df_raw.dropna(inplace=True)
else:
    df_raw = None
    print(f"Error: {data_path} not found.")

FEATURE_COLS = ['Op1', 'Op2', 'S2', 'S3', 'S4', 'S7', 'S8', 'S9', 'S11', 'S12', 'S13', 'S14', 'S15', 'S17', 'S20', 'S21']

# --- Static Routes to serve Frontend ---

@app.get("/")
def read_index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/style.css")
def read_style():
    if os.path.exists("style.css"):
        return FileResponse("style.css")
    raise HTTPException(status_code=404, detail="style.css not found")

@app.get("/app.js")
def read_js():
    if os.path.exists("app.js"):
        return FileResponse("app.js")
    raise HTTPException(status_code=404, detail="app.js not found")

# --- API Routes ---

@app.get("/api/units")
def get_units():
    if df_raw is None:
        raise HTTPException(status_code=500, detail="Dataset not loaded")
    
    unique_units = sorted(df_raw['Unit'].unique().tolist())
    return {"units": unique_units}

@app.get("/api/unit/{unit_id}")
def get_unit_details(unit_id: int):
    if df_raw is None:
        raise HTTPException(status_code=500, detail="Dataset not loaded")
    
    unit_df = df_raw[df_raw['Unit'] == unit_id].copy()
    if unit_df.empty:
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")
    
    unit_df.sort_values(by="Cycle", inplace=True)
    
    # Extract features for prediction
    X_unit = unit_df[FEATURE_COLS]
    
    # Make predictions
    try:
        X_scaled = scaler.transform(X_unit)
        predicted_rul = regressor.predict(X_scaled)
        
        # Classifier probability of failure within 20 cycles
        # class 1 index is usually 1 in classes_
        anomaly_prob = classifier.predict_proba(X_scaled)[:, 1]
        is_anomaly = classifier.predict(X_scaled)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
    
    # Structure the records
    records = []
    for idx, row in enumerate(unit_df.itertuples()):
        records.append({
            "cycle": int(row.Cycle),
            "actual_rul": int(row.RUL),
            "predicted_rul": float(predicted_rul[idx]),
            "is_anomaly": int(is_anomaly[idx]),
            "anomaly_prob": float(anomaly_prob[idx]),
            "sensors": {
                "S2": float(row.S2),
                "S3": float(row.S3),
                "S4": float(row.S4),
                "S7": float(row.S7),
                "S8": float(row.S8),
                "S9": float(row.S9),
                "S11": float(row.S11),
                "S12": float(row.S12),
                "S13": float(row.S13),
                "S14": float(row.S14),
                "S15": float(row.S15),
                "S17": float(row.S17),
                "S20": float(row.S20),
                "S21": float(row.S21),
            },
            "operations": {
                "Op1": float(row.Op1),
                "Op2": float(row.Op2)
            }
        })
        
    return {
        "unit_id": unit_id,
        "total_cycles": len(records),
        "records": records
    }
