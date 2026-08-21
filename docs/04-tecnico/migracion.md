## Migración Técnica Paso a Paso

Cómo convertir el repo viejo (38 MB, datos duplicados) al nuevo (12 MB, maestro GPKG, derivados automáticos).

---

### Pre-Requisitos

```bash
# Herramientas requeridas
gdal-bin    # ogrinfo, ogr2ogr, gdalinfo
sqlite3     # inspeccionador GPKG
git         # >= 2.25 (shallow clone support)
python3     # >= 3.9
jq          # (opcional, para validación JSON)
```

### Instalación (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install gdal-bin sqlite3 python3-pip
python3 -m pip install --upgrade pip
```

---

### Paso 1: Inspeccionar GPKG Maestro Actual

Antes de hacer cambios, entiende qué hay adentro.

```bash
# Ver todas las capas en GPKG
ogrinfo -so ../docs/layers_general_gpkg/todos_layers.gpkg

# Salida esperada:
# Layer 0: capas_censo (wkbPolygon)
# Layer 1: calles (wkbLineString)
# ...

# Contar registros por capa
for layer in $(ogrinfo -so datos.gpkg | grep "^Layer" | cut -d' ' -f2 | cut -d'(' -f1); do
  echo "$layer: $(ogrinfo datos.gpkg $layer | grep "^Feature Count" | awk '{print $3}')"
done

# Validar CRS
gdalinfo datos.gpkg | grep "PROJCS\|GEOGCS"
# Esperado: EPSG:5344 (POSGAR 2007 / Faja 2)
```

**Documentar salida en issue**, ejemplo:

```
Validación pre-migración:
- capas_censo: 450 registros, EPSG:5344 ✅
- calles: 3200 registros, EPSG:5344 ✅
- transporte: 185 registros, EPSG:4326 ⚠️ (expect 5344)
```

---

### Paso 2: Migrar Datasets Duplicados (Transporte, Barrios)

### 2a. Transporte (líneas desde GeoJSON)

```bash
# Convertir GeoJSON → GPKG (agregar a capa existente o nueva)
ogr2ogr -append -f GPKG \
  datos.gpkg \
  layers_transporte/transporte_lineas.geojson \
  -nln transporte_lineas \
  -t_srs EPSG:5344 \
  -lco GEOMETRY_NAME=geometry

# Validar
ogrinfo -so datos.gpkg transporte_lineas | head -5
```

### 2b. Transporte (paradas desde GeoJSON)

```bash
ogr2ogr -append -f GPKG \
  datos.gpkg \
  layers_transporte/transporte_paradas.geojson \
  -nln transporte_paradas \
  -t_srs EPSG:5344

# Validar
ogrinfo datos.gpkg transporte_paradas
```

### 2c. Barrios (desde JavaScript)

Primero, convertir `.js` a GeoJSON:

```javascript
// script: layers_js/barrios_data.js → barrios.geojson
// Editar manualmente o usar:
const fs = require('fs');
const script = fs.readFileSync('barrios_data.js', 'utf-8');
eval(script); // ejecuta var bios_data = {...}
fs.writeFileSync('barrios.geojson', JSON.stringify({
  type: "FeatureCollection",
  features: barrios_data.features
}));
```

Luego migrar a GPKG:

```bash
ogr2ogr -append -f GPKG \
  datos.gpkg \
  barrios.geojson \
  -nln barrios \
  -t_srs EPSG:5344

ogrinfo datos.gpkg barrios | head
```

### 2d. Repetir para `barrios_nivel_instruccion_data.js` y `barrios_sexo_data.js`

```bash
# Después de convertir a GeoJSON:
ogr2ogr -append -f GPKG datos.gpkg barrios_instruccion.geojson -nln barrios_instruccion -t_srs EPSG:5344
ogr2ogr -append -f GPKG datos.gpkg barrios_sexo.geojson -nln barrios_sexo -t_srs EPSG:5344
```

---

### Paso 3: Validar GPKG Consolidado

```bash
# Listar todas las capas
ogrinfo -so datos.gpkg

# Validar integridad (sin errores de topología)
ogrinfo datos.gpkg | grep -c "^Feature Count" # debe ser 23 (cantidad de capas)

# Validar proyección en todas las capas
for layer in $(ogrinfo -so datos.gpkg | grep "^Layer" | cut -d' ' -f2 | cut -d'(' -f1); do
  crs=$(gdalinfo datos.gpkg -layers $layer 2>/dev/null | grep EPSG | head -1)
  echo "$layer: $crs"
done
# Todas deben tener EPSG:5344
```

Si hay errores, documentarlos en issue antes de continuar.

---

### Paso 4: Configurar `.gitignore` para Derivados

Crear archivo `.gitignore` en raíz del repo:

```
# Derivados (generados por CI, no commitear)
*.geojson
*_data.js
layers_*.tar.gz
dist/

# Build artifacts
__pycache__/
*.pyc
*.pyo
*~

# Editor
.DS_Store
.vscode/*
!.vscode/settings.json
.idea/

# CI logs
logs/
*.log

# Temporal
tmp/
temp/
```

Commit este archivo:

```bash
git add .gitignore
git commit -m "chore: add .gitignore para derivados"
```

---

### Paso 5: Script de Generación GPKG → GeoJSON (CI Local)

Crear `scripts/gpkg_to_geojson.py`:

```python
#!/usr/bin/env python3
"""Generar GeoJSON desde GPKG para cada capa"""

import subprocess
import json
import os

GPKG_PATH = "datos.gpkg"
OUTPUT_DIR = "dist"

def get_layers(gpkg):
    """Listar capas en GPKG"""
    result = subprocess.run(['ogrinfo', '-so', gpkg], capture_output=True, text=True)
    layers = []
    for line in result.stdout.split('\n'):
        if line.startswith('Layer'):
            layer = line.split(': ')[1].split('(')[0].strip()
            layers.append(layer)
    return layers

def gpkg_to_geojson(gpkg, layer, output):
    """Convertir capa GPKG → GeoJSON"""
    subprocess.run([
        'ogr2ogr', '-f', 'GeoJSON',
        output, gpkg,
        '-sql', f"SELECT * FROM {layer}"
    ], check=True)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    layers = get_layers(GPKG_PATH)
    print(f"Generando {len(layers)} capas...")
    
    for layer in layers:
        output = f"{OUTPUT_DIR}/{layer}.geojson"
        print(f"  {layer}...", end=' ')
        gpkg_to_geojson(GPKG_PATH, layer, output)
        
        # Validar
        with open(output) as f:
            data = json.load(f)
        print(f"✓ ({len(data['features'])} features)")

if __name__ == '__main__':
    main()
```

Usar:

```bash
python3 scripts/gpkg_to_geojson.py
# Salida: ✓ (450 features), ✓ (3200 features), etc.
```

---

### Paso 6: Script de Generación JavaScript (opcional, Fase 2)

Si aún se necesita el visor JavaScript, crear `scripts/gpkg_to_js.py`:

```python
#!/usr/bin/env python3
"""Generar archivos JavaScript desde GPKG (para visor histórico)"""

import subprocess
import json
import os

GPKG_PATH = "datos.gpkg"
OUTPUT_DIR = "dist/layers_js"

def gpkg_to_geojson(gpkg, layer):
    """Convertir capa → GeoJSON temp"""
    result = subprocess.run([
        'ogr2ogr', '-f', 'GeoJSON', '/dev/stdout', gpkg,
        '-sql', f"SELECT * FROM {layer}"
    ], capture_output=True, text=True)
    return json.loads(result.stdout)

def geojson_to_js(layer, geojson):
    """Convertir GeoJSON → var JS"""
    output = f"{OUTPUT_DIR}/{layer}_data.js"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(output, 'w') as f:
        f.write(f"var {layer}_data = {json.dumps(geojson)};\n")

# Ejecutar para cada capa que necesite JS
layers = ['barrios', 'barrios_instruccion', 'barrios_sexo']
for layer in layers:
    geojson = gpkg_to_geojson(GPKG_PATH, layer)
    geojson_to_js(layer, geojson)
    print(f"✓ {layer}_data.js")
```

---

### Paso 7: Commit de Cambios

```bash
# Agregar GPKG maestro consolidado
git add datos.gpkg

# Commit
git commit -m "feat: consolidar 23 datasets en GPKG maestro

Resuelve deuda técnica:
- Transporte (líneas, paradas): GeoJSON → GPKG
- Barrios (3 datasets): JS → GPKG

Validación:
- Todas las capas: EPSG:5344 ✓
- 23 capas, ~8 MB de datos ✓
- Sin duplicación ✓

Aplica ADR-001 y ADR-002
"
```

---

### Paso 8: Verificación Final

```bash
# Tamaño del repo
du -sh .
# Esperado: < 20 MB total (antes: 38 MB)

# Validar que derivados NO están commitedos
git ls-files | grep ".geojson\|_data.js" | wc -l
# Esperado: 0

# Validar GPKG maestro
git ls-files | grep ".gpkg"
# Esperado: datos.gpkg (solo uno)

# Contar commits nuevos
git log --oneline --grep="feat:\|fix:" | head -10
```

---

### Troubleshooting

### Error: "cannot open source dataset"

```bash
# Causa: ruta incorrecta o archivo no existe
ls -la layers_transporte/transporte_lineas.geojson
# Si no existe, buscar:
find . -name "*transporte*" -type f
```

### Error: "SQL error"

```bash
# Causa: nombre de capa tiene caracteres especiales
# Solución: citar nombre: -sql "SELECT * FROM \"mi-capa\""
```

### GPKG crece > 50 MB

```bash
# Causa: geometría inválida o datos duplicados
ogrinfo -so datos.gpkg | grep "Feature Count"
# Si hay > 500K features, revisar si hay duplicadas
```

---

### Próximo Paso

Una vez completado este paso, ir a **Fase 1: Setup CI/CD** para automatizar esta generación.
