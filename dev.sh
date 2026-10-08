#!/bin/bash

# dev.sh — Arranca el servidor API local (FastAPI) y el Frontend (Vite) en paralelo.

cd "$(dirname "$0")"

# Activar el entorno virtual si existe
if [ -d "reddit-env" ]; then
    source reddit-env/bin/activate
fi

echo "🚀 Iniciando API Backend local (127.0.0.1:8000)..."
python3 -m uvicorn server.app:app --host 127.0.0.1 --port 8000 --reload &
SERVER_PID=$!

echo "🖥️  Iniciando Frontend Web (Vite http://localhost:5173)..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

cleanup() {
    echo ""
    echo "🛑 Deteniendo servidores..."
    kill $SERVER_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "✔ Ambos servidores están en ejecución."
echo "👉 Abre tu navegador en: http://localhost:5173"
echo "Presiona Ctrl+C para detener."

wait
