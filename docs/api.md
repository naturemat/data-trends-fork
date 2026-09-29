# Documentacion de la API

Base del servicio: la misma que sirve el frontend. Todas las rutas estan
registradas en el blueprint `routes_blueprint` de `app/routes.py`.

## Convenciones

- Todas las metricas aceptan los mismos parametros de filtro:
  - `pais`: codigo del pais (`worldwide`, `ecuador`, `argentina`, ...) o `all`. Por defecto `worldwide`.
  - `date_from` / `date_to`: rango en formato `YYYY-MM-DD`. Si se omiten, el
    servicio usa el dia de la ultima captura disponible.
  - `granularity`: `hour` o `day`. Por defecto `hour`.
- El backend trabaja en hora de Ecuador (UTC-5) y convierte a UTC antes de
  consultar Mongo. Los rangos sin zona horaria se interpretan como hora local
  de Ecuador.
- Los errores de metricas devuelven `{"error": "..."}` con codigo 400; los de
  los endpoints con IA devuelven 500.

## Frontend

### GET /
Renderiza `frontend/index.html`.

### GET /api/config
Configuracion publica para el frontend.

```json
{ "api_base": "http://3.151.181.99:5000" }
```

## Metadata

### GET /api/last_update
Fecha de la ultima captura almacenada.

```json
{ "last_update": "2026-02-20T21:45:00Z" }
```

## Metricas

### GET /api/metrics/summary
Totales para las tarjetas del dashboard.

```json
{ "total_unique": 120, "total_global": 15, "total_paises": 20 }
```

### GET /api/metrics/activity
Tendencia total por intervalo: cuantas tendencias habia y cuantas eran nuevas.

```json
{ "data": [ { "timestamp": "2026-02-20T15:00:00-05:00",
              "total_trends_in_period": 30,
              "new_trends": 12 } ] }
```

### GET /api/metrics/persistence
Top de tendencias mas persistentes. `appearances` es la cantidad de intervalos
de tiempo distintos en los que aparecio.

```json
{ "data": [ { "trend": "#Final", "appearances": 18,
              "time_units_active": 18,
              "countries": ["worldwide", "argentina"],
              "raw_time_units": ["2026-02-20T15:00:00-05:00"] } ] }
```

### GET /api/metrics/spread
Alcance geografico. `global` si esta en `worldwide` o aparece en 10 o mas
paises, `regional` si aparece en 3 o mas ubicaciones, `local` en el resto.

```json
{ "data": [ { "trend": "#Final", "scope": "global",
              "countries": ["argentina", "peru"], "countries_count": 2,
              "in_worldwide": true, "appearances": 40 } ] }
```

### GET /api/metrics/survival
Distribucion de las tendencias segun quantas horas sobreviven. Las
etiquetas cambian segun el rango pedido: si abarca 2 dias o menos son
`Fugaz (<3h)`, `Activa (3-8h)`, `Persistente (9-23h)`, `Inmortal (>=24h)`; si
abarca mas, `Efimera (<1d)`, `Estable (1-2d)`, `Semanal (3-6d)`,
`Historica (>=7d)`.

```json
{ "data": [ { "label": "Persistente (9-23h)", "count": 7,
              "topTrends": ["#Final", "#Mundial"] } ] }
```

## IA (Groq, modelo llama-3.3-70b-versatile)

Ambos endpoints usan el SDK de OpenAI apuntando a la API de Groq y necesitan
`GROQCLOUD_API_KEY` y `GROQCLOUD_API_KEY_ALT` en el entorno. Si falta la llave
el endpoint responde 500 con un mensaje explicito, y el resto de la aplicacion
sigue funcionando.

### POST /api/ai_summary
Redacta un analisis en texto plano de 200 a 300 palabras a partir de las
tendencias mas persistentes.

```json
{ "data": [ { "trend": "#Final", "appearances": 18 } ],
  "pais_nombre": "Argentina" }
```

Respuesta:

```json
{ "summary": "1. EL TEMA EN ARGENTINA: ..." }
```

### GET /api/metrics/ai_classification
Clasifica el top 50 de tendencias persistentes en seis categorias fijas:
`Politica y gobierno`, `Deportes`, `Entretenimiento`, `Tecnologia`, `Economia`,
`Otros`. Devuelve directamente el objeto que devuelve el modelo.

```json
{ "Deportes": ["#Final", "#Mundial"], "Tecnologia": ["iPhone15"] }
```

## Notas

- Los datos crudos de tendencias quedan en la coleccion `trends` de MongoDB.
- La busqueda semantica con embeddings se elimino del proyecto; los endpoints
  `/api/embeddings/*` ya no existen. La unica IA activa es la de resumen y
  clasificacion descrita arriba.
