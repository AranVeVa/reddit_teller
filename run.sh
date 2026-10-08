#!/bin/bash

# run.sh — Automatización para generar videos de reddit_teller sin interactividad.
# Uso:
#   ./run.sh <subreddit> [opciones_adicionales]
# Ejemplo:
#   ./run.sh shortscarystories
#   ./run.sh horrorstories -l 2

# Ir al directorio del script
cd "$(dirname "$0")"

# Activar el entorno virtual si existe
if [ -d "reddit-env" ]; then
    source reddit-env/bin/activate
fi

# Subreddit por defecto si no se especifica
SUBREDDIT=${1:-"horrorstories"}
shift 2>/dev/null || true # Eliminar el primer parámetro (subreddit) si existe

echo "🚀 Iniciando generación automática para r/$SUBREDDIT..."

# Ejecutar el pipeline con valores por defecto automatizados (-y)
python scripts/main.py \
    --subreddit "$SUBREDDIT" \
    --limit 1 \
    --duration 1 \
    --order hot \
    --scenes \
    --subs \
    --words-per-card 3 \
    --dark-mode \
    --yes \
    "$@"
