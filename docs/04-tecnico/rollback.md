## Plan de Rollback

Cómo revertir cambios si algo sale mal.

---

### Escenarios de Rollback

### S1: Cambio en GPKG introduce datos inválidos

**Síntoma**: Tests fallan, geometría corrupta, registros duplicados.

**Rollback (5 min)**:

```bash
# Encontrar commit anterior bueno
git log --oneline datos.gpkg | head -10
# Salida:
# abc1234 feat: agregar transporte
# def5678 chore: actualizar barrios ← BUENO (ultimo antes del error)
# ghi9012 feat: consolidar datasets ← ERROR aquí

# Revertir a commit bueno
git revert ghi9012  # crea un commit que revierte cambios
# O directamente:
git reset --hard def5678

# Validar
bash scripts/test_gpkg_integrity.sh

# Push fuerza (solo si estás seguro, coordiná con equipo)
git push --force origin main  # ⚠️ Comunicar a equipo antes
```

**Confirmación**: CI tests pasan, usuarios accesibles al visor en 10 min.

---

### S2: CI falla pero cambio es correcto

**Síntoma**: Tests locales pasan, pero CI falla en GitHub Actions (flaky test, timeout, etc).

**Rollback** (no necesario):

```bash
# Revisar log de CI
# GitHub Actions → PR → "Checks" → ver qué falló
# Ejemplo: "ogrinfo timeout after 30s"

# Opción 1: Reintentar CI
# En GitHub: botón "Re-run jobs"

# Opción 2: Mergear manualmente si estás seguro
git merge --ff-only origin/pr-branch
git push origin main
# CI se ejecuta nuevamente en main, si falla:
git revert HEAD
```

**No revertir commit si tests locales pasan**. Revisar por qué CI falla.

---

### S3: Metadatos ISO 19115 invalidos (Fase 3+)

**Síntoma**: Validador ISO retorna error, IDERA rechaza.

**Rollback**:

```bash
# Revertir cambios en metadatos
git revert <commit-metadata>

# O editar Sheets directamente
# (en Google Sheets: deshacer cambio manual)

# Regenerar derivados
python3 scripts/gpkg_to_geojson.py
python3 scripts/validate_iso19115.py metadatos.csv
```

**Prevención**: Validar localmente antes de mergear.

```bash
python3 scripts/validate_iso19115.py metadatos.csv
# Si falla: no mergear, corregir en Sheets primero
```

---

### S4: Accidente: Borré GPKG en local

**Síntoma**: `datos.gpkg` no existe en tu máquina.

**Recuperar (1 min)**:

```bash
# Git tiene el archivo
git restore datos.gpkg

# Verificar
ls -la datos.gpkg
ogrinfo -so datos.gpkg
```

**Si lo borraste de Git también**:

```bash
# Último commit que lo tenía
git log --diff-filter=D --summary | grep "delete mode.*gpkg"
# Salida: commit abc1234

# Restaurar
git show abc1234:datos.gpkg > datos.gpkg

# O desde un commit anterior
git checkout HEAD~1 datos.gpkg
```

---

### S5: Mergee PR conflictivo que daña GPKG

**Síntoma**: Merge automático en GitHub falló o pasó pero data es corrupta.

**Rollback (2 min)**:

```bash
# Identificar commit problemático
git log --oneline | head -5

# Revertir
git revert <commit-id>
git push origin main

# Validar
bash scripts/test_gpkg_integrity.sh
```

**Prevención**: Require PR reviews + CI passing antes de permitir merge (branch protection).

---

### S6: VPS en Fase 5 se queda sin espacio

**Síntoma**: PostGIS no acepta escrituras, disk full.

**Rollback a GPKG maestro**:

```bash
# En servidor VPS:
# 1. Pausar replicación GPKG → PG
sudo systemctl stop ide-sync-job

# 2. Limpiar old backups en PG
sudo -u postgres psql -c "DROP DATABASE ide_old_backup;"

# 3. Freear espacio
sudo rm -rf /tmp/ide_logs/*.old

# 4. Reanudar
sudo systemctl start ide-sync-job

# Monitorear
df -h /var/lib/postgresql
# Esperado: > 20% free
```

**Prevención**: Alertas de monitoreo con threshold 80% (actualización en ADR-Phase5).

---

### Rollback por Fase

| Fase | Escenario | Tiempo | Acción |
|------|-----------|--------|--------|
| 0 | Repo institucional creado mal | 10 min | `git remote set-url origin <new-url>` |
| 1 | CI build falla | 5 min | Revertir commit CI, debugguear |
| 2 | GPKG corrupto por migración | 10 min | `git reset --hard <last-good-commit>` |
| 3 | IDERA rechaza metadatos | 1h | Corregir Sheets, regenerar, reenviar |
| 4 | GPG signing causa problemas | 5 min | Disable GPG requirement (no es crítico) |
| 5 | PostGIS disk full | 30 min | Pausar, limpiar, reanudar |

---

### Rollback SLA

Objetivo de tiempo para resolver por nivel de impacto:

| Impacto | Severidad | SLA | Acción |
|---------|-----------|-----|--------|
| Datos corruptos, visor down | CRÍTICA | 15 min | Rollback inmediato + notificación |
| Datos consistentes, CI falla | ALTA | 1h | Debugguear o revertir |
| Metadatos inválidos | MEDIA | 24h | Corregir y reenviar |
| Build timeout o flaky test | BAJA | 2h | Reintentar o ignorar si local OK |

---

### Checklist Post-Rollback

Después de hacer rollback, ejecutar:

- [ ] CI tests pasan (verde en GitHub)
- [ ] GPKG valida con `ogrinfo -so`
- [ ] Visor carga sin errores (abrir en navegador)
- [ ] Cantidad de features es correcta
- [ ] Timestamp y usuario registrado en CHANGELOG
- [ ] Notificar equipo en Slack (si fue rollback crítico)
- [ ] Abrir issue post-mortem (¿por qué pasó? ¿cómo prevenirlo?)

---

## Automatizar Rollback

Para cambios que no pueden fallar, setup webhook para rollback automático:

```bash
# .github/workflows/auto_rollback.yml
name: Auto Rollback on Critical Failure

on:
  workflow_run:
    workflows: ["Validate GPKG"]
    types: [completed]

jobs:
  auto_rollback:
    if: failure()  # Si CI falló
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Revert to Last Good Commit
        run: |
          git log --oneline | head -20 > commits.txt
          # Encontrar último commit que pasó CI
          GOOD_COMMIT=$(git log --grep="✓ CI passed" -1 --pretty=format:"%H")
          git reset --hard $GOOD_COMMIT
          git push --force origin main
      
      - name: Notify Team
        run: |
          echo "🔴 Critical CI failure, rolled back to $GOOD_COMMIT"
          # Enviar a Slack, email, etc.
```

⚠️ **Usar con cuidado**. Mejor que humans revisen y decidan.

---

### Documentación Post-Rollback

Cada rollback debe documentarse en CHANGELOG:

```markdown
### [2027-02-15] - ROLLBACK: Migración transporte

**Descripción**: Revertido commit 7a8b9c0 (deuda técnica)

**Motivo**: 
- GPKG resultante tiene 50% más features de lo esperado (posibles duplicados)
- Tests manuales en QGIS revelan geometrías duplicadas en transporte_lineas

**Acción**:
- Reverted to commit 4d5e6f7 (last good)
- Validación: ✅ CI passed, ✅ QGIS loads, ✅ 23 datasets OK

**Próximos pasos**:
- [ ] Issue abierto: "Investigar duplicados en transporte"
- [ ] Reintentar deuda técnica en 1 semana con inspección más cuidadosa

**Responsable**: @usuario
**Timestamp**: 2027-02-15T14:30:00Z
```

Este registro queda en Git para auditoría futura.
