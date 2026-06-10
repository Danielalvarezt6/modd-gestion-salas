"""
Servidor FastAPI para MODD - Gestión Interactiva de Salas
Universidad de Sonora - Facultad ICEN

Este es un ejemplo básico de servidor FastAPI que sirve las plantillas Jinja2
y archivos estáticos para la Fase 1 (Landing Page + Login).
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional

# Inicializar aplicación FastAPI
app = FastAPI(
    title="MODD - Gestión de Salas",
    description="Sistema de gestión de salas interactivas para la Facultad ICEN",
    version="1.0.0"
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar plantillas Jinja2
templates = Jinja2Templates(directory="templates")

# Credenciales de demostración (EN PRODUCCIÓN USAR BASE DE DATOS)
DEMO_EMAIL = "admin@unison.mx"
DEMO_PASSWORD = "modd2026"


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """
    Renderiza la página de inicio (landing page)
    """
    return templates.TemplateResponse(
        request=request,
        name="landing.html"
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Renderiza la página de login
    """
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@app.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """
    Procesa el formulario de login (versión server-side)
    
    NOTA: La validación actual está en JavaScript client-side.
    Esta ruta es un ejemplo de cómo implementar la autenticación
    en el servidor para mayor seguridad.
    """
    # Validar credenciales (EN PRODUCCIÓN: verificar contra base de datos)
    if email == DEMO_EMAIL and password == DEMO_PASSWORD:
        # TODO: Crear sesión/token JWT
        # TODO: Establecer cookie de sesión
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # Credenciales incorrectas
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": "Credenciales incorrectas. Usa admin@unison.mx / modd2026"}
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Página de dashboard (Fase 2 - Por implementar)
    """
    # TODO: Verificar autenticación
    # TODO: Renderizar template de dashboard
    return HTMLResponse(
        content="""
        <html>
            <head>
                <title>Dashboard - MODD</title>
                <style>
                    body {
                        font-family: Inter, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }
                    .container {
                        text-align: center;
                        padding: 2rem;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 1rem;
                        backdrop-filter: blur(10px);
                    }
                    h1 { margin: 0 0 1rem 0; }
                    p { margin: 0.5rem 0; }
                    a {
                        display: inline-block;
                        margin-top: 1rem;
                        padding: 0.75rem 1.5rem;
                        background: white;
                        color: #667eea;
                        text-decoration: none;
                        border-radius: 0.5rem;
                        font-weight: 600;
                    }
                    a:hover { background: #f0f0f0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ ¡Autenticación Exitosa!</h1>
                    <p>Has iniciado sesión correctamente.</p>
                    <p><strong>Email:</strong> admin@unison.mx</p>
                    <p style="margin-top: 1.5rem; opacity: 0.9;">
                        El dashboard completo se implementará en la Fase 2.
                    </p>
                    <a href="/">← Volver al inicio</a>
                </div>
            </body>
        </html>
        """,
        status_code=200
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint para monitoreo
    """
    return {
        "status": "healthy",
        "service": "MODD API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
