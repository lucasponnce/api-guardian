import pandas as pd
from app.db.database import engine

def extract_features():
    df = pd.read_sql("SELECT * FROM request_logs", engine)
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
        "tasa_fallos": tasa_fallos_por_ip,
        "endpoints_distintos": endpoints_distintos_por_ip
    })

    return features
