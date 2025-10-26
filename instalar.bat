@echo off
cls
echo.
echo --- INSTALADOR AUTOMATICO DE BIBLIOTECA APP ---
echo.

:menu
echo.
echo Seleccione la base de datos para la instalacion:
echo.
echo   1. SQLite (Portatil, no necesita XAMPP)
echo   2. MySQL  (Requiere XAMPP)
echo.

set /p choice="Escriba 1 o 2 y presione Enter: "

if "%choice%"=="1" (
    set SETTINGS_FILE=BibliotecaProject.settings_sqlite
    set REQS_FILE=requirements_sqlite.txt
    goto install
)
if "%choice%"=="2" (
    set SETTINGS_FILE=BibliotecaProject.settings_mysql
    set REQS_FILE=requirements_mysql.txt
    goto install
)
echo.
echo Opcion no valida. Intentelo de nuevo.
pause
goto menu


:install
echo.
echo [1/4] Creando entorno virtual...
python -m venv venv
call venv\Scripts\activate

echo.
echo [2/4] Instalando requerimientos desde %REQS_FILE%...
pip install -r %REQS_FILE%

echo.
echo [3/4] Migrando la base de datos (%SETTINGS_FILE%)...
py manage.py migrate --settings=%SETTINGS_FILE%

echo.
echo [4/4] Poblando la base de datos con datos de ejemplo...
py manage.py seed_data --settings=%SETTINGS_FILE%

echo.
echo ---------------------------------------------------
echo      ¡Instalacion completada exitosamente!
echo ---------------------------------------------------
pause