@echo off
echo ===================================================
echo   MODD - Sistema de Gestion de Salas Interactivas
echo ===================================================
echo.

rem Verificar si python esta instalado
python --version >nul 2>&1
if errorlevel 1 goto python_error

rem Copiar .env si no existe
if not exist .env copy .env.example .env >nul

rem Crear venv si no existe
if exist venv goto activate_venv
echo [INFO] Creando entorno virtual (venv)...
python -m venv venv
if errorlevel 1 goto venv_error

:activate_venv
rem Activar entorno virtual
echo [INFO] Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 goto activation_error

rem Instalar dependencias
echo [INFO] Instalando dependencias desde requirements.txt...
pip install -r requirements.txt
if errorlevel 1 goto pip_error

rem Iniciar uvicorn
echo.
echo ===================================================
echo   Iniciando el servidor de desarrollo...
echo   El servidor estara disponible en: http://localhost:8000
echo   Para detener el servidor, presiona Ctrl+C.
echo ===================================================
echo.
uvicorn app.main:app --reload
goto end

:python_error
echo [ERROR] Python no esta instalado o no se encuentra en el PATH.
echo Por favor, instala Python 3.10 o superior y asegurate de marcar
echo la casilla "Add Python to PATH" durante la instalacion.
pause
exit /b 1

:venv_error
echo [ERROR] No se pudo crear el entorno virtual.
pause
exit /b 1

:activation_error
echo [ERROR] No se pudo activar el entorno virtual.
pause
exit /b 1

:pip_error
echo [ERROR] Error al instalar dependencias.
pause
exit /b 1

:end
pause
