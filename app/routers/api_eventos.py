from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select  # <-- Importar select
from typing import List

from app.core.database import get_db
from app.models.salas import Evento, Sala, Solicitud
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

    eventos_mismo_dia = db.execute(
        select(Evento)
        .outerjoin(Solicitud)
        .where(Evento.fecha == evento.fecha)
        .where((Solicitud.estado.is_(None)) | (Solicitud.estado != "rechazada"))
    ).scalars().all()

    salas_ocupadas = set()
    salas_en_conflicto = set()
    for existente in eventos_mismo_dia:
        if id_ignorado is not None and existente.id_evento == id_ignorado:
            continue
        if evento.hora_de_inicio < existente.hora_de_termino and evento.hora_de_termino > existente.hora_de_inicio:
            for sala in existente.salas:
                salas_ocupadas.add(sala.numero_sala)
                if sala.numero_sala in salas_ids:
                    salas_en_conflicto.add(sala.numero_sala)

    if salas_en_conflicto:
        todas_las_salas = db.execute(select(Sala).order_by(Sala.numero_sala)).scalars().all()
        salas_disponibles = [
            f"Sala {sala.numero_sala}"
            for sala in todas_las_salas
            if sala.numero_sala not in salas_ocupadas
        ]
        sugerencia = (
            f" Puedes usar {', '.join(salas_disponibles)} en ese horario."
            if salas_disponibles
            else " No hay otra sala disponible en ese bloque."
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede guardar: el evento se solapa con otro en la misma sala y horario.{sugerencia}",
        )

    return salas_asignadas


@router.get("/", response_model=List[EventoOut])
async def obtener_eventos(solo_aprobadas: bool = False, db: Session = Depends(get_db)):
    stmt = select(Evento).options(
        selectinload(Evento.salas),
        selectinload(Evento.requerimientos),
        selectinload(Evento.solicitud).selectinload(Solicitud.solicitante),
    )
    if solo_aprobadas:
        stmt = stmt.join(Solicitud).where(Solicitud.estado == "aprobada")

    eventos = db.execute(stmt.order_by(Evento.fecha, Evento.hora_de_inicio)).scalars().all()
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
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="No se pueden crear eventos directamente. Primero registra una solicitud y apruebala."
    )


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
    if evento.id_solicitud is not None:
        evento_db.id_solicitud = evento.id_solicitud
    if evento.id_requerimientos is not None:
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
    evento = db.execute(
        select(Evento)
        .where(Evento.id_evento == id_evento)
        .options(
            selectinload(Evento.salas),
            selectinload(Evento.requerimientos),
            selectinload(Evento.solicitud).selectinload(Solicitud.solicitante),
        )
    ).scalars().first()

    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El evento especificado no existe.",
        )

    solicitud = evento.solicitud
    solicitante = solicitud.solicitante if solicitud else None
    requerimientos = evento.requerimientos
    evento.salas.clear()
    db.delete(evento)
    if requerimientos:
        db.delete(requerimientos)
    if solicitud:
        db.delete(solicitud)
    if solicitante and len(solicitante.solicitudes) <= 1:
        db.delete(solicitante)
    db.commit()
