"""
API Router para la gestión de Solicitudes de reserva de salas.

Contiene la lógica de negocio principal para crear, validar, actualizar,
aprobar y rechazar solicitudes. Incluye los algoritmos de detección de colisiones
de horarios y la asignación automática/híbrida de salas contiguas.
"""

from datetime import date, datetime, time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.email import enviar_correo_resolucion
from app.models.salas import Evento, Requerimientos, Sala, Solicitante, Solicitud
from app.schemas.salas import SolicitudEstadoUpdate, SolicitudEventoCreate, SolicitudResumenOut

router = APIRouter(prefix="/api/solicitudes", tags=["Solicitudes"])
CAPACIDAD_MAXIMA_POR_SALA = 40
HORA_APERTURA = time(8, 0)
HORA_CIERRE = time(20, 0)


def _solicitud_resumen(solicitud: Solicitud, advertencia: str = None) -> SolicitudResumenOut:
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
        advertencia_reubicacion=advertencia,
    )

def _calcular_advertencia_reubicacion(db: Session, solicitud: Solicitud) -> str | None:
    """
    Simula la aprobación de una solicitud pendiente para prever si forzará
    la reubicación de eventos preexistentes.
    
    Retorna un string con la advertencia si hay colisiones mitigables, o None.
    """
    evento_nuevo = solicitud.eventos[0] if solicitud.eventos else None
    if not evento_nuevo or not evento_nuevo.salas:
        return None
    
    todas_las_salas = db.execute(select(Sala).order_by(Sala.numero_sala)).scalars().all()
    eventos_mismo_dia = db.execute(
        select(Evento)
        .outerjoin(Solicitud)
        .where(Evento.fecha == evento_nuevo.fecha)
        .where(Evento.id_evento != evento_nuevo.id_evento)
        .where((Solicitud.estado.is_(None)) | (Solicitud.estado != "rechazada"))
        .options(selectinload(Evento.salas))
    ).scalars().all()
    
    eventos_en_conflicto = []
    salas_ocupadas_por_otros = set()
    
    for e in eventos_mismo_dia:
        if evento_nuevo.hora_de_inicio < e.hora_de_termino and evento_nuevo.hora_de_termino > e.hora_de_inicio:
            salas_nums = {s.numero_sala for s in e.salas}
            salas_ocupadas_por_otros.update(salas_nums)
            if salas_nums.intersection({s.numero_sala for s in evento_nuevo.salas}):
                eventos_en_conflicto.append(e)
                
    if not eventos_en_conflicto:
        return None
        
    mensajes = []
    for e_conflicto in eventos_en_conflicto:
        salas_ocupadas_sin_este = salas_ocupadas_por_otros - {s.numero_sala for s in e_conflicto.salas}
        salas_ocupadas_sin_este.update({s.numero_sala for s in evento_nuevo.salas})
        
        salas_libres = [s for s in todas_las_salas if s.numero_sala not in salas_ocupadas_sin_este]
        bloque = _get_bloques_contiguos(salas_libres, len(e_conflicto.salas))
        
        if bloque:
            nombres_salas = " y ".join([f"Sala {s.numero_sala}" for s in bloque])
            mensajes.append(f"'{e_conflicto.titulo}' a la {nombres_salas}")
            salas_ocupadas_por_otros = salas_ocupadas_sin_este
            salas_ocupadas_por_otros.update({s.numero_sala for s in bloque})
            
    if mensajes:
        return f"⚠️ Si apruebas esta solicitud, se reubicará automáticamente: " + ", ".join(mensajes) + "."
    return None


def _get_bloques_contiguos(salas_list, needed):
    """
    Busca bloques de N salas contiguas (ej. Sala 1 y Sala 2) dentro de
    una lista de salas disponibles. Necesario para mantener la logística
    cuando un evento requiere abrir las puertas divisoras entre salas.
    """
    nums = sorted([s.numero_sala for s in salas_list])
    for i in range(len(nums) - needed + 1):
        if nums[i+needed-1] - nums[i] == needed - 1:
            return [s for s in salas_list if s.numero_sala in nums[i:i+needed]]
    return None


def _validar_solape_evento(payload: SolicitudEventoCreate, db: Session, id_evento_ignorado: int | None = None):
    """
    Valida la disponibilidad de salas para un bloque de tiempo dado.
    
    Operativa en dos modos:
    1. Manual (Administradora envía `salas_ids`): Verifica que el conjunto de salas pedidas no colisione.
    2. Automático (Formularios web sin `salas_ids`): Calcula cuántas salas se necesitan basándose en
       el número de asistentes y busca bloques contiguos. Si no hay bloque libre, intenta simular
       una reubicación matemática de otros eventos para hacer espacio.
    """
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
    if asistentes > 125:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La capacidad máxima de asistentes es de 125."
        )
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
        todas_las_salas_ordenadas = sorted(todas_las_salas, key=lambda s: s.numero_sala)
        bloque_libre = _get_bloques_contiguos(salas_disponibles, salas_necesarias)
        if bloque_libre:
            return bloque_libre
            
        # Si no hay bloque libre, buscar si podemos reubicar UN evento para liberar espacio
        # (Esto permite guardar la solicitud como pendiente con conflicto temporal)
        for evento_choca in eventos_mismo_dia:
            if id_evento_ignorado is not None and evento_choca.id_evento == id_evento_ignorado:
                continue
            if payload.evento_inicio < evento_choca.hora_de_termino and payload.evento_fin > evento_choca.hora_de_inicio:
                # Simular quitar este evento
                salas_ocupadas_simuladas = set(salas_ocupadas)
                for s in evento_choca.salas:
                    salas_ocupadas_simuladas.discard(s.numero_sala)
                
                salas_disponibles_simuladas = [s for s in todas_las_salas_ordenadas if s.numero_sala not in salas_ocupadas_simuladas]
                bloque_para_nuevo = _get_bloques_contiguos(salas_disponibles_simuladas, salas_necesarias)
                
                if bloque_para_nuevo:
                    # El nuevo cabe, ¿pero a dónde se va el que choca?
                    salas_libres_para_choca = [s for s in salas_disponibles_simuladas if s not in bloque_para_nuevo]
                    bloque_para_choca = _get_bloques_contiguos(salas_libres_para_choca, len(evento_choca.salas))
                    
                    if bloque_para_choca:
                        # Se puede reubicar matemáticamente. Asignar el bloque al nuevo (causando choque temporal).
                        # La administradora verá el choque y al aprobar, el sistema hará el movimiento real.
                        return bloque_para_nuevo
                        
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Se requieren {salas_necesarias} salas contiguas para {asistentes} asistentes, y no hay forma de acomodarlos ni reubicando eventos."
        )


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
        .order_by(Solicitud.id_solicitud.desc())
    ).scalars().all()

    res = []
    for sol in solicitudes:
        adv = None
        if sol.estado == "pendiente":
            adv = _calcular_advertencia_reubicacion(db, sol)
        res.append(_solicitud_resumen(sol, adv))
    return res


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
    advertencia = None
    try:
        salas = _validar_solape_evento(payload, db)
    except HTTPException as e:
        if payload.salas_ids is None and e.status_code in (status.HTTP_409_CONFLICT, status.HTTP_422_UNPROCESSABLE_ENTITY):
            salas = []
            advertencia = f"[ALERTA_SISTEMA]{e.detail}[/ALERTA_SISTEMA]"
        else:
            raise

    # Ahora permitimos múltiples solicitudes con el mismo correo pero diferente responsable
    solicitante = Solicitante(
        correo=payload.solicitante_correo,
        nombre=payload.solicitante_nombre,
        apellido=payload.solicitante_apellido,
        no_de_telefono=payload.solicitante_telefono
    )
    db.add(solicitante)

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
    
    descripcion_final = payload.evento_descripcion or ""
    if advertencia:
        separador = "\n\n" if descripcion_final else ""
        descripcion_final += f"{separador}{advertencia}"

    evento = Evento(
        titulo=payload.evento_titulo,
        descripcion=descripcion_final,
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
    adv = _calcular_advertencia_reubicacion(db, solicitud) if solicitud.estado == "pendiente" else None
    return _solicitud_resumen(solicitud, adv)


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
    adv = _calcular_advertencia_reubicacion(db, solicitud) if solicitud.estado == "pendiente" else None
    return _solicitud_resumen(solicitud, adv)


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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Actualiza el estado de la solicitud (pendiente, aprobada, rechazada).
    
    - Si el estado pasa a "aprobada", se consolida el evento: 
      el algoritmo recalcula las colisiones y efectúa las reubicaciones
      automáticas reales de otros eventos si fuera necesario para dar cabida
      al nuevo evento prioritario.
    """
    estados_validos = {"pendiente", "aprobada", "rechazada"}
    if payload.estado not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Estado de solicitud no valido.",
        )

    solicitud = db.execute(
        select(Solicitud)
        .where(Solicitud.id_solicitud == id_solicitud)
        .options(
            selectinload(Solicitud.solicitante),
            selectinload(Solicitud.eventos).selectinload(Evento.salas),
        )
    ).scalars().first()
    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La solicitud especificada no existe.",
        )

    if payload.estado == "aprobada":
        evento_nuevo = solicitud.eventos[0] if solicitud.eventos else None
        if evento_nuevo:
            todas_las_salas = db.execute(select(Sala).order_by(Sala.numero_sala)).scalars().all()
            eventos_mismo_dia = db.execute(
                select(Evento)
                .outerjoin(Solicitud)
                .where(Evento.fecha == evento_nuevo.fecha)
                .where(Evento.id_evento != evento_nuevo.id_evento)
                .where((Solicitud.estado.is_(None)) | (Solicitud.estado != "rechazada"))
                .options(selectinload(Evento.salas))
            ).scalars().all()
            
            eventos_en_conflicto = []
            salas_ocupadas_por_otros = set()
            
            for e in eventos_mismo_dia:
                if evento_nuevo.hora_de_inicio < e.hora_de_termino and evento_nuevo.hora_de_termino > e.hora_de_inicio:
                    salas_nums = {s.numero_sala for s in e.salas}
                    salas_ocupadas_por_otros.update(salas_nums)
                    if salas_nums.intersection({s.numero_sala for s in evento_nuevo.salas}):
                        eventos_en_conflicto.append(e)
            
            for e_conflicto in eventos_en_conflicto:
                salas_ocupadas_sin_este = salas_ocupadas_por_otros - {s.numero_sala for s in e_conflicto.salas}
                salas_ocupadas_sin_este.update({s.numero_sala for s in evento_nuevo.salas})
                
                salas_libres = [s for s in todas_las_salas if s.numero_sala not in salas_ocupadas_sin_este]
                bloque = _get_bloques_contiguos(salas_libres, len(e_conflicto.salas))
                
                if bloque:
                    e_conflicto.salas = bloque
                    salas_ocupadas_por_otros = salas_ocupadas_sin_este
                    salas_ocupadas_por_otros.update({s.numero_sala for s in bloque})
                    db.add(e_conflicto)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"No se puede aprobar. El evento '{e_conflicto.titulo}' que choca con esta solicitud ya no tiene salas contiguas disponibles para ser reubicado automáticamente."
                    )

    solicitud.estado = payload.estado
    db.commit()

    if payload.estado in ("aprobada", "rechazada"):
        evento = solicitud.eventos[0] if solicitud.eventos else None
        if evento:
            dia_str = evento.fecha.strftime("%d/%m/%Y")
            hora_inicio_str = evento.hora_de_inicio.strftime("%H:%M")
            hora_fin_str = evento.hora_de_termino.strftime("%H:%M")
            background_tasks.add_task(
                enviar_correo_resolucion,
                to_email=solicitud.solicitante.correo,
                estado=payload.estado,
                titulo_evento=evento.titulo,
                dia=dia_str,
                hora_inicio=hora_inicio_str,
                hora_fin=hora_fin_str,
            )

    solicitud_actualizada = db.execute(
        select(Solicitud)
        .where(Solicitud.id_solicitud == id_solicitud)
        .options(
            selectinload(Solicitud.solicitante),
            selectinload(Solicitud.eventos).selectinload(Evento.salas),
            selectinload(Solicitud.eventos).selectinload(Evento.requerimientos),
        )
    ).scalars().one()
    adv = _calcular_advertencia_reubicacion(db, solicitud_actualizada) if solicitud_actualizada.estado == "pendiente" else None
    return _solicitud_resumen(solicitud_actualizada, adv)
