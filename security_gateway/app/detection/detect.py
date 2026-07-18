import joblib
import pandas as pd
from app.detection.extraction import extract_features
from app.detection.classification import classify_alert_type
from app.db.database import engine
from sqlalchemy import text
from app.detection.sql_injection_check import get_sqli_candidates, contains_sql_injection, build_sqli_alerts

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

all_alerts_in_db = pd.read_sql("SELECT id, ip_address, alert_type, pattern_started_at, pattern_ended_at FROM alerts", engine)

alerts_with_id = new_alerts.merge(
    all_alerts_in_db,
    on=["ip_address", "alert_type", "pattern_started_at", "pattern_ended_at"],
    how="inner" # Las filas que tienen coincidencia en ambas tablas
)

try:
    for i, alert_row in alerts_with_id.iterrows():
        select_query = text("""
            SELECT id FROM request_logs
            WHERE ip_address = :ip
            AND created_at BETWEEN :start AND :end
        """)
        with engine.connect() as connection:
            result = connection.execute(
                select_query, {
                    "ip": alert_row["ip_address"],
                    "start": alert_row["pattern_started_at"],
                    "end": alert_row["pattern_ended_at"]
                }
            )
            matching_logs = result.fetchall()

            insert_query = text("""
                INSERT INTO alert_logs (request_logs_id, alerts_id, created_at)
                VALUES (:request_log_id, :alert_id, now())
            """)
            for log in matching_logs:
                connection.execute(insert_query, {
                    "request_log_id": log.id,
                    "alert_id": alert_row["id"]
                })

            connection.commit()
except Exception as error:

    print(f"Error al insertar alert_logs: {error}")

sqli_df = build_sqli_alerts()

sqli_alerts_in_db = pd.read_sql("SELECT ip_address, alert_type, pattern_started_at, pattern_ended_at FROM alerts", engine)

sqli_merged = sqli_df.merge(
    sqli_alerts_in_db,
    on=["ip_address", "alert_type", "pattern_started_at", "pattern_ended_at"],
    how="left",
    indicator="existence"
)

new_sqli_alerts = sqli_merged[sqli_merged["existence"] == "left_only"]

new_sqli_alerts = new_sqli_alerts.drop(columns=["existence"])

if not new_sqli_alerts.empty:
    new_sqli_alerts.to_sql("alerts", engine, if_exists="append", index=False)

all_sqli_alerts_in_db = pd.read_sql("SELECT id, ip_address, alert_type, pattern_started_at, pattern_ended_at FROM alerts", engine)

sqli_alerts_with_id = new_sqli_alerts.merge(
    all_sqli_alerts_in_db,
    on=["ip_address", "alert_type", "pattern_started_at", "pattern_ended_at"],
    how="inner"
)

try:
    for i, alert_row in sqli_alerts_with_id.iterrows():
        select_query = text("""
            SELECT id FROM request_logs
            WHERE ip_address = :ip
            AND created_at BETWEEN :start AND :end
        """)
        with engine.connect() as connection:
            result = connection.execute(
                select_query, {
                    "ip": alert_row["ip_address"],
                    "start": alert_row["pattern_started_at"],
                    "end": alert_row["pattern_ended_at"]
                }
            )
            matching_logs = result.fetchall()

            insert_query = text("""
                INSERT INTO alert_logs (request_logs_id, alerts_id, created_at)
                VALUES (:request_log_id, :alert_id, now())
            """)
            for log in matching_logs:
                connection.execute(insert_query, {
                    "request_log_id": log.id,
                    "alert_id": alert_row["id"]
                })

            connection.commit()
except Exception as error:
        
    print(f"Error al insertar alert_logs: {error}")