from fastapi import APIRouter, Depends
from typing import List
# from sqlalchemy.orm import Session
# from app.core.database import get_db
# from app.models.salas import Sala, Solicitud

router = APIRouter()

@router.get("/", response_model=list)
async def obtener_salas():
    """
    Retorna la lista de salas disponibles (JSON).
    El desarrollador del frontend consumirá esta ruta (GET /api/salas/).
    """

    # Simulación de respuesta de base de datos
    return [
        {"numero_sala": 1, "capacidad": 30, "estado": "ocupada"},
        {"numero_sala": 2, "capacidad": 50, "estado": "disponible"},
        {"numero_sala": 3, "capacidad": 120, "estado":"disponible"}
    ]

@router.get("/solicitudes/pendientes")
async def obtener_solicitudes_pendientes():
    """
    Retorna JSON con las solicitudes en espera de aprobación.
    """
    return [
        {"id": 1, "titulo": "Taller de Innovación", "fecha": "2026-06-12", "sala": 1},
        {"id": 2, "titulo": "Reunión Académica", "fecha": "2026-06-14", "sala": 2}
    ]
