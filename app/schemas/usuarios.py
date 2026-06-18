from pydantic import BaseModel, EmailStr
from typing import Optional

# ==========================================
# SCHEMAS DE USUARIO
# ==========================================


class UsuarioBase(BaseModel):
    correo: EmailStr  # Valida que sea un formato de correo real
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioOut(UsuarioBase):
    id: int

    class Config:
        from_attributes = True
