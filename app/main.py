from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from app.core.config import settings

# importar routers
from app.routers import views, api_auth, api_salas, api_eventos, api_solicitudes, api_reportes

app = FastAPI(
    title="MODD API - Gesión de Salas",
    description="Backend para el sistema de salas de la Universidad de Sonora",
    version="1.0.0",
)

# Configuración CORS para permitir que el frontend consuma la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar por el dominio del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PROTECTED_PAGE_PATHS = {"/dashboard", "/calendario", "/solicitudes", "/eventos", "/reportes"}


@app.middleware("http")
async def redirect_unauthenticated_pages(request: Request, call_next):
    if request.url.path in PROTECTED_PAGE_PATHS:
        raw_token = request.cookies.get("access_token", "")
        token = raw_token.replace("Bearer ", "", 1)
        try:
            if not token:
                raise JWTError("missing token")
            jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError:
            return RedirectResponse(url="/login", status_code=303)

    return await call_next(request)

# Montar archivos estáticos para la landing y el login
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Rutas visuales
app.include_router(views.router)

# Rutas de API REST
app.include_router(api_auth.router)
app.include_router(api_salas.router)
app.include_router(api_eventos.router)
app.include_router(api_solicitudes.router)
app.include_router(api_reportes.router)
