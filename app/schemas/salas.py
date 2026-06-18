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
    correo: EmailStr  # Valida automaticamente que lleve '@' y '.com'
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
    estado: Optional[str] = "pendiente"
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


class SolicitudResumenOut(BaseModel):
    id_solicitud: int
    estado: Optional[str] = "pendiente"
    fecha_solicitud: date
    hora_de_solicitud: time
    solicitante_nombre: str
    solicitante_correo: str
    evento_titulo: Optional[str] = None
    evento_fecha: Optional[date] = None
    evento_inicio: Optional[time] = None
    evento_fin: Optional[time] = None
    evento_asistentes: Optional[int] = None
    acomodo: Optional[str] = None
    equipo_de_sonido: Optional[bool] = False
    cafeteria: Optional[bool] = False
    videoconferencia: Optional[bool] = False
    salas: List[SalaOut] = []


class SolicitudEstadoUpdate(BaseModel):
    estado: str


class SolicitudEventoCreate(BaseModel):
    solicitante_nombre: str
    solicitante_apellido: str
    solicitante_correo: EmailStr
    solicitante_telefono: Optional[str] = None
    evento_titulo: str
    evento_descripcion: Optional[str] = None
    evento_fecha: date
    evento_inicio: time
    evento_fin: time
    evento_asistentes: Optional[int] = 0
    sala_id: int
    acomodo: Optional[str] = None
    equipo_de_sonido: Optional[bool] = False
    cafeteria: Optional[bool] = False
    videoconferencia: Optional[bool] = False


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
    # Cuando el frontend envie el formulario, mandara un arreglo de salas ej: [101, 102]
    salas_ids: Optional[List[int]] = []


class EventoUpdate(EventoCreate):
    pass


class EventoOut(EventoBase):
    id_evento: int
    id_solicitud: Optional[int] = None
    id_requerimientos: Optional[int] = None

    # Anidamos los schemas "Out" para que al pedir un evento,
    # FastAPI traiga toda la info util de golpe:
    salas: List[SalaOut] = []
    requerimientos: Optional[RequerimientosOut] = None
    solicitud: Optional[SolicitudOut] = None

    class Config:
        from_attributes = True


class ReporteResumenOut(BaseModel):
    total_eventos: int
    total_asistentes: int
    uso_por_sala: List[dict]
    eventos: List[EventoOut]

