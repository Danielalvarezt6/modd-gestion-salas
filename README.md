# MODD - Sistema de Gestión de Salas Interactivas

MODD es una aplicación web diseñada para la administración y reserva de las salas interactivas del edificio de Servicios Escolares en la Universidad de Sonora. Su propósito es reemplazar el control tradicional basado en hojas de cálculo para evitar conflictos de horarios, facilitar la consulta y mejorar la comunicación en la gestión de eventos.

## Características Principales

* **Visualización de Calendario**: Interfaz interactiva para revisar la programación por día, semana y mes, identificando eventos por sala mediante colores.
* **Solicitudes de Reserva**: Flujo digitalizado para que usuarios internos y externos soliciten salas, permitiendo su revisión y validación antes de agendar.
* **Control de Solapamientos**: Verificación en tiempo real para impedir reservas duplicadas o empalmes de horarios en una misma sala.
* **Diseño Institucional**: Interfaz moderna basada en la paleta de colores oficial de la Universidad de Sonora, con soporte completo para modo claro y modo oscuro.

---

## Estructura del Proyecto

```text
modd-gestion-salas/
│
├── .env                        # Variables de entorno (credenciales, puerto, base de datos)
├── requirements.txt            # Dependencias del proyecto (FastAPI, Uvicorn, Jinja2, etc.)
│
└── app/                        # Directorio principal del módulo de la aplicación
    ├── __init__.py
    ├── main.py                 # Punto de entrada de Uvicorn, configuración de FastAPI y CORS
    │
    ├── routers/                # Enrutadores (Controladores de los endpoints)
    │   ├── __init__.py
    │   ├── views.py            # Rutas visuales que renderizan las plantillas Jinja2
    │   ├── api_auth.py         # Endpoints REST para autenticación (recibe el POST del login)
    │   └── api_salas.py        # Endpoints REST para enviar JSONs al dashboard (Fase 2)
    │
    ├── templates/              # Plantillas visuales (Frontend renderizado por servidor)
    │   ├── base.html           # Plantilla maestra con cabeceras y Tailwind
    │   ├── landing.html        # Página principal de información
    │   ├── login.html          # Formulario de inicio de sesión con fetch asíncrono
    │   └── dashboard.html      # Pantalla de éxito tras el inicio de sesión
    │
    ├── static/                 # Archivos estáticos públicos
    │   ├── css/
    │   │   └── custom.css      # Estilos personalizados (colores, sombras, utilidades)
    │   ├── js/
    │   │   └── landing.js      # Interactividad del frontend
    │   └── assets/
    │       └── logo.png        # Recursos gráficos y multimedia
    │
    ├── core/                   # (En preparación) Lógica central y configuraciones
    │   ├── __init__.py
    │   ├── config.py           
    │   ├── database.py         # Aquí irá el 'engine' y la conexión a PostgreSQL
    │   └── security.py         
    │
    ├── models/                 # (En preparación) Modelos ORM (Traducción del diagrama E-R)
    │   ├── __init__.py
    │   ├── usuarios.py         
    │   └── salas.py            
    │
    ├── schemas/                # (En preparación) Esquemas de validación de Pydantic
    │   ├── __init__.py
    │   ├── usuarios.py         
    │   └── salas.py            
    │
    └── crud/                   # (En preparación) Operaciones directas a la base de datos
        ├── __init__.py
        ├── usuarios.py         
        └── salas.py
```

---

## Instalación y Configuración

### Prerrequisitos
* Python 3.10 o superior

### Pasos para Ejecutar Localmente

1. **Clonar el repositorio:**
   ```bash
   git clone <url-del-repositorio>
   cd modd-gestion-salas
   ```

2. **Crear y activar el entorno virtual:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar el servidor de desarrollo:**
   ```bash
    uvicorn app.main:app --reload
   ```
   *Nota: El servidor iniciará en http://localhost:8000*

### Credenciales de Demostración (Fase 1)
Para probar el acceso a la sección de login:
* **Usuario:** `admin@unison.mx`
* **Contraseña:** `modd2026`

---

## Integrantes del Proyecto

Desarrollado por estudiantes de la **Licenciatura en Ciencias de la Computación** del **Departamento de Matemáticas** de la Universidad de Sonora:

* Daniel Eduardo Alvarez Terrazas
* Melina González Méndez
* Omar Pacheco Velasquez
* Jesús David Ayala Morales
