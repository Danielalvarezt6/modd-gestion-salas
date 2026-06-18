from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings
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
