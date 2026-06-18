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
├── .env/                    # entorno virtual de Python
├── .env.example             # Plantilla de contraseñas de ejemplo
├── .gitignore               # Lista negra de archivos que Git debe ignorar
├── README.md  
├── requirements.txt         # Lista de dependencias
├── alembic.ini              # Archivo de configuración maestro de Alembic
├── forzar_admin.py          # Script de "fuerza bruta" para inyectar admins (uso interno)
├── seed.py                  # Script estándar de inyección de datos (opcional)
│
├── alembic/                 # CARPETA DE MIGRACIONES (Base de Datos)
│   ├── env.py               # Puente que conecta Alembic con tu config.py y tus modelos
│   ├── script.py.mako       # Plantilla base de Alembic
│   └── versions/            # Historial de todos los cambios en tus tablas
│       └── 25b4a2a8460d_creacion_inicial_tablas_modd.py  # La migración de las tablas
│
└── app/                     # NÚCLEO DE LA APLICACIÓN FASTAPI
    ├── __init__.py
    ├── main.py              # Donde se unen rutas, frontend y se levanta el servidor.
    │
    ├── core/                # CONFIGURACIONES CENTRALES
    │   ├── __init__.py
    │   ├── config.py        # Lógica de Pydantic que lee el archivo .env.local
    │   ├── database.py      # Motor de SQLAlchemy (SessionLocal, Base)
    │   └── security.py      # Lógica de encriptación y creación de Tokens JWT
    │
    ├── models/              # PLANOS DE LA BASE DE DATOS (SQLAlchemy)
    │   ├── __init__.py
    │   ├── usuarios.py      # Clase Usuario (id, correo, hashed_password)
    │   └── salas.py         # Clases Sala, Solicitante, Evento, Requerimientos, etc.
    │
    ├── routers/             # CONTROLADORES DE TRÁFICO (Endpoints)
    │   ├── __init__.py
    │   ├── views.py         # Rutas visuales que devuelven el HTML (Ej: GET /login)
    │   ├── api_auth.py      # Lógica de inicio/cierre sesión (Ej: POST /api/auth/login)
    │   └── api_salas.py     # (Próximamente) Rutas para crear, 
    │
    ├── schemas/             
    │   └── __init__.py      # Aquí irán las reglas de qué datos son obligatorios al crear cosas
    │
    ├── static/             
    │   ├── css/
    │   │   └── custom.css
    │   ├── js/
    │   └── assets/
    │       └── logo.png
    │
    └── templates/          
        ├── login.html
        └── dashboard.html   
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

4. **Crear la Base de Datos en PostgreSQL**
   ```bash
   Abre tu consola de PostgreSQL (sudo -u postgres psql) y ejecuta:
   CREATE USER tu_usuario WITH PASSWORD 'tu_contraseña';
   CREATE DATABASE modd_db;
   GRANT ALL PRIVILEGES ON DATABASE modd_db TO tu_usuario;
   \c modd_db
   GRANT ALL ON SCHEMA public TO tu_usuario;
   \q
   ```

5. **Configurar Variables de entorno:**
   Crea un archivo llamado ```.env.local``` en la raíz del proyecto.
   Copia el contenido de .env.exaple y pon las credenciales que acabas de crear en PostgreSQL:
   ```bash
    DATABASE_URL=postgresql://tu_usuario:tu_contraseña@localhost:5432/modd_db
	SECRET_KEY=escribe_aqui_una_llave_aleatoria
	ALGORITHM=HS256
	ACCESS_TOKEN_EXPIRE_MINUTES=60
   ```
6. **Crear las tablas (Alembic)**
No necesitas crear nuevas migraciones. Solo aplica la estructura que ya está en el códio ejecutando:
	```bash
	alembic upgrade head
	```
7. **Inyectar el Administrador de Prueba**
Para poder iniciar sesión, se necesita un usuario en la base de datos. Abre el archivo forzar_admin.py, pon temporalmente tu contraseña de PostgreSQL en la linea ```DATABASE_URL``` y ejecuta:
	```bash
	python forzar_admin.py
	```
8. **Levantar el servidor**
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
