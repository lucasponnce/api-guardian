import pandas as pd
from app.db.database import engine

# Agrego la ip local para posteriormente excluirla del análisis
TRUSTED_IPS = ["127.0.0.1"]

def extract_features():
    df = pd.read_sql("SELECT * FROM request_logs", engine)
    # Excluímos la ip local
    df = df[~df["ip_address"].isin(TRUSTED_IPS)]

    # Agregamos una columna booleana que indique si el request falló
    df["es_fallo"] = df["status_code"] >= 400

    # Calculamos la cantidad de requests por cada ip
    requests_por_ip = df.groupby("ip_address").size()
    # Calculamos la tasa de fallos por cada ip
    tasa_fallos_por_ip = df.groupby("ip_address")["es_fallo"].mean()
    # Calculamos la cantidad de endpoints distintos por ip
    endpoints_distintos_por_ip = df.groupby("ip_address")["endpoint"].nunique()

    # Hacemos un DataFrame con las 3 características calculadas
    features = pd.DataFrame({
        "total_requests": requests_por_ip,
        "failure_rate": tasa_fallos_por_ip,
        "different_endpoints": endpoints_distintos_por_ip
    })

    start_ip = df.groupby("ip_address")["created_at"].min() # Fecha y hora exacta del primer request por ip
    end_ip = df.groupby("ip_address")["created_at"].max() # Fecha y hora exacta del último request por ip

    # Creamos la "ventana" de tiempo
    range_by_ip = pd.DataFrame({
        "pattern_started_at": start_ip,
        "pattern_ended_at": end_ip
    })

    return features, range_by_ip
