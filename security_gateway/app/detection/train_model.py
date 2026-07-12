import joblib
from sklearn.ensemble import IsolationForest
from app.detection.extraction import extract_features

features, range_by_ip = extract_features()

# Contamination = 0.1, es decir, asume más o menos el 10% de los datos como anómalos
model = IsolationForest(contamination=0.1, random_state=42)
model.fit(features)

# Guardamos el modelo entrenado en un archivo, para no reentrenar cada vez
joblib.dump(model, "app/detection/model.pkl")
print("Modelo entrenado y guardado.")