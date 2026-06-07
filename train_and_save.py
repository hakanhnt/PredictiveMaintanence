import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib

print("Starting model training pipeline...", flush=True)

# Load dataset
df = pd.read_csv("RUL_DATA.csv")
print(f"Data loaded. Shape: {df.shape}", flush=True)

# Clean dataset
df.dropna(inplace=True)
df.drop(['S18', 'S19'], axis=1, inplace=True, errors='ignore')
drop_sensors = ["S1", "S5", "S6", "S10", "S16"]
df.drop(drop_sensors, axis=1, inplace=True, errors='ignore')
df.drop(['Op3'], axis=1, inplace=True, errors='ignore')

# 1. Define targets
y_reg = df['RUL']
df['Target_20_Cycles'] = np.where(df['RUL'] <= 20, 1, 0)
y_cls = df['Target_20_Cycles']

# 2. Define features (Excluding target, Unit, and Cycle to prevent leakage)
X = df.drop(['RUL', 'Target_20_Cycles', 'Unit', 'Cycle'], axis=1)
print(f"Features list: {list(X.columns)}", flush=True)

# 3. Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print("Features scaled successfully.", flush=True)

# 4. Train RUL Regressor
print("Training RandomForestRegressor...", flush=True)
regressor = RandomForestRegressor(n_estimators=100, max_depth=12, min_samples_leaf=10, random_state=1339, n_jobs=-1)
regressor.fit(X_scaled, y_reg)
print("Regressor trained.", flush=True)

# 5. Train Anomaly/Maintenance Classifier (Target: RUL <= 20 cycles)
print("Training RandomForestClassifier...", flush=True)
classifier = RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_leaf=10, random_state=1339, n_jobs=-1)
classifier.fit(X_scaled, y_cls)
print("Classifier trained.", flush=True)

# 6. Save models and scaler
joblib.dump(regressor, "rul_regressor.joblib")
joblib.dump(classifier, "rul_classifier.joblib")
joblib.dump(scaler, "scaler.joblib")
print("Models and scaler saved successfully:", flush=True)
print("  - rul_regressor.joblib", flush=True)
print("  - rul_classifier.joblib", flush=True)
print("  - scaler.joblib", flush=True)

print("Pipeline completed successfully.", flush=True)
