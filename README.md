# API Guardian

Proyecto personal desarrollado durante la carrera de Ingeniería en Sistemas de Información (UTN FRVM).

## Objetivo

Diseñar un sistema de monitoreo de seguridad para APIs REST, capaz de detectar comportamiento anómalo (fuerza bruta, IDOR, scraping/enumeración, abuso de rate limit, intentos de SQL injection, fuzzing de endpoints) combinando reglas y Machine Learning no supervisado.

En vez de depender solo de reglas fijas ("bloquear si hay más de X requests por segundo"), el sistema aprende cuál es el comportamiento normal de tráfico hacia una API y marca como sospechoso lo que se desvía de ese patrón.

## Alcance del sistema

1. API REST objetivo con autenticación, roles y recursos, usada como banco de pruebas
2. Middleware de logging que registra cada request (IP, endpoint, método, payload, status code, tiempos)
3. Simulador de tráfico normal y de tráfico de ataque para entrenamiento y pruebas
4. Motor de detección de anomalías basado en Isolation Forest (scikit-learn)
5. Generación de alertas asociadas a los requests que las originaron, con estado de revisión
6. Dashboard web para visualización de alertas

## Tecnologías

* Base de datos: PostgreSQL 17
* Backend: Python 3 + FastAPI
* ORM: SQLAlchemy
* Autenticación: JWT (python-jose) + hasheo de contraseñas con bcrypt (passlib)
* Análisis de datos: pandas
* Machine Learning: scikit-learn (Isolation Forest), persistencia del modelo con joblib
* Orquestación: Docker + Docker Compose

## Arquitectura (visión general)

El proyecto está pensado en componentes separados:

1. **`api/`** — API REST "objetivo" (registro, login con JWT, endpoint protegido `/me`, consulta de usuarios por ID) que sirve como banco de pruebas. Incluye el middleware que loguea cada request en `request_logs`.
2. **`security_gateway/`** — servicio de análisis: extracción de features a partir de `request_logs`, entrenamiento del modelo de detección de anomalías (Isolation Forest) y generación de alertas. No intercepta tráfico en vivo; lee los logs generados por `api/`.
3. **`traffic_simulator/`** — scripts que generan tráfico normal (`normal_traffic.py`) y tráfico de ataque simulado (`attack_simulator.py`: fuerza bruta, scraping/IDOR, endpoint fuzzing) contra la API objetivo.
4. **`dashboard/`** — panel donde se visualizan las alertas generadas. *(pendiente)*

## Modelo de datos

El diseño contempla 6 tablas:

- `users` — usuarios del sistema.
- `roles` / `user_roles` — roles y su asignación many-to-many a usuarios.
- `request_logs` — registro de cada request recibido por la API (IP, método, endpoint, query params, payload, status code, tiempo de respuesta, usuario si está autenticado).
- `alerts` — alertas generadas a partir de patrones sospechosos detectados (tipo, score de anomalía, ventana temporal del patrón, estado de revisión).
- `alert_logs` — tabla intermedia que vincula cada alerta con los `request_logs` puntuales que la originaron.

Tipos de alerta contemplados: `bruteforce`, `idor`, `scraping`, `rate_limit`, `sql_injection`, `endpoint_fuzzing`.

El schema completo (DDL) vive en [`database/init.sql`](./database/init.sql) y se aplica automáticamente al levantar el contenedor de PostgreSQL.

## Estado actual del proyecto

- [x] Diseño del DER y modelado de relaciones (incluye tabla intermedia many-to-many y relación 1 a muchos vía tabla puente)
- [x] `init.sql` con constraints (`NOT NULL`, `CHECK`, `UNIQUE`, `DEFAULT`), índices y foreign keys
- [x] PostgreSQL corriendo en Docker, con credenciales gestionadas por `.env`
- [x] Modelos SQLAlchemy de las 6 tablas (`User`, `Role`, `user_roles`, `RequestLog`, `Alert`, `AlertLog`)
- [x] Conexión verificada entre FastAPI y PostgreSQL
- [x] Endpoints de autenticación (registro, login con JWT, endpoint protegido `/me`)
- [x] Endpoint de consulta de usuario por ID (`/users/{id}`, banco de pruebas para IDOR/scraping)
- [x] Middleware de logging de requests en `api/`
- [x] Simulador de tráfico normal (`traffic_simulator/normal_traffic.py`)
- [x] Simulador de ataques: fuerza bruta, scraping, endpoint fuzzing (`traffic_simulator/attack_simulator.py`)
- [x] Extracción de features por IP (volumen de requests, tasa de fallos, diversidad de endpoints) con pandas
- [x] Entrenamiento del modelo de detección (Isolation Forest) y persistencia con joblib
- [x] Generación de alertas a partir del modelo, con clasificación por tipo de ataque
- [x] Exclusión de IPs de confianza y prevención de alertas duplicadas
- [ ] Vinculación de alertas con los `request_logs` puntuales que las originaron (`alert_logs`)
- [ ] Dashboard de alertas

## Cómo levantar el entorno (hasta ahora)

### 1. Variables de entorno

Copiar `.env.example` a `.env` en la raíz del proyecto y en `security_gateway/`, y completar los valores:

```bash
cp .env.example .env
```

### 2. Levantar la base de datos

```bash
docker compose up -d
docker compose logs db   # verificar que el init.sql corrió sin errores
```

Verificar las tablas creadas:

```bash
docker exec -it apiguardian_db psql -U postgres -d api_guardian -c "\dt"
```

### 3. Levantar la API

```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API: `http://localhost:8000/`
- Documentación interactiva (Swagger): `http://localhost:8000/docs`

### 4. Generar tráfico de prueba

```bash
cd traffic_simulator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 normal_traffic.py --num-users 10 --duration 60 --rpm 30
```

Los ataques (`attack_simulator.py`) se prueban actualmente desde la consola interactiva de Python, importando las funciones `brute_force_attack`, `scraping_attack` y `endpoint_fuzzing_attack`.

### 5. Entrenar el modelo y detectar anomalías

```bash
cd security_gateway
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 -m app.detection.train_model   # entrena y guarda el modelo en model.pkl
python3 -m app.detection.detect        # aplica el modelo y genera alertas nuevas
```

## Estructura del repositorio

```
api-guardian/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── database/
│   └── init.sql
├── api/
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── core/
│       │   └── security.py
│       ├── schemas/
│       │   └── user.py
│       ├── db/
│       │   └── database.py
│       └── models/
│           ├── alert_log.py
│           ├── alert.py
│           ├── associations.py
│           ├── request_log.py
│           ├── role.py
│           └── user.py
├── traffic_simulator/
│   ├── normal_traffic.py
│   └── attack_simulator.py
└── security_gateway/
    ├── requirements.txt
    └── app/
        ├── db/
        │   └── database.py
        └── detection/
            ├── extraction.py
            ├── classification.py
            ├── train_model.py
            ├── detect.py
            └── model.pkl
```