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
* Machine Learning: scikit-learn (Isolation Forest) *(próximamente)*
* Orquestación: Docker + Docker Compose

## Arquitectura (visión general)

El proyecto está pensado en componentes separados:

1. **`target_api/`** — una API REST "objetivo" (login, usuarios, recursos) que sirve como banco de pruebas.
2. **`security_gateway/`** — middleware que intercepta cada request, lo loguea y lo evalúa contra el modelo de detección. *(pendiente)*
3. **`traffic_simulator/`** — scripts que generan tráfico normal y tráfico de ataque simulado para entrenar y probar el sistema. *(pendiente)*
4. **`dashboard/`** — panel donde se visualizan las alertas generadas. *(pendiente)*

## Modelo de datos

El diseño contempla 6 tablas:

- `users` — usuarios del sistema.
- `roles` / `user_roles` — roles y su asignación many-to-many a usuarios.
- `request_logs` — registro de cada request recibido por la API (IP, método, endpoint, query params, payload, status code, tiempo de respuesta, usuario si está autenticado).
- `alerts` — alertas generadas a partir de patrones sospechosos detectados (tipo, score de anomalía, ventana temporal del patrón, estado de revisión).
- `alert_logs` — tabla intermedia que vincula cada alerta con los `request_logs` puntuales que la originaron.

Tipos de alerta contemplados: `bruteforce`, `idor`, `scraping`, `rate_limit_abuse`, `sql_injection_attempt`, `endpoint_fuzzing`.

El schema completo (DDL) vive en [`database/init.sql`](./database/init.sql) y se aplica automáticamente al levantar el contenedor de PostgreSQL.

## Estado actual del proyecto

- [x] Diseño del DER y modelado de relaciones (incluye tabla intermedia many-to-many y relación 1 a muchos vía tabla puente)
- [x] `init.sql` con constraints (`NOT NULL`, `CHECK`, `UNIQUE`, `DEFAULT`), índices y foreign keys
- [x] PostgreSQL corriendo en Docker, con credenciales gestionadas por `.env`
- [x] Estructura inicial de `api/` con FastAPI
- [x] Modelos SQLAlchemy de las 6 tablas (`User`, `Role`, `user_roles`, `RequestLog`, `Alert`, `AlertLog`)
- [ ] Conexión verificada entre FastAPI y PostgreSQL (engine/session probados)
- [ ] Endpoints de autenticación (registro, login con JWT)
- [ ] Endpoints de recursos de la API objetivo
- [ ] Middleware de logging de requests (`security_gateway`)
- [ ] Simulador de tráfico normal y de ataques
- [ ] Extracción de features y entrenamiento del modelo de detección (Isolation Forest)
- [ ] Dashboard de alertas

## Cómo levantar el entorno (hasta ahora)

### 1. Variables de entorno

Copiar `.env.example` a `.env` y completar los valores:

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

### 3. Levantar la API objetivo (en desarrollo)

```bash
cd target_api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API: `http://localhost:8000/`
- Documentación interactiva (Swagger): `http://localhost:8000/docs`

## Estructura del repositorio

```
api-guardian/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── database/
│   └── init.sql
└── api/
    ├── requirements.txt
    └── app/
        ├── main.py
        ├── db/
        │   └── database.py
        └── models/
            ├── alert_log.py
            ├── alert.py
            ├── associations.py
            ├── request_log.py
            ├── role.py
            └── user.py
```

## Contexto del proyecto

Este proyecto nace como continuación de un portfolio enfocado en bases de datos y backend, sumando un enfoque nuevo: seguridad de aplicaciones web y una introducción práctica a Machine Learning aplicado a detección de anomalías, usando tecnologías modernas y con alta demanda (FastAPI, APIs security, ML no supervisado).

---

*Proyecto en desarrollo activo — este README se irá actualizando a medida que avancen las fases.*