import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()  # Lee .env desde la raíz del proyecto

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definido en el archivo .env")

# Motor SQLAlchemy (singleton)
engine = create_engine(
    DATABASE_URL,
    future=True,
    echo=False,
    pool_pre_ping=True
)

# Alias para compatibilidad
_engine = engine

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)

Base = declarative_base()


def get_session():
    """Retorna una sesión de SQLAlchemy."""
    return SessionLocal()


def get_db():
    """Generador de sesión para usar en rutas con contexto."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
