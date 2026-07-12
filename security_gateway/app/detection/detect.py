import joblib
import pandas as pd
from app.detection.extraction import extract_features
from app.detection.classification import classify_alert_type
from app.db.database import engine

# Cargamos el modelo ya entrenado, en vez de entrenar de nuevo
model = joblib.load("app/detection/model.pkl")

features, range_by_ip = extract_features()

# Por cada ip, nos dice -1 si es anómalo o 1 si no lo es
predictions = model.predict(features)
# Nos da una puntuación de anomalía (entre más negativo, más anómalo, y viceversa)
scores = model.decision_function(features)

features["predictions"] = predictions
features["anomaly_score"] = scores

# Filtramos solamente las filas que fueron clasificadas como anómalas (predictions = -1)
anomalies = features[features["predictions"] == -1]

# Juntamos los datos de ambas tablas (anomalies y range_by_ip) por ip
alert_candidates = anomalies.join(range_by_ip)

# Clasificamos el tipo de alerta fila por fila con apply y la función classify_alert_type
alert_candidates["alert_type"] = alert_candidates.apply(classify_alert_type, axis=1)

# Hacemos que la columna ip_address no sea el índice, sino una columna normal
alert_candidates = alert_candidates.reset_index()

# Nos quedamos solamente con las columnas que queremos insertar en la tabla alerts de la DB
alerts_table = alert_candidates[["ip_address", "alert_type", "anomaly_score", "pattern_started_at", "pattern_ended_at"]]

# Guardamos en una variable aparte los datos de las alertas
existing_alerts = pd.read_sql("SELECT ip_address, alert_type, pattern_started_at, pattern_ended_at FROM alerts", engine)

without_duplicated = alerts_table.merge(
    existing_alerts,
    on=["ip_address", "alert_type", "pattern_started_at", "pattern_ended_at"],
    how="left",
    indicator="existence" # Esto es clave ya que nos devuelve "left_only" si la alerta no es duplicada (para poder filtrarla)
)

# Nos quedamos solo con las filas (alertas) donde el valor de la columna "existence" es left_only (es decir, es una alerta nueva)
new_alerts = without_duplicated[without_duplicated["existence"] == "left_only"]
# Una vez filtradas las alertas nuevas, borramos la columna "existence" que usamos para que no tire error to_sql posteriormente
new_alerts = new_alerts.drop(columns=["existence"])

# Ahora insertamos los datos en la tabla alerts de la DB utilizando to_sql de pandas
new_alerts.to_sql("alerts", engine, if_exists="append", index=False)
