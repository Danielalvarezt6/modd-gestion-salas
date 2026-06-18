from fastapi import APIRouter, Depends, HTTPException, status, Response, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.usuarios import Usuario
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/login")
async def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),  # Se inyecta la sesión de la base de datos
):
    """
    Procesa el login, validando contra la base de datos. inyecta la cookie JWT y devuelve JSON si es exitoso.
    """

    # Se busca al usuario en la base de datos por medio de su correo.
    usuario = db.query(Usuario).filter(Usuario.correo == email).first()

    print(f"Correo recibido: '{email}'")
    print(f"Contraseña recibida: '{password}'")
    print(f"¿Encontró usuario?: {usuario is not None}")
    print(f"URL de la BD en FastAPI: {db.get_bind().url}")

    # Verificamos si el usuario existe y si es la contraseña correcta.
    if not usuario or not verify_password(password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas"
        )

    if not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta de usuario está desactivada",
        )

    # Crear el token JWT real
    # Guardamos el correo y añadimos el rol para usarlo después en permisos
    access_token = create_access_token(
        data={"sub": usuario.correo, "rol": "admin" if usuario.is_admin else "usuario"}
    )

    # Configurar la cookie segura
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
    )

    # Devolvemos JSON puro para que el JS del frontend decia qué hacer
    return {
        "message": "Autenticación exitosa",
        "user": usuario.correo,
        "redirect": "/dashboard",
    }
