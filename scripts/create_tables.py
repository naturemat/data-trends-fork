from app.db import _engine, Base

Base.metadata.create_all(bind=_engine)
print("Tablas creadas correctamente.")
