from datetime import date, datetime, time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.salas import Evento, Requerimientos, Sala, Solicitante, Solicitud
from app.schemas.salas import SolicitudEstadoUpdate, SolicitudEventoCreate, SolicitudResumenOut

router = APIRouter(prefix="/api/solicitudes", tags=["Solicitudes"])
CAPACIDAD_MAXIMA_POR_SALA = 40
HORA_APERTURA = time(8, 0)
HORA_CIERRE = time(20, 0)


def _solicitud_resumen(solicitud: Solicitud) -> SolicitudResumenOut:
    evento = solicitud.eventos[0] if solicitud.eventos else None
    solicitante = solicitud.solicitante
    requerimientos = evento.requerimientos if evento else None
    return SolicitudResumenOut(
        id_solicitud=solicitud.id_solicitud,
        estado=solicitud.estado or "pendiente",
        fecha_solicitud=solicitud.fecha_solicitud,
        hora_de_solicitud=solicitud.hora_de_solicitud,
        solicitante_nombre=f"{solicitante.nombre} {solicitante.apellido}" if solicitante else "Sin solicitante",
        solicitante_apellido=solicitante.apellido if solicitante else None,
        solicitante_correo=solicitante.correo if solicitante else "",
        solicitante_telefono=solicitante.no_de_telefono if solicitante else None,
        evento_titulo=evento.titulo if evento else "Sin evento",
        evento_descripcion=evento.descripcion if evento else None,
        evento_fecha=evento.fecha if evento else None,
        evento_inicio=evento.hora_de_inicio if evento else None,
        evento_fin=evento.hora_de_termino if evento else None,
        evento_asistentes=evento.no_de_asistentes if evento else None,
        acomodo=requerimientos.acomodo if requerimientos else None,
        equipo_de_sonido=requerimientos.equipo_de_sonido if requerimientos else False,
        cafeteria=requerimientos.cafeteria if requerimientos else False,
        videoconferencia=requerimientos.videoconferencia if requerimientos else False,
        salas=evento.salas if evento else [],
    )


def _validar_solape_evento(payload: SolicitudEventoCreate, db: Session, id_evento_ignorado: int | None = None):
    if payload.evento_inicio >= payload.evento_fin:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La hora de fin debe ser posterior a la hora de inicio.",
        )
    if payload.evento_inicio < HORA_APERTURA or payload.evento_fin > HORA_CIERRE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El horario permitido es unicamente de 08:00 a 20:00.",
        )
    if payload.evento_inicio.minute != 0 or payload.evento_fin.minute != 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se permiten bloques por hora completa.",
        )

    asistentes = payload.evento_asistentes or 0
    salas_necesarias = max(1, (asistentes + CAPACIDAD_MAXIMA_POR_SALA - 1) // CAPACIDAD_MAXIMA_POR_SALA)

    eventos_mismo_dia = db.execute(
        select(Evento)
        .outerjoin(Solicitud)
        .where(Evento.fecha == payload.evento_fecha)
        .where((Solicitud.estado.is_(None)) | (Solicitud.estado != "rechazada"))
    ).scalars().all()

    salas_ocupadas = set()
    for evento in eventos_mismo_dia:
        if id_evento_ignorado is not None and evento.id_evento == id_evento_ignorado:
            continue
        if payload.evento_inicio < evento.hora_de_termino and payload.evento_fin > evento.hora_de_inicio:
            for item in evento.salas:
                salas_ocupadas.add(item.numero_sala)

    todas_las_salas = db.execute(select(Sala).order_by(Sala.numero_sala)).scalars().all()
    salas_disponibles = [sala for sala in todas_las_salas if sala.numero_sala not in salas_ocupadas]

    salas_ids = payload.salas_ids or []
    
    if salas_ids:
        # Modo Administradora (Manual)
        if len(salas_ids) < salas_necesarias:
            disponibles_str = ", ".join(f"Sala {s.numero_sala}" for s in salas_disponibles)
            sugerencia = f" Quedan disponibles en ese horario: {disponibles_str}." if disponibles_str else " No hay más salas disponibles."
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Para {asistentes} asistentes necesitas al menos {salas_necesarias} salas.{sugerencia}"
            )
            
        salas_asignadas = [sala for sala in todas_las_salas if sala.numero_sala in salas_ids]
        if len(salas_asignadas) != len(set(salas_ids)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Una o mas salas seleccionadas no existen.")
            
        salas_en_conflicto = [sala.numero_sala for sala in salas_asignadas if sala.numero_sala in salas_ocupadas]
        if salas_en_conflicto:
            disponibles_str = ", ".join(f"Sala {s.numero_sala}" for s in salas_disponibles)
            sugerencia = f" Puedes usar {disponibles_str} en ese horario." if disponibles_str else " No hay salas disponibles en ese bloque."
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Las salas solicitadas están ocupadas en ese horario.{sugerencia}"
            )
        return salas_asignadas
    else:
        # Modo Google Forms (Automático)
        if len(salas_disponibles) < salas_necesarias:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Se requieren {salas_necesarias} salas para {asistentes} asistentes, pero solo hay {len(salas_disponibles)} disponibles en ese horario."
            )
        return salas_disponibles[:salas_necesarias]


def _load_solicitud(db: Session, id_solicitud: int) -> Solicitud | None:
    return db.execute(
        select(Solicitud)
        .where(Solicitud.id_solicitud == id_solicitud)
        .options(
            selectinload(Solicitud.solicitante),
            selectinload(Solicitud.eventos).selectinload(Evento.salas),
            selectinload(Solicitud.eventos).selectinload(Evento.requerimientos),
        )
    ).scalars().first()


@router.get("/", response_model=List[SolicitudResumenOut])
async def obtener_solicitudes(db: Session = Depends(get_db)):
    solicitudes = db.execute(
        select(Solicitud)
        .join(Solicitud.eventos)
        .options(
            selectinload(Solicitud.solicitante),
            selectinload(Solicitud.eventos).selectinload(Evento.salas),
            selectinload(Solicitud.eventos).selectinload(Evento.requerimientos),
        )
        .order_by(Solicitud.fecha_solicitud.desc(), Solicitud.hora_de_solicitud.desc())
    ).scalars().all()

    return [_solicitud_resumen(solicitud) for solicitud in solicitudes]


def _delete_solicitud_tree(db: Session, solicitud: Solicitud):
    solicitante = solicitud.solicitante
    requerimientos = []
    for evento in list(solicitud.eventos):
        if evento.requerimientos:
            requerimientos.append(evento.requerimientos)
        evento.salas.clear()
        db.delete(evento)

    for requerimiento in requerimientos:
        db.delete(requerimiento)

    db.delete(solicitud)
    if solicitante and len(solicitante.solicitudes) <= 1:
        db.delete(solicitante)


@router.post("/", response_model=SolicitudResumenOut, status_code=status.HTTP_201_CREATED)
async def crear_solicitud(payload: SolicitudEventoCreate, db: Session = Depends(get_db)):
    salas = _validar_solape_evento(payload, db)
    solicitante = db.query(Solicitante).filter(Solicitante.correo == payload.solicitante_correo).first()
    if not solicitante:
        solicitante = Solicitante(correo=payload.solicitante_correo)
        db.add(solicitante)

    solicitante.nombre = payload.solicitante_nombre
    solicitante.apellido = payload.solicitante_apellido
    solicitante.no_de_telefono = payload.solicitante_telefono

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
        solicitud=solicitud,
        requerimientos=requerimientos,
        salas=salas,
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
            selectinload(Solicitud.eventos).selectinload(Evento.requerimientos),
        )
    ).scalars().one()
    return _solicitud_resumen(solicitud)


@router.put("/{id_solicitud}", response_model=SolicitudResumenOut)
async def actualizar_solicitud(
    id_solicitud: int,
    payload: SolicitudEventoCreate,
    db: Session = Depends(get_db),
):
    solicitud = _load_solicitud(db, id_solicitud)
    if not solicitud:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="La solicitud especificada no existe.",
      )

    evento = solicitud.eventos[0] if solicitud.eventos else None
    salas = _validar_solape_evento(payload, db, id_evento_ignorado=evento.id_evento if evento else None)

    solicitante = solicitud.solicitante or Solicitante(correo=payload.solicitante_correo)
    solicitante.nombre = payload.solicitante_nombre
    solicitante.apellido = payload.solicitante_apellido
    solicitante.correo = payload.solicitante_correo
    solicitante.no_de_telefono = payload.solicitante_telefono
    solicitud.solicitante = solicitante

    if not evento:
        evento = Evento(solicitud=solicitud)
        db.add(evento)

    requerimientos = evento.requerimientos or Requerimientos()
    evento.requerimientos = requerimientos

    requerimientos.acomodo = payload.acomodo
    requerimientos.equipo_de_sonido = payload.equipo_de_sonido
    requerimientos.cafeteria = payload.cafeteria
    requerimientos.videoconferencia = payload.videoconferencia

    evento.titulo = payload.evento_titulo
    evento.descripcion = payload.evento_descripcion
    evento.fecha = payload.evento_fecha
    evento.hora_de_inicio = payload.evento_inicio
    evento.hora_de_termino = payload.evento_fin
    evento.no_de_asistentes = payload.evento_asistentes
    evento.salas = salas

    db.commit()
    solicitud = _load_solicitud(db, id_solicitud)
    return _solicitud_resumen(solicitud)


@router.delete("/{id_solicitud}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_solicitud(id_solicitud: int, db: Session = Depends(get_db)):
    solicitud = db.execute(
        select(Solicitud)
        .where(Solicitud.id_solicitud == id_solicitud)
        .options(
            selectinload(Solicitud.solicitante),
            selectinload(Solicitud.eventos).selectinload(Evento.salas),
            selectinload(Solicitud.eventos).selectinload(Evento.requerimientos),
        )
    ).scalars().first()

    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La solicitud especificada no existe.",
        )

    _delete_solicitud_tree(db, solicitud)
    db.commit()


@router.patch("/{id_solicitud}/estado", response_model=SolicitudResumenOut)
async def actualizar_estado_solicitud(
    id_solicitud: int,
    payload: SolicitudEstadoUpdate,
    db: Session = Depends(get_db),
):
    estados_validos = {"pendiente", "aprobada", "rechazada"}
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
            selectinload(Solicitud.eventos).selectinload(Evento.requerimientos),
        )
    ).scalars().one()
    return _solicitud_resumen(solicitud)
