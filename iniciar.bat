@echo off
setlocal
cd /d "%~dp0"
title Gestor Proyectos - Inicio

echo ==========================================
echo       INICIAR GESTOR PROYECTOS
echo ==========================================
echo.

if not exist "requirements.txt" (
    echo ERROR: No se encuentra requirements.txt. Ejecuta este archivo desde la raiz del proyecto.
    pause
    exit /b 1
)
if not exist "app\main.py" (
    echo ERROR: No se encuentra app\main.py. Ejecuta este archivo desde la raiz del proyecto.
    pause
    exit /b 1
)

REM Elegir el Python a usar: 3.14, o el Python 3 por defecto del lanzador.
set "PYCMD="
py -3.14 --version >nul 2>&1 && set "PYCMD=py -3.14"
if not defined PYCMD (
    py -3 --version >nul 2>&1 && set "PYCMD=py -3"
)
if not defined PYCMD (
    echo ERROR: No se encuentra Python 3. Instalalo desde python.org y vuelve a ejecutar este archivo.
    pause
    exit /b 1
)

REM Si el entorno virtual existe pero esta roto, se recrea.
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" --version >nul 2>&1
    if errorlevel 1 rmdir /s /q ".venv"
)
if not exist ".venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    %PYCMD% -m venv .venv
    if errorlevel 1 (
        echo ERROR: No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

echo.
echo Instalando/verificando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Fallo la instalacion de dependencias.
    pause
    exit /b 1
)

echo.
echo Iniciando la aplicacion en http://127.0.0.1:8000 ...
start "" "http://127.0.0.1:8000"
".venv\Scripts\python.exe" -m app.main
if errorlevel 1 (
    echo.
    echo La aplicacion termino con un error. Revisa el mensaje anterior.
)

echo.
pause
endlocal
