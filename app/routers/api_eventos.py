from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select  # <-- Importar select
from typing import List

from app.core.database import get_db
from app.models.salas import Evento, Sala
from app.schemas.salas import EventoOut, EventoCreate

router = APIRouter(prefix="/api/eventos", tags=["Eventos"])


@router.get("/", response_model=List[EventoOut])
async def obtener_eventos(db: Session = Depends(get_db)):
    eventos = db.execute(select(Evento)).scalars().all()
    return eventos


@router.post("/", response_model=EventoOut, status_code=status.HTTP_21_CREATED)
async def crear_evento(evento: EventoCreate, db: Session = Depends(get_db)):
    nuevo_evento = Evento(
        titulo=evento.titulo,
        descripcion=evento.descripcion,
        fecha=evento.fecha,
        hora_de_inicio=evento.hora_de_inicio,
        hora_de_termino=evento.hora_de_termino,
        no_de_asistentes=evento.no_de_asistentes,
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
