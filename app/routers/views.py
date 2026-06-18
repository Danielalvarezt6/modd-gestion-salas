from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.salas import Solicitud

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
async def dashboard_page(request: Request):
    """Renderiza la página del dashboard tras iniciar sesión."""
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/calendario", response_class=HTMLResponse)
async def calendar_page(request: Request):
    """Renderiza la seccion visual del calendario."""
    return templates.TemplateResponse(request=request, name="calendario.html")


@router.get("/solicitudes", response_class=HTMLResponse)
async def requests_page(request: Request, db: Session = Depends(get_db)):
    """Renderiza la seccion visual de solicitudes."""
    solicitudes_db = db.execute(select(Solicitud)).scalars().all()

    count_stmt = select(Solicitud.estado, func.count(Solicitud.id_solicitud)).group_by(
        Solicitud.estado
    )
    resultados_conteo = db.execute(count_stmt).all()
    conteo_dict = {estado: cantidad for estado, cantidad in resultados_conteo}

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
async def events_page(request: Request):
    """Renderiza la seccion visual de eventos."""
    return templates.TemplateResponse(request=request, name="eventos.html")


@router.get("/reportes", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Renderiza la seccion visual de reportes."""
    return templates.TemplateResponse(request=request, name="reportes.html")
