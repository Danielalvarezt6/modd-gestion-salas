from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List
from datetime import date, time

from app.core.database import get_db
from app.models.salas import Sala, Evento, Solicitud
from app.schemas.salas import SalaOut, SalaBase  # Importa tus schemas recién creados

router = APIRouter(prefix="/api/salas", tags=["Salas"])
CAPACIDAD_MAXIMA_POR_SALA = 40

# 1. Endpoint para Consultar Disponibilidad
@router.get("/disponibilidad")
async def consultar_disponibilidad(
    fecha: date,
    inicio: time,
    fin: time,
    id_evento_ignorado: int = None,
    db: Session = Depends(get_db)
):
    eventos_mismo_dia = db.execute(
        select(Evento)
        .outerjoin(Solicitud)
        .where(Evento.fecha == fecha)
        .where((Solicitud.estado.is_(None)) | (Solicitud.estado != "rechazada"))
    ).scalars().all()

    salas_ocupadas = set()
    for evento in eventos_mismo_dia:
        if id_evento_ignorado is not None and evento.id_evento == id_evento_ignorado:
            continue
        if inicio < evento.hora_de_termino and fin > evento.hora_de_inicio:
            for item in evento.salas:
                salas_ocupadas.add(item.numero_sala)
    
    return {"ocupadas": list(salas_ocupadas)}

# 2. Endpoint para OBTENER todas las salas
@router.get("/", response_model=List[SalaOut])
async def obtener_salas(db: Session = Depends(get_db)):
    salas = db.execute(select(Sala)).scalars().all()
    return salas

# 3. Endpoint para CREAR una nueva sala (Útil si tienes un panel de admin)
@router.post("/", response_model=SalaOut, status_code=status.HTTP_201_CREATED)
async def crear_sala(sala: SalaBase, db: Session = Depends(get_db)):
    if sala.capacidad > CAPACIDAD_MAXIMA_POR_SALA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El cupo maximo por sala es de {CAPACIDAD_MAXIMA_POR_SALA} personas.",
        )

    stmt = select(Sala).where(Sala.numero_sala == sala.numero_sala)
    sala_existente = db.execute(stmt).scalars().first()

    if sala_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La sala número {sala.numero_sala} ya está registrada.",
        )

    nueva_sala = Sala(numero_sala=sala.numero_sala, capacidad=sala.capacidad)
    db.add(nueva_sala)
    db.commit()
    db.refresh(nueva_sala)
    return nueva_sala
