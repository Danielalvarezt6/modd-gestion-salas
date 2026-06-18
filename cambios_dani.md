# Cambios realizados - Dani

## Resumen general

Se avanzo en la construccion del frontend administrativo de MODD, manteniendo el proyecto con Jinja2, Tailwind CSS, JavaScript Vanilla y FullCalendar, sin generar endpoints nuevos de datos ni logica backend adicional.

## Calendario

- Se creo una pagina independiente para el calendario en `/calendario`.
- Se implemento un calendario semanal interactivo con columnas por dia y subcolumnas por sala.
- Se agregaron filtros por sala, busqueda, leyenda de salas/estados y modal de evento.
- Los eventos pueden moverse entre dias, horas y salas.
- Los eventos pueden extenderse horizontalmente para ocupar mas de una sala.
- Se agrego extension vertical para aumentar o reducir la duracion del evento.
- Los movimientos y extensiones ahora se ajustan solo a bloques de una hora.
- Se evita guardar cambios cuando existe solapamiento con otro evento en la misma sala, dia y horario.
- El modal de evento limita los horarios a pasos de una hora.

## Paginas administrativas

Se agregaron nuevas secciones visuales:

- `/solicitudes`
- `/eventos`
- `/reportes`

Cada pagina incluye diseno responsive, barra superior, busqueda, navegacion lateral, estados visuales y datos mock para representar el flujo futuro del sistema.

## Solicitudes

- Se implemento una vista para revisar solicitudes de sala.
- Incluye tarjetas de resumen por estado.
- Incluye busqueda por solicitante, evento o institucion.
- Incluye filtro por estado.
- Incluye tabla con solicitante, institucion, evento, sala, fecha/hora y estado.
- Se agregaron acciones visuales como aprobar, editar y ver detalle.

## Eventos

- Se implemento una vista de eventos confirmados.
- Incluye metricas de total de eventos, confirmados, mantenimiento y eventos de la semana.
- Incluye filtros por sala y tipo de evento.
- Incluye tabla de eventos con responsable, sala, dia, horario, asistentes, tipo, estado y acciones.
- Se agregaron indicadores visuales por sala y estado.

## Reportes

- Se implemento una vista para generar reportes PDF.
- Incluye tarjetas para reporte semanal, mensual, por sala y personalizado.
- Incluye filtros por fecha inicial, fecha final y sala.
- Las acciones de exportacion son visuales y quedan listas para integracion futura.

## Navegacion y layout

- Se conecto el sidebar con las rutas reales:
  - Dashboard
  - Calendario
  - Solicitudes
  - Eventos
  - Reportes
- Se agrego un boton global de modo claro/oscuro en `base.html`, visible en toda la aplicacion.

## Estilos

- Se agregaron estilos compartidos para paginas administrativas en `custom.css`.
- Se mantuvo compatibilidad con modo claro y oscuro.
- Se cuidaron estados visuales, tablas responsivas, tarjetas, filtros, botones e indicadores.
- Se priorizo una interfaz limpia, moderna, institucional y facil de usar.

## Dependencias

- Se limpio `requirements.txt`.
- El archivo anterior tenia dependencias de sistema y paquetes incompatibles.
- Se dejo solo lo necesario para el proyecto MODD:
  - FastAPI
  - Uvicorn
  - Jinja2
  - SQLAlchemy
  - Psycopg2
  - Alembic
  - Python dotenv
  - Pydantic
  - Pydantic settings
  - Python jose
  - Passlib
  - Python multipart
  - HTTPX

## Verificaciones

- Se verifico que las rutas principales respondan correctamente con `TestClient`.
- Se verifico que el JavaScript del calendario no tenga errores de sintaxis con `node --check`.
- Se verifico que `pip install -r requirements.txt` funcione con el archivo limpio.

