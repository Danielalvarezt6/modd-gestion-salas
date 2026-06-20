# MODD - Gestion de Salas Interactivas

MODD es una aplicacion web para administrar solicitudes, eventos, calendario y reportes PDF de salas interactivas. El sistema usa FastAPI, Jinja2, Tailwind CSS, JavaScript Vanilla, SQLAlchemy, Alembic y PostgreSQL.

## Funcionalidades

- Login con cookie JWT y rutas internas protegidas.
- Dashboard.
- Calendario por semana, mes y dia.
- Deteccion de solapamientos por sala, fecha y horario.
- Sugerencia de salas disponibles cuando un horario se solapa.
- Arrastre  y redimension de eventos por horas y por salas.
- Asignación inteligente e híbrida de salas (selección manual con validación de cupo o automática para integraciones externas como Google Forms).
- Edición, aprobación y rechazo de solicitudes de sala.
- Reportes PDF semanal, mensual, por sala y personalizado.
- Modo claro/oscuro en toda la aplicacion.

## Modelo Relacional

El proyecto contiene las tablas del modelo:

- `solicitante`
- `solicitud`
- `evento`
- `requerimientos`
- `sala`
- `sala_evento`
- `usuarios`

## Requisitos

- Python 3.10 o superior
- PostgreSQL
- pgAdmin4 opcional para inspeccionar la base de datos

## Instalacion

1. Clonar el repositorio:

```bash
git clone <url-del-repositorio>
cd modd-gestion-salas
```

2. Crear y activar entorno virtual:

```bash
python -m venv venv
venv\Scripts\activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Crear base de datos en PostgreSQL:

```sql
CREATE DATABASE modd_db;
```

Si necesitas crear usuario:

```sql
CREATE USER modd_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE modd_db TO modd_user;
```

5. Crear `.env.local` en la raiz:

```env
DATABASE_URL=postgresql://modd_user:tu_password@localhost:5432/modd_db
SECRET_KEY=cambia_esta_llave_por_una_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Puedes usar `.env.example` como referencia.

## Migraciones

Aplicar estructura de base de datos:

```bash
alembic upgrade head
```

## Usuario Administrador

Para crear o forzar el usuario administrador local:

```bash
python forzar_admin.py
```

Credenciales usadas en desarrollo:

- Usuario: `admin@unison.mx`
- Contrasena: `modd2026`

## Datos Demo

Para reiniciar y llenar datos de prueba:

```bash
python scripts/seed_demo.py
```

El script crea salas, solicitantes, solicitudes, requerimientos y eventos consistentes con el modelo relacional.

## Ejecutar

```bash
uvicorn app.main:app --reload
```

Abrir:

```text
http://127.0.0.1:8000
```

## Rutas Principales

- `/` landing
- `/login` inicio de sesion
- `/dashboard` panel principal
- `/calendario` calendario interactivo
- `/solicitudes` gestion de solicitudes
- `/eventos` listado de eventos
- `/reportes` generacion de PDF

Las rutas internas requieren sesion activa.

## APIs Principales

- `POST /api/auth/login`
- `GET /api/auth/logout`
- `GET /api/eventos/`
- `GET /api/eventos/?solo_aprobadas=true`
- `PUT /api/eventos/{id_evento}`
- `DELETE /api/eventos/{id_evento}`
- `GET /api/solicitudes/`
- `POST /api/solicitudes/`
- `PUT /api/solicitudes/{id_solicitud}`
- `PATCH /api/solicitudes/{id_solicitud}/estado`
- `DELETE /api/solicitudes/{id_solicitud}`
- `GET /api/reportes/resumen`
- `GET /api/reportes/pdf`

## Verificacion Rapida en SQL

Eventos con salas:

```sql
SELECT
    e.id_evento,
    e.titulo,
    e.fecha,
    e.hora_de_inicio,
    e.hora_de_termino,
    string_agg('Sala ' || se.numero_sala::text, ', ' ORDER BY se.numero_sala) AS salas
FROM evento e
LEFT JOIN sala_evento se ON se.id_evento = e.id_evento
GROUP BY e.id_evento, e.titulo, e.fecha, e.hora_de_inicio, e.hora_de_termino
ORDER BY e.fecha, e.hora_de_inicio;
```

Solicitudes con solicitante:

```sql
SELECT
    so.id_solicitud,
    so.estado,
    s.nombre,
    s.apellido,
    s.correo
FROM solicitud so
JOIN solicitante s ON s.id_solicitante = so.id_solicitante
ORDER BY so.id_solicitud;
```

## Estructura

```text
modd-gestion-salas/
├── alembic/
│   ├── env.py
│   └── versions/
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/
│   │   ├── salas.py
│   │   └── usuarios.py
│   ├── routers/
│   │   ├── api_auth.py
│   │   ├── api_eventos.py
│   │   ├── api_reportes.py
│   │   ├── api_salas.py
│   │   ├── api_solicitudes.py
│   │   └── views.py
│   ├── schemas/
│   ├── static/
│   └── templates/
├── scripts/
│   ├── check_overlaps.py
│   └── seed_demo.py
├── alembic.ini
├── requirements.txt
└── README.md
```

## Integrantes

- Daniel Eduardo Alvarez Terrazas
- Melina Gonzalez Mendez
- Omar Pacheco Velasquez
- Jesus David Ayala Morales
