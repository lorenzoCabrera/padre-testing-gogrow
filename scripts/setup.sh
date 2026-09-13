#!/usr/bin/env bash
# Clones pis-gogrow into this repo if it isn't there yet. Idempotent.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="$ROOT/pis-gogrow"
PROJECT_URL="https://github.com/PIS-GoGrow/pis-gogrow.git"

if [ -d "$PROJECT_DIR/.git" ]; then
  echo "pis-gogrow ya está clonado en $PROJECT_DIR — nada que hacer."
  exit 0
fi

echo "Clonando $PROJECT_URL en $PROJECT_DIR..."
git clone "$PROJECT_URL" "$PROJECT_DIR"
echo "Listo. Para levantar el proyecto: cd pis-gogrow && bin/setup"
