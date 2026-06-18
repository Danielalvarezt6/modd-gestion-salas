from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.salas import Evento, Requerimientos, Sala, Solicitante, Solicitud
from app.schemas.salas import SolicitudEstadoUpdate, SolicitudEventoCreate, SolicitudResumenOut

router = APIRouter(prefix="/api/solicitudes", tags=["Solicitudes"])


def _solicitud_resumen(solicitud: Solicitud) -> SolicitudResumenOut:
    evento = solicitud.eventos[0] if solicitud.eventos else None
    solicitante = solicitud.solicitante
    return SolicitudResumenOut(
        id_solicitud=solicitud.id_solicitud,
        estado=solicitud.estado or "pendiente",
        fecha_solicitud=solicitud.fecha_solicitud,
        hora_de_solicitud=solicitud.hora_de_solicitud,
        solicitante_nombre=f"{solicitante.nombre} {solicitante.apellido}" if solicitante else "Sin solicitante",
        solicitante_correo=solicitante.correo if solicitante else "",
        institucion=solicitante.institucion if solicitante else "",
        evento_titulo=evento.titulo if evento else "Sin evento",
        evento_fecha=evento.fecha if evento else None,
        evento_inicio=evento.hora_de_inicio if evento else None,
        evento_fin=evento.hora_de_termino if evento else None,
        evento_asistentes=evento.no_de_asistentes if evento else None,
        evento_tipo=evento.tipo if evento else None,
        salas=evento.salas if evento else [],
    )


def _validar_solape_evento(payload: SolicitudEventoCreate, db: Session):
    if payload.evento_inicio >= payload.evento_fin:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La hora de fin debe ser posterior a la hora de inicio.",
        )

    sala = db.get(Sala, payload.sala_id)
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La sala seleccionada no existe.",
        )

    eventos_mismo_dia = db.execute(
        select(Evento).where(Evento.fecha == payload.evento_fecha)
    ).scalars().all()
    for evento in eventos_mismo_dia:
        if evento.estado_evento == "cancelado":
            continue
        if not any(item.numero_sala == payload.sala_id for item in evento.salas):
            continue
        if payload.evento_inicio < evento.hora_de_termino and payload.evento_fin > evento.hora_de_inicio:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede crear la solicitud: el evento se solapa con otro en la misma sala y horario.",
            )

    return sala


@router.get("/", response_model=List[SolicitudResumenOut])
async def obtener_solicitudes(db: Session = Depends(get_db)):
    solicitudes = db.execute(
        select(Solicitud)
        .options(
            selectinload(Solicitud.solicitante),
            selectinload(Solicitud.eventos).selectinload(Evento.salas),
        )
        .order_by(Solicitud.fecha_solicitud.desc(), Solicitud.hora_de_solicitud.desc())
    ).scalars().all()

    return [_solicitud_resumen(solicitud) for solicitud in solicitudes]


@router.post("/", response_model=SolicitudResumenOut, status_code=status.HTTP_201_CREATED)
async def crear_solicitud(payload: SolicitudEventoCreate, db: Session = Depends(get_db)):
    sala = _validar_solape_evento(payload, db)
    solicitante = db.query(Solicitante).filter(Solicitante.correo == payload.solicitante_correo).first()
    if not solicitante:
        solicitante = Solicitante(correo=payload.solicitante_correo)
        db.add(solicitante)

    solicitante.nombre = payload.solicitante_nombre
    solicitante.apellido = payload.solicitante_apellido
    solicitante.no_de_telefono = payload.solicitante_telefono
    solicitante.institucion = payload.institucion

    solicitud = Solicitud(
        fecha_solicitud=date.today(),
        hora_de_solicitud=datetime.now().time().replace(microsecond=0),
        estado="pendiente",
        solicitante=solicitante,
    )
    requerimientos = Requerimientos(
        acomodo=payload.acomodo,
        equipo_de_sonido=payload.equipo_de_sonido,
        cafeteria=payload.cafeteria,
        videoconferencia=payload.videoconferencia,
    )
    evento = Evento(
        titulo=payload.evento_titulo,
        descripcion=payload.evento_descripcion,
        fecha=payload.evento_fecha,
        hora_de_inicio=payload.evento_inicio,
        hora_de_termino=payload.evento_fin,
        no_de_asistentes=payload.evento_asistentes,
        tipo=payload.evento_tipo,
        estado_evento="pendiente",
        solicitud=solicitud,
        requerimientos=requerimientos,
        salas=[sala],
    )
    db.add(evento)
    db.flush()
    solicitud_id = solicitud.id_solicitud
    db.commit()

    solicitud = db.execute(
        select(Solicitud)
        .where(Solicitud.id_solicitud == solicitud_id)
        .options(
            selectinload(Solicitud.solicitante),
            selectinload(Solicitud.eventos).selectinload(Evento.salas),
        )
    ).scalars().one()
    return _solicitud_resumen(solicitud)


@router.patch("/{id_solicitud}/estado", response_model=SolicitudResumenOut)
async def actualizar_estado_solicitud(
    id_solicitud: int,
    payload: SolicitudEstadoUpdate,
    db: Session = Depends(get_db),
):
    estados_validos = {"pendiente", "aprobada", "rechazada", "cancelada"}
    if payload.estado not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Estado de solicitud no valido.",
        )

    solicitud = db.get(Solicitud, id_solicitud)
    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La solicitud especificada no existe.",
        )

    solicitud.estado = payload.estado
    db.commit()

    solicitud = db.execute(
        select(Solicitud)
        .where(Solicitud.id_solicitud == id_solicitud)
        .options(
            selectinload(Solicitud.solicitante),
            selectinload(Solicitud.eventos).selectinload(Evento.salas),
        )
    ).scalars().one()
    evento = solicitud.eventos[0] if solicitud.eventos else None
    solicitante = solicitud.solicitante

    return SolicitudResumenOut(
        id_solicitud=solicitud.id_solicitud,
        estado=solicitud.estado or "pendiente",
        fecha_solicitud=solicitud.fecha_solicitud,
        hora_de_solicitud=solicitud.hora_de_solicitud,
        solicitante_nombre=f"{solicitante.nombre} {solicitante.apellido}" if solicitante else "Sin solicitante",
        solicitante_correo=solicitante.correo if solicitante else "",
        institucion=solicitante.institucion if solicitante else "",
        evento_titulo=evento.titulo if evento else "Sin evento",
        evento_fecha=evento.fecha if evento else None,
        evento_inicio=evento.hora_de_inicio if evento else None,
        evento_fin=evento.hora_de_termino if evento else None,
        evento_asistentes=evento.no_de_asistentes if evento else None,
        evento_tipo=evento.tipo if evento else None,
        salas=evento.salas if evento else [],
    )
