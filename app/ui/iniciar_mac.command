#!/bin/bash

# Ir a la carpeta donde está este archivo
cd "$(dirname "$0")"

echo "================================"
echo "   GESTOR DE PROYECTOS"
echo "================================"

# Comprobar que Python esté instalado
if command -v python3.14 >/dev/null 2>&1; then
    PYTHON="python3.14"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    echo "No se encontró Python 3."
    echo "Instala Python y vuelve a intentarlo."
    read -r -p "Presiona Enter para salir..."
    exit 1
fi

# Crear el entorno virtual si no existe
if [ ! -d ".venv" ]; then
    "$PYTHON" -m venv .venv || exit 1
fi

# Activar el entorno virtual
source .venv/bin/activate

# Instalar dependencias si existe requirements.txt
if [ -f "requirements.txt" ]; then
    python -m pip install -r requirements.txt || exit 1
else
    echo "Falta el archivo requirements.txt."
    echo "No se pueden instalar las dependencias automáticamente."
    read -r -p "Presiona Enter para salir..."
    exit 1
fi

echo ""
echo "Iniciando la aplicación..."
echo "Abre http://127.0.0.1:8000 en tu navegador."
echo "Para detenerla, presiona Ctrl+C."
echo ""

python -m app.main
