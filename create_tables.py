from app.db import engine, Base
from app.models import Trend

Base.metadata.create_all(bind=engine)
print("Tablas creadas correctamente.")
