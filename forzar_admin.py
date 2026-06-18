from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.usuarios import Usuario
from app.core.security import get_password_hash

# Aquí pondremos la URL directa, sin leer el archivo .env
# IMPORTANTE: Reemplaza 'TU_USUARIO' y 'TU_CONTRASEÑA' por la contraseña real que usas en PostgreSQL
DATABASE_URL = "postgresql://TU_USUARIO:TU_CONTRASEÑA@localhost:5432/modd_db"

def inyectar_usuario():
    print("Conectando directamente a PostgreSQL...")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        nuevo_admin = Usuario(
            correo="admin@unison.mx",
            hashed_password=get_password_hash("modd2026"),
            is_active=True,
            is_admin=True
        )
        db.add(nuevo_admin)
        db.commit()
        print("¡ÉXITO! Administrador inyectado en la base de datos real.")
    except Exception as e:
        print(f"Error al inyectar: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    inyectar_usuario()
