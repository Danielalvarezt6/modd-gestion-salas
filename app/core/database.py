from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Crear el Engine (El traductor que usa psycopg2 para hablar con Postgres)
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Configurar la fábrica de sesiones (SessionLocal)
# autocommit=False y autoflush=False para tener control manual de las transacciones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declaraiva (De aquí se heredan los modelos, como Sala, Evento, etc.)
Base = declarative_base()

# Inyección de Dependencias
# Esta función se usa en los routers para abrir y cerrar conexiones automáticamente.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
