#!/bin/bash
# Script para exponer Print Quote a internet con Cloudflare Tunnel

set -e

echo "=========================================="
echo "  Print Quote - Cloudflare Tunnel Setup"
echo "=========================================="
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Debes ejecutar este script desde el directorio raíz del proyecto"
    exit 1
fi

# Puerto por defecto
PORT=${PORT:-8000}

echo "📦 Paso 1/3: Build del frontend..."
cd frontend
./node_modules/.bin/vite build
cd ..
echo "✅ Frontend build completado"
echo ""

echo "🚀 Paso 2/3: Iniciando servidor backend..."
.venv/bin/uvicorn quote.api.main:app --host 0.0.0.0 --port $PORT &
SERVER_PID=$!
echo "✅ Servidor iniciado en puerto $PORT (PID: $SERVER_PID)"
echo ""

# Función para limpiar al salir
cleanup() {
    echo ""
    echo "🛑 Deteniendo servidor..."
    kill $SERVER_PID 2>/dev/null || true
    echo "✅ Servidor detenido"
    exit 0
}

# Capturar señales de salida
trap cleanup SIGINT SIGTERM

echo "🌐 Paso 3/3: Iniciando Cloudflare Tunnel..."
echo ""
echo "=========================================="
echo "  Tu aplicación estará disponible en:"
echo "  (espera unos segundos para ver la URL)"
echo "=========================================="
echo ""
echo "Presiona Ctrl+C para detener todo"
echo ""

# Iniciar tunnel (esto bloquea hasta que se presione Ctrl+C)
cloudflared tunnel --url http://localhost:$PORT

# Si el tunnel termina, limpiar
cleanup