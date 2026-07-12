from sklearn.ensemble import IsolationForest
from app.detection.extraction import extract_features
from app.detection.clasification import classify_alert_type
from app.db.database import engine

features, range_by_ip = extract_features()

# Contamination = 0.1, es decir, asume más o menos el 10% de los datos como anómalos
# Este numero se calibra mejor más adelante
model = IsolationForest(contamination=0.1, random_state=42)
model.fit(features) # Acá hacemos que el modelo pueda acceder al DataFrame que creamos en extraction

# Por cada ip, nos dice -1 si es anómalo o 1 si no lo es
predictions = model.predict(features)
# Nos da una puntuación de anomalía (entre más negativo, más anómalo, y viceversa)
scores = model.decision_function(features)

features["predictions"] = predictions
features["anomaly_score"] = scores

anomalies = features[features["predictions"] == -1]

# Juntamos los datos de ambas tablas (anomalies y range_by_ip) por ip
alert_candidates = anomalies.join(range_by_ip)
# print(alert_candidates)

# Clasificamos el tipo de alerta fila por fila con apply y la función classify_alert_type
alert_candidates["alert_type"] = alert_candidates.apply(classify_alert_type, axis=1)

alert_candidates = alert_candidates.reset_index()

alerts_table = alert_candidates[["ip_address", "alert_type", "anomaly_score", "pattern_started_at", "pattern_ended_at"]]
# print(alerts_table)

# Insertamos los datos en la tabla alerts de la DB utilizando to_sql de pandas
alerts_table.to_sql("alerts", engine, if_exists="append", index=False)