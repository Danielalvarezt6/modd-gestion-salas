from app.core.database import SessionLocal
from app.models.usuarios import Usuario
from app.core.security import get_password_hash

def seed_admin():
    # Se abre una conexión a la base de datos
    db = SessionLocal()

    try:
        # Verificamos si el usuario ya existe para no duplicarlo
        usuario_existente = db.query(Usuario).filter(Usuario.correo=="admin@unison.mx").first

        if not usuario_existente:
            print("Creando usuario administrador...")
            nuevo_admin = Usuario(
                correo="admin@unison.mx",
                hashed_password=get_password_hash("modd2026"),
                is_active=True,
                is_admin=True
            )
            db.add(nuevo_admin)
            db.commit()
            print("Administrador creado con exito")

        else:
            print("El administrador ya existe en la base de datos.")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
