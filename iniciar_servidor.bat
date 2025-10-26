@echo off
REM Activa el entorno virtual de Python.
call venv\Scripts\activate

:menu
cls
echo.
echo --- CONFIGURACION DE LA BASE DE DATOS ---
echo.
echo Por favor, selecciona la base de datos a utilizar:
echo.
echo   1. SQLite (Version portatil, no necesita XAMPP)
echo   2. MySQL  (Requiere XAMPP)
echo.
set /p choice="Escribe 1 o 2 y presiona Enter: "

if "%choice%"=="1" ( set SETTINGS_FILE=BibliotecaProject.settings_sqlite & goto runserver )
if "%choice%"=="2" ( set SETTINGS_FILE=BibliotecaProject.settings_mysql & goto runserver )

echo Opcion no valida. Por favor, intentalo de nuevo.
pause
goto menu


:runserver
cls
echo.
echo --- INICIAR SERVIDOR DE BIBLIOTECA APP ---
echo      (Usando configuracion: %SETTINGS_FILE%)
echo.

REM --- MODO 1: ACCESO LOCAL (POR DEFECTO) ---
REM El servidor solo sera accesible desde este mismo computador en http://127.0.0.1:8000
echo Iniciando servidor para acceso local...
py manage.py runserver 127.0.0.1:8000 --settings=%SETTINGS_FILE%


REM --- MODO 2: ACCESO DESDE RED LOCAL (OPCIONAL) ---
REM Para acceder desde otros dispositivos (ej. un telefono) en la misma red Wi-Fi:
REM 1. Comenta la linea de arriba (pon REM al inicio).
REM 2. Descomenta la ultima linea de abajo (quita el REM).
REM 3. Averigua tu IP local ejecutando "ipconfig" en la terminal y reemplaza "TU_IP_AQUI".
REM 4. Asegurate de haber anadido tu IP en el archivo de settings correspondiente (%SETTINGS_FILE%.py).

REM py manage.py runserver TU_IP_AQUI:8000 --settings=%SETTINGS_FILE%