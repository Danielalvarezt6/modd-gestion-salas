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
