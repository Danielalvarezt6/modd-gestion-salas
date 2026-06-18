from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# importar routers
from app.routers import views, api_auth, api_salas, api_eventos

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

# Montar archivos estáticos para la landing y el login
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Rutas visuales
app.include_router(views.router)

# Rutas de API REST
app.include_router(api_auth.router)
app.include_router(api_salas.router)
app.include_router(api_eventos.router)
