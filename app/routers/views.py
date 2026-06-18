from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """ Renderiza el landing page """
    return templates.TemplateResponse(request=request, name="landing.html")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """ Renderiza el formulario de inicio de sesión."""
    return templates.TemplateResponse(request=request, name="login.html")
    
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """ Renderiza la página del dashboard tras iniciar sesión."""
    return templates.TemplateResponse(request=request, name="dashboard.html")

@router.get("/calendario", response_class=HTMLResponse)
async def calendar_page(request: Request):
    """ Renderiza la seccion visual del calendario."""
    return templates.TemplateResponse(request=request, name="calendario.html")

@router.get("/solicitudes", response_class=HTMLResponse)
async def requests_page(request: Request):
    """ Renderiza la seccion visual de solicitudes."""
    return templates.TemplateResponse(request=request, name="solicitudes.html")

@router.get("/eventos", response_class=HTMLResponse)
async def events_page(request: Request):
    """ Renderiza la seccion visual de eventos."""
    return templates.TemplateResponse(request=request, name="eventos.html")

@router.get("/reportes", response_class=HTMLResponse)
async def reports_page(request: Request):
    """ Renderiza la seccion visual de reportes."""
    return templates.TemplateResponse(request=request, name="reportes.html")
