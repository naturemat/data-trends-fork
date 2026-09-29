# Configuracion de gunicorn para produccion.
# La usa deploy/scraper.service a traves de: gunicorn wsgi:app -c gunicorn.conf.py

# Puerto 5000. Dejarlo en 0.0.0.0 mantiene el comportamiento actual, donde el
# servicio se expone directamente. Si se pone nginx delante (ver
# deploy/nginx.conf), conviene cambiar esto a 127.0.0.1:5000 para que la
# aplicacion deje de ser alcanzable desde Internet.
bind = "0.0.0.0:5000"

# Los endpoints de IA (/api/ai_summary, /api/metrics/ai_classification) hacen
# llamadas bloqueantes a Groq que pueden tardar mas de un minuto. Con workers
# sincronicos unas pocas peticiones de IA alcanzan para bloquear todo el
# dashboard, por eso se usan hilos.
workers = 3
threads = 4
worker_class = "gthread"

# Margen para las llamadas a Groq, que es la peticion mas lenta que hay.
timeout = 120

accesslog = "-"
errorlog = "-"
loglevel = "info"

# Reinicio de workers si se acumulan peticiones
max_requests = 1000
max_requests_jitter = 100
