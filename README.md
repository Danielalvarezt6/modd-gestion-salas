# MODD - Gestión de Salas Interactivas

MODD es una aplicación web integral diseñada para la administración, programación y seguimiento de salas interactivas en la Universidad de Sonora. Su propósito es erradicar el uso de hojas de cálculo y simplificar el proceso de reservas mediante una interfaz moderna, automatizada e inteligente.

El sistema fue desarrollado con un backend robusto basado en **FastAPI** y una interfaz interactiva fluida utilizando **Jinja2**, **JavaScript Vanilla** (para ligereza) y **Tailwind CSS**.

---

## 🚀 Funcionalidades Principales

### Para Usuarios y Solicitantes
- **Dashboard e Inicio de Sesión**: Autenticación segura mediante cookies JWT con redirección automática para rutas protegidas.
- **Formularios de Solicitud (Google Forms Ready)**: Compatibilidad para procesar solicitudes externas o de forma nativa a través de la aplicación.
- **Modo Oscuro/Claro**: Soporte completo de temas que se adaptan a las preferencias del sistema del usuario, incluyendo componentes dinámicos como el calendario y los PDF exportables.

### Para Administradores
- **Notificaciones por Correo**: Envío automático de resoluciones (aprobaciones o rechazos) vía email utilizando procesamiento asíncrono (`BackgroundTasks`) sin retrasar la respuesta del servidor.
- **Calendario Interactivo**: Visualización de eventos y disponibilidades en formato semanal, mensual y diario utilizando `FullCalendar`.
- **Drag & Drop Avanzado**: Ajuste dinámico de la duración de los eventos y la sala asignada arrastrando los bloques dentro del calendario, con cálculos de disponibilidad en tiempo real.
- **Detección Inteligente de Solapamientos**: El sistema previene colisiones de horarios, validando sala, fecha y hora. Si hay un conflicto, sugiere automáticamente salas alternativas disponibles.
- **Gestión de Solicitudes**: Aprobación, rechazo y re-evaluación de solicitudes en un solo clic. Las solicitudes rechazadas pueden editarse y reactivarse.
- **Reportes y Exportación PDF**: Generación de recuadros estadísticos de ocupación en el dashboard y exportación de calendarios y horarios a formatos imprimibles (PDF), filtrables por semana o día.

---

## 🏗️ Arquitectura y Tecnologías

El proyecto sigue una arquitectura **MVC-like** adaptada al ecosistema de FastAPI y está optimizado para su despliegue en la nube. Actualmente, la aplicación se encuentra alojada en **Render** (servidor web) y utiliza **Neon** (base de datos PostgreSQL Serverless).

### Stack Tecnológico
| Capa         | Tecnologías                                                                 |
|--------------|-----------------------------------------------------------------------------|
| **Backend**  | Python 3.10+, FastAPI, Pydantic, SQLAlchemy, Alembic                        |
| **Base de Datos** | PostgreSQL 14+ (alojada en **Neon Tech**)                                   |
| **Frontend** | HTML5, CSS Variables, Tailwind CSS, JavaScript (ES6), FullCalendar, Lucide Icons |
| **Generación PDF** | Motor Nativo (Direct PDF 1.4 Byte-stream)                                                 |
| **Infraestructura**| **Render** (Web Service), Gunicorn, Uvicorn                                  |

### Estructura de la Base de Datos (Relacional)
El diagrama entidad-relación principal se centra en el ciclo de vida de la reserva:
`Solicitante` ➔ (realiza) ➔ `Solicitud` ➔ (si es aprobada, se convierte en) ➔ `Evento` ➔ (ocupa) ➔ `Sala_Evento` ➔ `Sala`

Tablas involucradas:
- `usuarios`: Administradores con acceso al panel.
- `solicitante`: Datos de contacto de la persona u organización.
- `solicitud`: Intención de reserva, fecha, horas sugeridas y asistentes.
- `requerimientos`: Servicios adicionales (audio, proyector, catering).
- `evento`: Confirmación programada de una solicitud en tiempo real.
- `sala`: Catálogo de ubicaciones físicas y su capacidad técnica.
- `sala_evento`: Relación N:M para eventos que ocupan múltiples salas simultáneamente.

---

## 📂 Estructura del Proyecto

```text
modd-gestion-salas/
├── alembic/                # Configuraciones y scripts de migraciones DB
├── app/
│   ├── core/               # Núcleo: Configuración de entorno, conexión a BD, Seguridad (JWT), Emails
│   ├── models/             # ORM: Modelos SQLAlchemy que mapean las tablas en BD
│   ├── routers/            # Controladores: 
│   │   ├── views.py        # ➔ Renderizado SSR de Jinja2
│   │   └── api_*.py        # ➔ Endpoints RESTful para comunicación asíncrona con el Frontend
│   ├── schemas/            # Validación de datos con Pydantic (Request/Response)
│   ├── static/             # Archivos estáticos: CSS (Tailwind/Custom), JS, Imágenes, Favicons
│   └── templates/          # Vistas HTML, componentes (base.html) y modales de la interfaz
├── scripts/                # Herramientas de soporte (Población de datos Demo, Verificadores)
├── requirements.txt        # Dependencias de Python
└── README.md               # Documentación principal
```

---

## ⚙️ Instalación y Configuración (Desarrollo)

### Prerrequisitos
- **Python 3.10+** (Recomendado 3.11)
- **PostgreSQL** instalado y ejecutándose.

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd modd-gestion-salas
```

### 2. Entorno Virtual y Dependencias
Crea un entorno virtual para aislar las dependencias del proyecto:
```bash
python -m venv venv
venv\Scripts\activate   # En Windows
# source venv/bin/activate # En Linux/Mac
pip install -r requirements.txt
```

### 3. Configuración de Base de Datos y Correo
En tu motor de PostgreSQL, crea la base de datos y un usuario (opcional):
```sql
CREATE DATABASE modd_db;
CREATE USER modd_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE modd_db TO modd_user;
```

Crea un archivo `.env.local` en la raíz del proyecto (basándote en `.env.example`):
```env
DATABASE_URL=postgresql://modd_user:tu_password@localhost:5432/modd_db
SECRET_KEY=clave_secreta_para_firmar_jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=gestiondesalasmodd@gmail.com
SMTP_PASSWORD=tu_contraseña_de_aplicacion_gmail
FROM_EMAIL=gestiondesalasmodd@gmail.com
```

### 4. Migraciones y Población de Datos
Construye la estructura de tablas inicial:
```bash
alembic upgrade head
```

Opcionalmente, inyecta datos de prueba para experimentar con el sistema:
```bash
python scripts/seed_demo.py
```

### 5. Crear Usuario Administrador
Fuerza la creación de un usuario administrador local predeterminado:
```bash
python forzar_admin.py
```
*Credenciales de desarrollo: `admin@unison.mx` / `modd2026`*

### 6. Ejecutar Servidor de Desarrollo
```bash
uvicorn app.main:app --reload
```
La aplicación estará disponible en: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🌐 APIs Principales
El sistema expone endpoints seguros bajo `/api/` y los agrupa lógicamente:
- **Autenticación:** `/api/auth/login` (Generación JWT), `/api/auth/logout`.
- **Eventos:** Lógica de CRUD, asignación inteligente y Drag&Drop (`PUT /api/eventos/{id}`).
- **Solicitudes:** Aprobación (convierte Solicitud en Evento) y edición de estado (`PATCH /api/solicitudes/{id}/estado`).
- **Reportes:** Generación de resúmenes estadísticos y conversión de HTML a PDF (`GET /api/reportes/pdf`).

Toda la documentación técnica automática e interactiva (Swagger) está disponible internamente en `/docs` si está activado en el entorno.

---

## 👥 Integrantes del Equipo

- Daniel Eduardo Alvarez Terrazas
- Melina Gonzalez Mendez
- Omar Pacheco Velasquez
- Jesus David Ayala Morales
