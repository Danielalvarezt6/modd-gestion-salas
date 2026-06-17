# Cambios realizados por David en el Proyecto
Se hizo una nueva estructura del proyecto, creando carpetas como *app/routers*, *app/templates*, *app/static,* etc.

Se elimino *app.py* para hacer que *main.py* sea el coordinador, configurando el punto de entrada que levanta Uvicorn.

Las vistas (*views.py*) se crearon para aislar el código que sirve el HTML de la landing page, el login y el dashboard.

Los routers de la API (*api_auth.py* y *api_salas.py*) fueron creados para hacer los endpoints que devuelven JSON. ACTUALMENTE ESTOS ARCHIVOS TIENEN DATOS "SIMULADOS".

El cliente *login.html* fue modificado, el javascript fue modificado para que haga peticiones asincronas reales (*fetch*) al backend.

---
A implementar:
1. Archivo **.env** para definir *DATABASE_URL* y *SECRET_KEY*
    Archivo **app/core/config.py** para cargar las variables del .env a la aplicación de forma tipada.
2. Archivo **app/core/database.py**. Crear el *engine* de SQLAlchemy conectado a psycopg2, inicializar *SessionLocal* y crear la función *get_db()* para la inyección de dependencias.
    Archivo **app/models/usuarios.py**. Falta crear el modelo SQLAlchemy para la tabla de administradores/usuarios (ID, correo, contraseña hasheada).
    Archivo **app/models/salas.py**. Falta crear el modelo para el diagrama de la base de datos.
3. Archivo **app/core/security.py**. Implementar las funciones de *passlib* (para encryptar las contraseñas con bcrypt) y *python-jose* (para generar y decodificar los tokens JWT).
    Archivo **app/routers/api_auth.py**. Falta reemplazar el login temporal, el nuevo flujo debe consultar la base de datos, comparar el hash de la contraseña y, si es correcta, usar *security.py* para generar el JWT y enviarlo en la cookie.

4. Archivo **app/schemas/usuarios.py**. Faltan las clases para validar la creación de usuarios y la estructura del Token.
    Archivo **app/schemas/salas.py**. Faltan las clases para validar la entrada de datos.

5. Archivo **app/crud/usuarios.py**. Faltan las funciones como *get_user_by_email(db, email)* para buscar al administrador que intenta iniciar sesión.
    Archivo **app/crud/salas.py**. Faltan las funciones vitales para el sistema, especialmente *verificar_disponibilidad(db, sala_id, hora_inicio, hora_fin)* para asegurar que el sistema rechace empalmes, y *crear_evento(db, evento)*.
    
6. Conectar los endpoints.
    En **app/routers/api_salas.py** borrar los diccionarios de prueba  usar las funciones de la carpeta *crud* para devolver la información real desde la base de datos a quien esté desarrollando el frontend.

7. Migraciones de Base de Datos (Alembic)
Dado que este es un proyecto robusto en Postgres, no es recomendable crear las tablas "a mano". Es buena practica usar *alembic*.
    Acción en terminal: Ejecutar *alembic init alembic* en la raíz del proyecto.
    Falta configurar el archivo *alembic.ini* para que apunte a tu PostgreSQL y generar la primera migración que construirá automáticamente todas las tablas de los archivos en *app/models/*.
