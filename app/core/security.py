from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request, status
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.usuarios import Usuario
import bcrypt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara la contraseña que el usuario escribe en el login con el hash encriptado que está guardado en PostgreSQL.
    """
    return bcrypt.checkpw(
        bytes(plain_password, encoding="utf-8"),
        bytes(hashed_password, encoding="utf-8"),
    )


def get_password_hash(password: str) -> str:
    """
    Toma una contraseña y la convierte en un hash irreversible.
    Esto se usará cuando se creen nuevos usuarios administradores.
    """
    return bcrypt.hashpw(
        bytes(password, encoding="utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Genera un token JWT firmado con la SECRET_KEY del archivo de entorno.
    """

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def _token_from_cookie(request: Request) -> str | None:
    raw_token = request.cookies.get("access_token")
    if not raw_token:
        return None
    return raw_token.replace("Bearer ", "", 1)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Usuario:
    token = _token_from_cookie(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        correo = payload.get("sub")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesion invalida") from exc

    if not correo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesion invalida")

    usuario = db.query(Usuario).filter(Usuario.correo == correo).first()
    if not usuario or not usuario.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesion invalida")

    return usuario


def require_authenticated_page(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    return current_user
