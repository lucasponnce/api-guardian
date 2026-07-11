import pandas as pd
from app.db.database import engine

df = pd.read_sql("SELECT * FROM request_logs", engine)

# Calculamos la cantidad de requests por cada ip
requests_por_ip = df.groupby("ip_address").size()

# Agregamos una columna booleana que indique si el request falló
df["es_fallo"] = df["status_code"] >= 400

# Calculamos la tasa de fallos por cada ip
tasa_fallos_por_ip = df.groupby("ip_address")["es_fallo"].mean()

# Calculamos la cantidad de endpoints distintos por ip
endpoints_distintos_por_ip = df.groupby("ip_address")["endpoint"].nunique()

features = pd.DataFrame({
    "total_requests": requests_por_ip,
    "tasa_fallos": tasa_fallos_por_ip,
    "total_endpoints": endpoints_distintos_por_ip
})
print(features)