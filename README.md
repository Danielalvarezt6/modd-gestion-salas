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
├── app.py             # Servidor FastAPI
├── requirements.txt   # Dependencias de Python
├── static/            # Archivos estáticos
│   ├── css/
│   │   └── custom.css # Estilos personalizados y variables de temas
│   └── js/
│   │   └── landing.js # Interactividad y lógica de cliente
├── templates/          # Vistas (Jinja2 Templates)
│   ├── base.html      # Estructura HTML base y barra de navegación
│   ├── landing.html   # Página de inicio / presentación
│   └── login.html     # Formulario de acceso al sistema
└── guidelines/        # Documentación de diseño y desarrollo
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
   python app.py
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
