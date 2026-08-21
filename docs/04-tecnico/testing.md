## Estrategia de Testing

Qué validar en cada cambio para garantizar integridad de datos.

---

### Test Pre-Commit (Local, Desarrollador)

Antes de hacer `git push`, correr estos tests:

### T1: Validación de GPKG

```bash
#!/bin/bash
# scripts/test_gpkg_integrity.sh

GPKG="datos.gpkg"

# T1.1: GPKG existe y no está vacío
test -f "$GPKG" || exit 1
test -s "$GPKG" || exit 1

# T1.2: GPKG se puede abrir con GDAL
ogrinfo -so "$GPKG" > /dev/null || exit 1

# T1.3: Todas las capas tienen CRS EPSG:5344
for layer in $(ogrinfo -so "$GPKG" | grep "^Layer" | cut -d' ' -f2 | cut -d'(' -f1); do
  crs=$(gdalinfo "$GPKG" -oo LAYER="$layer" 2>/dev/null | grep -i "EPSG" | head -1)
  if [[ ! "$crs" =~ "5344" ]]; then
    echo "ERROR: $layer no tiene EPSG:5344"
    exit 1
  fi
done

# T1.4: Cantidad de registros conocida
# (Documento valores esperados en CHANGELOG)
EXPECTED_TOTAL=8200  # Ejemplo
ACTUAL=$(ogrinfo "$GPKG" | grep "^Feature Count" | awk '{s+=$3} END {print s}')
if [ "$ACTUAL" -lt "$EXPECTED_TOTAL" ]; then
  echo "WARNING: Total de features ($ACTUAL) menor a esperado ($EXPECTED_TOTAL)"
  exit 1
fi

echo "✓ GPKG integrity OK"
```

Usar:

```bash
bash scripts/test_gpkg_integrity.sh
```

### T2: Validación de Geometría

```bash
#!/bin/bash
# scripts/test_geometries.sh

GPKG="datos.gpkg"

echo "Validando geometrías..."

# T2.1: Sin geometría self-intersecting
ogrinfo "$GPKG" -sql "
  SELECT ST_IsValid(geometry) as valid, COUNT(*) as count 
  FROM capas_censo 
  WHERE NOT ST_IsValid(geometry)
" 

# Si retorna count > 0, hay geometrías inválidas

# T2.2: Sin geometría vacía
ogrinfo "$GPKG" -sql "
  SELECT COUNT(*) as empty_geoms 
  FROM capas_censo 
  WHERE geometry IS NULL
"

# T2.3: Validar envelope (bbox)
ogrinfo "$GPKG" -sql "
  SELECT 
    ST_MinX(geometry) as minx,
    ST_MaxX(geometry) as maxx,
    ST_MinY(geometry) as miny,
    ST_MaxY(geometry) as maxy
  FROM capas_censo
  LIMIT 1
"
# Esperado: Comodoro Rivadavia ≈ -68.4 a -68.3, -45.9 a -45.8

echo "✓ Geometries OK"
```

### T3: Sin Cambios Inesperados

```bash
#!/bin/bash
# scripts/test_no_unexpected_changes.sh

# T3.1: Validar que solo GPKG cambió (no derivados)
git diff --cached --name-only | grep -E "\.geojson|_data\.js" && {
  echo "ERROR: Derivados detectados en staging. Remover con 'git restore --staged'"
  exit 1
}

# T3.2: GPKG size no creció > 50%
OLD_SIZE=$(git show HEAD:datos.gpkg | wc -c)
NEW_SIZE=$(wc -c < datos.gpkg)
GROWTH=$((NEW_SIZE * 100 / OLD_SIZE))
if [ "$GROWTH" -gt 150 ]; then
  echo "WARNING: GPKG creció ${GROWTH}%. Revisar si hay duplicados."
fi

echo "✓ Changes OK"
```

---

### Test en CI (GitHub Actions)

Ejecutado automáticamente en cada PR.

### Workflow: `.github/workflows/test.yml`

```yaml
name: Validate GPKG & Metadata

on:
  pull_request:
    paths:
      - 'datos.gpkg'
      - 'scripts/**'
      - '.github/workflows/test.yml'

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install GDAL
        run: |
          sudo apt update
          sudo apt install -y gdal-bin
      
      # T1: GPKG Integrity
      - name: Test GPKG Integrity
        run: bash scripts/test_gpkg_integrity.sh
      
      # T2: Geometrías Válidas
      - name: Test Geometries
        run: bash scripts/test_geometries.sh
      
      # T3: No Derivados
      - name: Test No Unexpected Changes
        run: bash scripts/test_no_unexpected_changes.sh
      
      # T4: Metadatos (Fase 1+)
      - name: Test ISO 19115 Metadata
        if: hashFiles('metadatos.csv') != ''
        run: python3 scripts/validate_iso19115.py metadatos.csv
      
      # T5: Build Derivados (Fase 1+)
      - name: Build Derivates (GeoJSON, JS)
        run: python3 scripts/gpkg_to_geojson.py
      
      # T6: Validar GeoJSON generado
      - name: Validate Generated GeoJSON
        run: |
          for f in dist/*.geojson; do
            jq empty "$f" || exit 1
          done
      
      # T7: Tamaño del repo
      - name: Check Repo Size
        run: |
          SIZE=$(du -sb . | cut -f1)
          LIMIT=$((20 * 1024 * 1024))  # 20 MB
          if [ $SIZE -gt $LIMIT ]; then
            echo "ERROR: Repo size ($((SIZE / 1024 / 1024)) MB) > limit (20 MB)"
            exit 1
          fi
```

### Test de Regresión Mensual

Cada primer viernes del mes, ejecutar test más exhaustivo:

```yaml
name: Monthly Regression Test

on:
  schedule:
    - cron: '0 9 1 * *'  # Primer día del mes, 09:00 UTC (06:00 ART)

jobs:
  regression:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install tools
        run: sudo apt install -y gdal-bin sqlite3
      
      - name: Full GPKG Analysis
        run: |
          echo "=== Capas ==="
          ogrinfo -so datos.gpkg
          
          echo "=== Estadísticas ==="
          ogrinfo datos.gpkg | grep "Feature Count"
          
          echo "=== CRS ==="
          gdalinfo datos.gpkg | grep EPSG
      
      - name: Compare with Previous Month
        run: |
          # Descargar GPKG del último commit de hace 30 días
          git show $(git rev-list --max-count=1 --before='30 days ago' HEAD):datos.gpkg > datos_prev.gpkg
          
          # Comparar features count
          PREV_COUNT=$(ogrinfo datos_prev.gpkg | grep "Feature Count" | awk '{s+=$3} END {print s}')
          CURR_COUNT=$(ogrinfo datos.gpkg | grep "Feature Count" | awk '{s+=$3} END {print s}')
          
          echo "Features: $PREV_COUNT (prev) → $CURR_COUNT (current)"
          
          if [ $CURR_COUNT -lt $PREV_COUNT ]; then
            echo "WARNING: Cantidad de features decreció (¿borrado intencional?)"
          fi
      
      - name: Generate Test Report
        run: |
          # Crear reporte y subirlo a artefacto
          {
            echo "# Test Report - $(date)"
            echo ""
            echo "## GPKG Status"
            ogrinfo -so datos.gpkg
            echo ""
            echo "## Feature Counts"
            ogrinfo datos.gpkg | grep "Feature Count"
          } > test_report.txt
      
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: monthly-test-report
          path: test_report.txt
```

---

### Test Manual (Revisor)

Antes de mergear PR, revisor ejecuta:

```bash
# Checkout PR branch
git fetch origin pull/123/head:pr-123
git checkout pr-123

# Abrir GPKG en QGIS
qgis datos.gpkg

# Validaciones visuales:
# - [ ] Todas las capas renderean sin error
# - [ ] Límite de Comodoro Rivadavia está visible
# - [ ] Estilos son correctos (colores, simbología)
# - [ ] Atributos tienen datos coherentes

# Validaciones programáticas:
bash scripts/test_gpkg_integrity.sh
bash scripts/test_geometries.sh

# Si todo OK:
git checkout main
git merge pr-123
```

---

### Métricas de Calidad

Documentar en `CHANGELOG.md` después de cada cambio:

```markdown
### [2027-02-15] - Actualización dataset X

Cambios:
- Dataset X: +50 registros, -10 registros (total: 500 → 540)
- Geometría: 100% válida, sin self-intersecting
- Tamaño GPKG: 8.2 MB → 8.4 MB (+2.4%)
- CI: ✅ All tests passed (6/6)
- Review: ✅ 2 aprobaciones

Versión: v1.2.3
Timestamp: 2027-02-15T10:30:00Z
Responsable: @usuario
```

---

### Checklist de Tests Antes de Mergear

- [ ] ✅ Tests locales pasan (`test_gpkg_integrity.sh`, `test_geometries.sh`)
- [ ] ✅ CI pasa (GitHub Actions todas las checks verdes)
- [ ] ✅ No hay derivados en staging (`.geojson`, `_data.js`)
- [ ] ✅ CHANGELOG actualizado con cambios
- [ ] ✅ Review manual en QGIS (si cambio es significativo)
- [ ] ✅ Commit message describe cambio y APR/ADR relacionado
- [ ] ✅ Número de features conocido y documentado

Sin esto, no mergear.

---

### Escalada de Fallos

| Test | Falla | Acción |
|------|-------|--------|
| `test_gpkg_integrity.sh` | GPKG corrupto | Rollback inmediato, abrir issue P1 |
| `test_geometries.sh` | Geometría inválida | Corregir antes de mergear, abrir issue |
| `test_no_unexpected_changes.sh` | Derivado commitedo | Remover con `git restore --staged` |
| `validate_iso19115.py` | Metadatos invalidos | Corregir en Sheets/CSV, regenerar |
| `test_size.yml` | Repo > 20 MB | Investigar bloat, aplicar regla derivado |
| CI timeout | > 5 min | Optimizar scripts, revisar performance |

---

### Test Performance

Tiempo esperado por test:

```
test_gpkg_integrity.sh      ~2 sec
test_geometries.sh          ~5 sec
test_no_unexpected_changes  <1 sec
CI build                    ~30 sec total
Monthly regression test     ~2 min
```

Si alguno tarda más, perfilar y optimizar.
