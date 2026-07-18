import pandas as pd
import re
from app.db.database import engine
from urllib.parse import unquote

# Posibles patrones de SQLI utilizando expresiones regulares
SQLI_PATTERN = r"(\bOR\b|\bUNION\b|\bDROP\b|\bSELECT\b|--|;|\d+=\d+|'.*=.*')"

# Función para retornar un booleano si encontramos un intento de SQL Injection
def contains_sql_injection(text):
    if text is None:
        return False
    return bool(re.search(SQLI_PATTERN, text, re.IGNORECASE))

# Función para decodificar un valor, usando while por si está doblemente codificado
def decode(value):
    # isna es un valor nulo
    if pd.isna(value):
        return None

    # Convertimos a string para evitar errores
    value = str(value)

    while "%" in value:
        decoded = unquote(value)
        if decoded == value:
            break
        value = decoded

    return value

# Buscamos los request_logs que tengan contenido en request_payload o en query_params
def get_sqli_candidates():
    df = pd.read_sql("""
        SELECT id, ip_address, endpoint, request_payload, query_params, created_at
        FROM request_logs
        WHERE request_payload IS NOT NULL OR query_params IS NOT NULL
    """, engine)

    # Omitimos ip local
    TRUSTED_IPS = ["127.0.0.1"]
    df = df[~df["ip_address"].isin(TRUSTED_IPS)]

    # Decodificamos los campos request_payload y query_params para poder analizarlos correctamente
    df["decoded_payload"] = df["request_payload"].apply(decode)
    df["decoded_query"] = df["query_params"].apply(decode)

    # Marcamos si cada fila tiene contenido sospechoso en payload o en query
    df["is_sqli_payload"] = df["decoded_payload"].apply(contains_sql_injection)
    df["is_sqli_query"] = df["decoded_query"].apply(contains_sql_injection)

    # Nos quedamos solo con las filas donde alguna de las dos columnas dio True
    sqli_detected = df[(df["is_sqli_payload"]) | (df["is_sqli_query"])]

    return sqli_detected

def build_sqli_alerts():
    sqli_candidates = get_sqli_candidates()

    if sqli_candidates.empty:
        return pd.DataFrame()
    
    start_ip = sqli_candidates.groupby("ip_address")["created_at"].min() # Fecha y hora exacta del primer request por ip
    end_ip = sqli_candidates.groupby("ip_address")["created_at"].max() # Fecha y hora exacta del último request por ip

    sqli_grouped = pd.DataFrame({
        "pattern_started_at": start_ip,
        "pattern_ended_at": end_ip
    })

    sqli_grouped = sqli_grouped.reset_index()
    sqli_grouped["alert_type"] = "sql_injection"
    sqli_grouped["anomaly_score"] = 0.0

    return sqli_grouped