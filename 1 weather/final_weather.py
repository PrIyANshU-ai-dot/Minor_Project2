# -*- coding: utf-8 -*-
"""final weather.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1x6xSEDBadJqXO4X9jPpLK2hsXFaeNAs0
"""

# ✅ STEP 1: Install required packages
!pip install pandas numpy matplotlib seaborn scikit-learn shap joblib requests --quiet

# ✅ STEP 2: Import necessary libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import shap
import joblib
import requests
import re

from datetime import datetime
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report

# ✅ STEP 3: Load and preprocess dataset
df = pd.read_csv('weather_dataset.csv')

df['DateTime'] = pd.to_datetime(df['DateTime'])
df.drop(columns=['DateTime'], inplace=True)
df = pd.get_dummies(df, columns=['LaunchSite'])

# 🔍 NEW: Correlation Heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(df.corr(), annot=True, fmt='.2f', cmap='coolwarm', square=True)
plt.title("Feature Correlation Heatmap")
plt.tight_layout()
plt.show()

X = df.drop('SuitableForLaunch', axis=1)
y = df['SuitableForLaunch']

# 📊 NEW: Class Distribution Plot
plt.figure(figsize=(5, 4))
sns.countplot(x=y, palette="Set2")
plt.title("Distribution of Launch Suitability Classes")
plt.xlabel("Suitable for Launch (0 = No, 1 = Yes)")
plt.ylabel("Count")
plt.tight_layout()
plt.show()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ✅ STEP 4: Feature scaling
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ✅ STEP 5: Hyperparameter tuning
param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [None, 10, 20],
    'min_samples_split': [2, 5],
}

grid_search = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid,
    cv=3,
    scoring='accuracy',
    n_jobs=-1
)

grid_search.fit(X_train_scaled, y_train)
model = grid_search.best_estimator_
print("✅ Best Hyperparameters:", grid_search.best_params_)

# ✅ STEP 6: Evaluate the model
y_pred = model.predict(X_test_scaled)

plt.figure(figsize=(6, 4))
sns.heatmap(confusion_matrix(y_test, y_pred), annot=True, fmt='d', cmap='Blues')
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()

print("Classification Report:\n")
print(classification_report(y_test, y_pred))

# 🔍 NEW: SHAP Summary Plot
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_train_scaled)

# Check if binary or multiclass (list or single array)
if isinstance(shap_values, list):
    shap_vals = shap_values[1]  # Class 1: Suitable
else:
    shap_vals = shap_values

shap.summary_plot(shap_vals, pd.DataFrame(X_train_scaled, columns=X.columns), plot_type="bar", show=False)
plt.title("SHAP Feature Importance (Class 1 - Suitable)")
plt.tight_layout()
plt.show()


# ✅ STEP 7: Feature Importance Plot
importances = model.feature_importances_
feature_names = X.columns
indices = np.argsort(importances)[::-1]

plt.figure(figsize=(10, 6))
sns.barplot(x=importances[indices], y=np.array(feature_names)[indices])
plt.title("Weather Feature Importances")
plt.xlabel("Importance")
plt.ylabel("Feature")
plt.tight_layout()
plt.show()

# ✅ STEP 8: Save model, scaler, and feature names
joblib.dump(model, "falcon9_weather_model.pkl")
joblib.dump(scaler, "weather_scaler.pkl")
joblib.dump(X.columns.tolist(), "feature_names.pkl")
print("✅ Model, scaler, and feature names saved successfully!")

# ✅ STEP 9: Launch Site Coordinates
launch_sites = {
    'Cape Canaveral': (28.3922, -80.6077),
    'Kennedy LC-39A': (28.5733, -80.6469),
    'VAFB SLC 4E': (34.6328, -120.6108)
}

# ✅ STEP 10: NOAA Weather Fetching Function
def get_nws_forecast(lat, lon):
    point_url = f"https://api.weather.gov/points/{lat},{lon}"
    point_response = requests.get(point_url).json()
    forecast_url = point_response['properties']['forecast']
    forecast_data = requests.get(forecast_url).json()
    return forecast_data['properties']['periods']

# ✅ STEP 11: User Input
print("\n🗓️ Available Launch Sites:")
for site in launch_sites:
    print(f"- {site}")

site_input = input("\nEnter Launch Site exactly as shown above: ")
launch_date = input("Enter desired launch date (YYYY-MM-DD): ")

if site_input not in launch_sites:
    print("❌ Invalid Launch Site. Exiting.")
    exit()

# ✅ STEP 12: Fetch Forecast
lat, lon = launch_sites[site_input]
forecast_periods = get_nws_forecast(lat, lon)

selected_forecast = None
for period in forecast_periods:
    if launch_date in period['startTime']:
        selected_forecast = period
        break

if not selected_forecast:
    print("❌ Forecast for given date not found. Try a closer date.")
    exit()

# ✅ STEP 13: Prepare Input
short_desc = selected_forecast['shortForecast'].lower()

weather_input = {
    'Temperature (°C)': (selected_forecast['temperature'] - 32) * 5/9 if selected_forecast['temperatureUnit'] == 'F' else selected_forecast['temperature'],
    'Humidity (%)': np.random.randint(50, 90),
    'Wind Speed (km/h)': float(re.findall(r'\d+', selected_forecast['windSpeed'])[0]) * 1.609,
    'Cloud Cover (%)': 100 if 'cloudy' in short_desc else (50 if 'partly' in short_desc else 0),
    'Visibility (km)': np.random.randint(5, 10),
    'Rain?': 1 if 'rain' in short_desc else 0,
    'Thunderstorm?': 1 if 'thunder' in short_desc else 0
}

# Add one-hot encoding manually
weather_input[f'LaunchSite_{site_input}'] = 1

# Convert to DataFrame
input_df = pd.DataFrame([weather_input])

# ✅ STEP 14: Match feature columns from training
feature_names = joblib.load("feature_names.pkl")

# Add any missing columns (fill with 0)
for col in feature_names:
    if col not in input_df.columns:
        input_df[col] = 0

# Reorder columns to match model input
input_df = input_df[feature_names]

# ✅ STEP 15: Predict Suitability
model = joblib.load("falcon9_weather_model.pkl")
scaler = joblib.load("weather_scaler.pkl")

scaled_input = scaler.transform(input_df)
prediction = model.predict(scaled_input)[0]
proba = model.predict_proba(scaled_input)[0]

# ✅ STEP 16: Output Result
print("\n🔹 Forecast for", site_input, "on", launch_date)
print(f"🌡️ Temperature: {weather_input['Temperature (°C)']:.1f} °C")
print(f"💨 Wind: {weather_input['Wind Speed (km/h)']:.1f} km/h")
print(f"☁️ Clouds: {weather_input['Cloud Cover (%)']}%")
print(f"🌧️ Rain: {'Yes' if weather_input['Rain?'] else 'No'}")
print(f"⛈️ Thunderstorm: {'Yes' if weather_input['Thunderstorm?'] else 'No'}")

print("\n🚀 Launch Suitability Prediction:")
print("✅ Suitable for Launch" if prediction == 1 else "❌ Not Suitable for Launch")
print(f"Confidence: {proba[prediction]*100:.2f}%")

# 📊 NEW: Prediction Probability Plot
labels = ["Not Suitable", "Suitable"]
plt.figure(figsize=(5, 3))
sns.barplot(x=labels, y=proba, palette="viridis")
plt.title("Launch Suitability Prediction Confidence")
plt.ylabel("Probability")
plt.ylim(0, 1)
for i, v in enumerate(proba):
    plt.text(i, v + 0.02, f"{v*100:.1f}%", ha='center')
plt.tight_layout()
plt.show()

from sklearn.metrics import roc_curve, auc

fpr, tpr, _ = roc_curve(y_test, model.predict_proba(X_test_scaled)[:, 1])
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(6, 4))
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f"ROC curve (AUC = {roc_auc:.2f})")
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("Receiver Operating Characteristic (ROC)")
plt.legend(loc="lower right")
plt.tight_layout()
plt.show()