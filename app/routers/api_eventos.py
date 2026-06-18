from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select  # <-- Importar select
from typing import List

from app.core.database import get_db
from app.models.salas import Evento, Sala
from app.schemas.salas import EventoOut, EventoCreate, EventoUpdate

router = APIRouter(prefix="/api/eventos", tags=["Eventos"])


def validar_horario_evento(evento: EventoCreate | EventoUpdate, db: Session, id_ignorado: int | None = None) -> List[Sala]:
    if evento.hora_de_inicio >= evento.hora_de_termino:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La hora de termino debe ser posterior a la hora de inicio.",
        )

    salas_ids = evento.salas_ids or []
    if not salas_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selecciona al menos una sala.",
        )

    salas_asignadas = db.execute(
        select(Sala).where(Sala.numero_sala.in_(salas_ids))
    ).scalars().all()

    if len(salas_asignadas) != len(set(salas_ids)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Una o más salas especificadas no existen.",
        )

    if evento.estado_evento == "cancelado":
        return salas_asignadas

    eventos_mismo_dia = db.execute(
        select(Evento).where(Evento.fecha == evento.fecha)
    ).scalars().all()

    for existente in eventos_mismo_dia:
        if id_ignorado is not None and existente.id_evento == id_ignorado:
            continue
        if existente.estado_evento == "cancelado":
            continue
        if not any(sala.numero_sala in salas_ids for sala in existente.salas):
            continue
        if evento.hora_de_inicio < existente.hora_de_termino and evento.hora_de_termino > existente.hora_de_inicio:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede guardar: el evento se solapa con otro en la misma sala y horario.",
            )

    return salas_asignadas


@router.get("/", response_model=List[EventoOut])
async def obtener_eventos(db: Session = Depends(get_db)):
    eventos = db.execute(select(Evento)).scalars().all()
    return eventos


@router.get("/{id_evento}", response_model=EventoOut)
async def obtener_evento(id_evento: int, db: Session = Depends(get_db)):
    evento = db.get(Evento, id_evento)
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El evento especificado no existe.",
        )
    return evento


@router.post("/", response_model=EventoOut, status_code=status.HTTP_201_CREATED)
async def crear_evento(evento: EventoCreate, db: Session = Depends(get_db)):
    validar_horario_evento(evento, db)
    nuevo_evento = Evento(
        titulo=evento.titulo,
        descripcion=evento.descripcion,
        fecha=evento.fecha,
        hora_de_inicio=evento.hora_de_inicio,
        hora_de_termino=evento.hora_de_termino,
        no_de_asistentes=evento.no_de_asistentes,
        tipo=evento.tipo,
        estado_evento=evento.estado_evento,
        id_solicitud=evento.id_solicitud,
        id_requerimientos=evento.id_requerimientos,
    )

    if evento.salas_ids:
        stmt = select(Sala).where(Sala.numero_sala.in_(evento.salas_ids))
        salas_asignadas = db.execute(stmt).scalars().all()

        if len(salas_asignadas) != len(evento.salas_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Una o más salas especificadas no existen.",
            )

        nuevo_evento.salas = salas_asignadas

    db.add(nuevo_evento)
    db.commit()
    db.refresh(nuevo_evento)
    return nuevo_evento


@router.put("/{id_evento}", response_model=EventoOut)
async def actualizar_evento(id_evento: int, evento: EventoUpdate, db: Session = Depends(get_db)):
    evento_db = db.get(Evento, id_evento)

    if not evento_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El evento especificado no existe.",
        )

    validar_horario_evento(evento, db, id_ignorado=id_evento)

    evento_db.titulo = evento.titulo
    evento_db.descripcion = evento.descripcion
    evento_db.fecha = evento.fecha
    evento_db.hora_de_inicio = evento.hora_de_inicio
    evento_db.hora_de_termino = evento.hora_de_termino
    evento_db.no_de_asistentes = evento.no_de_asistentes
    evento_db.tipo = evento.tipo
    evento_db.estado_evento = evento.estado_evento
    evento_db.id_solicitud = evento.id_solicitud
    evento_db.id_requerimientos = evento.id_requerimientos

    if evento.salas_ids is not None:
        stmt = select(Sala).where(Sala.numero_sala.in_(evento.salas_ids))
        salas_asignadas = db.execute(stmt).scalars().all()

        if len(salas_asignadas) != len(evento.salas_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Una o más salas especificadas no existen.",
            )

        evento_db.salas = salas_asignadas

    db.commit()
    db.refresh(evento_db)
    return evento_db


@router.delete("/{id_evento}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_evento(id_evento: int, db: Session = Depends(get_db)):
    evento = db.get(Evento, id_evento)

    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El evento especificado no existe.",
        )

    db.delete(evento)
    db.commit()
