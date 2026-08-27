#!/usr/bin/env bash
# Construye el sitio estático fuera de GitHub Actions (Cloudflare Pages).
# Replica los pasos de .github/workflows/publicar.yml, con dos diferencias:
#   - no instala GDAL (no hay sudo en el contenedor de build de CF);
#     generar_derivados.py cae a su motor en Python puro.
#   - recupera la historia de git, porque CF clona shallow.
# Salida: carpeta sitio/ en la raíz del repo.

set -euo pipefail

cd "$(dirname "$0")/../.."

# comun.fecha_git() lee `git log`. Con un clon shallow todas las fechas
# saldrían iguales al último commit. Si ya está completo, git falla y sigue.
git fetch --unshallow || true

PY="$(command -v python3 || command -v python)"
echo "Python: $PY ($("$PY" --version 2>&1))"
echo "Shallow: $(git rev-parse --is-shallow-repository)"

: "${IDE_URL_BASE:?Falta IDE_URL_BASE (URL pública final del sitio)}"
export IDE_URL_BASE

"$PY" ide-datos/scripts/validar_catalogo.py
"$PY" ide-datos/scripts/derivar_catalogo.py
"$PY" ide-datos/scripts/generar_derivados.py
"$PY" ide-datos/scripts/creador_metadata.py
"$PY" ide-datos/scripts/armar_sitio.py

echo "Listo. Contenido de sitio/:"
ls -la sitio
