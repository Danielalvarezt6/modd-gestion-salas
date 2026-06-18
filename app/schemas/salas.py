from pydantic import BaseModel, EmailStr
from datetime import date, time
from typing import Optional, List


# ==========================================
# SCHEMAS PARA SALA
# ==========================================
class SalaBase(BaseModel):
    numero_sala: int
    capacidad: int


class SalaOut(SalaBase):
    class Config:
        from_attributes = True


# ==========================================
# SCHEMAS PARA REQUERIMIENTOS
# ==========================================
class RequerimientosBase(BaseModel):
    acomodo: Optional[str] = None
    equipo_de_sonido: Optional[bool] = False
    cafeteria: Optional[bool] = False
    videoconferencia: Optional[bool] = False


class RequerimientosCreate(RequerimientosBase):
    pass  # No necesitamos campos extra para crear


class RequerimientosOut(RequerimientosBase):
    id_requerimientos: int

    class Config:
        from_attributes = True


# ==========================================
# SCHEMAS PARA SOLICITANTE
# ==========================================
class SolicitanteBase(BaseModel):
    nombre: str
    apellido: str
    correo: EmailStr  # Valida automáticamente que lleve '@' y '.com'
    no_de_telefono: Optional[str] = None


class SolicitanteCreate(SolicitanteBase):
    pass


class SolicitanteOut(SolicitanteBase):
    id_solicitante: int

    class Config:
        from_attributes = True


# ==========================================
# SCHEMAS PARA SOLICITUD
# ==========================================
class SolicitudBase(BaseModel):
    fecha_solicitud: date
    hora_de_solicitud: time
    id_solicitante: Optional[int] = None


class SolicitudCreate(SolicitudBase):
    pass


class SolicitudOut(SolicitudBase):
    id_solicitud: int

    # Opcional: Si quieres que al consultar una solicitud te traiga
    # los datos del solicitante anidados en el JSON:
    solicitante: Optional[SolicitanteOut] = None

    class Config:
        from_attributes = True


# ==========================================
# SCHEMAS PARA EVENTO
# ==========================================
class EventoBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    fecha: date
    hora_de_inicio: time
    hora_de_termino: time
    no_de_asistentes: Optional[int] = None


class EventoCreate(EventoBase):
    id_solicitud: Optional[int] = None
    id_requerimientos: Optional[int] = None
    # Cuando el frontend envíe el formulario, mandará un arreglo de salas ej: [101, 102]
    salas_ids: Optional[List[int]] = []


class EventoOut(EventoBase):
    id_evento: int
    id_solicitud: Optional[int] = None
    id_requerimientos: Optional[int] = None

    # Anidamos los schemas "Out" para que al pedir un evento,
    # FastAPI traiga toda la info útil de golpe:
    salas: List[SalaOut] = []
    requerimientos: Optional[RequerimientosOut] = None

    class Config:
        from_attributes = True
