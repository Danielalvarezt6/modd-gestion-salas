"""
Enrutador de vistas HTML principales de la aplicación MODD.

Este módulo contiene todas las rutas GET que retornan páginas HTML
(TemplateResponse) renderizadas usando el motor Jinja2. Aquí se inyectan
datos estadísticos y de contexto necesarios para inicializar las vistas.
"""

from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func
from datetime import date, timedelta

from app.core.database import get_db
from app.core.security import require_authenticated_page
from app.models.salas import Solicitud, Evento
from app.models.usuarios import Usuario

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Renderiza el landing page"""
    return templates.TemplateResponse(request=request, name="landing.html")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Renderiza el formulario de inicio de sesión."""
    return templates.TemplateResponse(request=request, name="login.html")



@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, current_user: Usuario = Depends(require_authenticated_page)):
    """Renderiza la página del dashboard tras iniciar sesión."""
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/calendario", response_class=HTMLResponse)
async def calendar_page(request: Request, current_user: Usuario = Depends(require_authenticated_page)):
    """
    Renderiza la sección visual del calendario interactivo.
    
    Esta vista carga la base donde FullCalendar operará mediante JS asíncrono
    consumiendo los endpoints de `/api/eventos`.
    """
    return templates.TemplateResponse(request=request, name="calendario.html")

@router.get("/calendario/print", response_class=HTMLResponse)
async def print_calendar_page(
    request: Request,
    start_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_authenticated_page)
):
    """
    Renderiza la vista de exportación e impresión del calendario para una semana específica.
    
    Toma una fecha pivote (`start_date`), calcula la semana correspondiente (lunes a domingo),
    extrae todos los eventos aprobados de esa semana con sus relaciones (salas, solicitante),
    y los agrupa en un diccionario estructurado para facilitar el renderizado de la tabla en Jinja.
    """
    # Aislar el inicio y fin de la semana (Lunes = 0, Domingo = 6)
    lunes = start_date - timedelta(days=start_date.weekday())
    domingo = lunes + timedelta(days=6)
    
    stmt = (
        select(Evento)
        .join(Solicitud)
        .where(Solicitud.estado == "aprobada")
        .where(Evento.fecha >= lunes)
        .where(Evento.fecha <= domingo)
        .options(selectinload(Evento.salas), selectinload(Evento.solicitud).selectinload(Solicitud.solicitante))
        .order_by(Evento.fecha, Evento.hora_de_inicio)
    )
    eventos = db.execute(stmt).scalars().all()
    
    # Agrupar eventos por día (0 = Lunes, 6 = Domingo)
    eventos_por_dia = {i: [] for i in range(7)}
    for e in eventos:
        dia_idx = (e.fecha - lunes).days
        if 0 <= dia_idx <= 6:
            eventos_por_dia[dia_idx].append(e)
    
    return templates.TemplateResponse(
        "print_calendar.html",
        {
            "request": request,
            "lunes": lunes,
            "domingo": domingo,
            "eventos_por_dia": eventos_por_dia,
            "timedelta": timedelta
        }
    )


@router.get("/solicitudes", response_class=HTMLResponse)
async def requests_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_authenticated_page),
):
    """
    Renderiza la sección de administración de solicitudes de salas.
    
    Inyecta métricas clave en la cabecera (totales, pendientes, aprobadas, rechazadas)
    y envía la lista completa de solicitudes para poblar la tabla principal.
    """
    # Consultar todas las solicitudes (Nota: En producción se sugeriría paginación)
    solicitudes_db = db.execute(select(Solicitud)).scalars().all()

    # Cálculo eficiente de las métricas agrupadas por estado usando base de datos
    count_stmt = select(Solicitud.estado, func.count(Solicitud.id_solicitud)).group_by(
        Solicitud.estado
    )
    resultados_conteo = db.execute(count_stmt).all()
    conteo_dict = {estado: cantidad for estado, cantidad in resultados_conteo}

    # Asignar los contadores, con un fallback a 0 en caso de no existir registros de un tipo
    total = sum(conteo_dict.values())
    pendientes = conteo_dict.get("pendiente", 0)
    aprobadas = conteo_dict.get("aprobada", 0)
    rechazadas = conteo_dict.get("rechazada", 0)

    return templates.TemplateResponse(
        "solicitudes.html",
        {
            "request": request,
            "solicitudes": solicitudes_db,
            "stat_total": total,
            "stat_pendientes": pendientes,
            "stat_aprobadas": aprobadas,
            "stat_rechazadas": rechazadas,
        },
    )


@router.get("/eventos", response_class=HTMLResponse)
async def events_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_authenticated_page),
):
    """
    Renderiza el listado tabular de eventos (solicitudes ya aprobadas).
    
    A diferencia de la vista de calendario, esta vista expone un formato crudo 
    y lineal (lista) para la administración masiva o auditoría visual de eventos confirmados.
    """
    eventos_db = db.execute(select(Evento)).scalars().all()

    # Contador rápido para estadísticas de resumen
    count_stmt = select(func.count(Evento.id_evento))
    total = db.execute(count_stmt).scalar()

    return templates.TemplateResponse(
        "eventos.html", {"request": request, "eventos": eventos_db, "stat_total": total}
    )


@router.get("/reportes", response_class=HTMLResponse)
async def reports_page(request: Request, current_user: Usuario = Depends(require_authenticated_page)):
    return templates.TemplateResponse(request=request, name="reportes.html")
