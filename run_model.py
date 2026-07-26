import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

df = pd.read_csv('RUL_DATA.csv')
df.dropna(inplace=True)
df.fillna(method='ffill', inplace=True)
drop_features = ['S18', 'S19']
if set(drop_features).issubset(df.columns):
    df.drop(drop_features, axis=1, inplace=True)

y = df['RUL']
X = df.drop(['RUL'], axis=1)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
print('MSE:', mean_squared_error(y_test, y_pred))
print('MAE:', mean_absolute_error(y_test, y_pred))
print('R^2:', r2_score(y_test, y_pred))
